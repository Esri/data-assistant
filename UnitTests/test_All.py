import functools
import pathlib
import sys
import traceback
import unittest
import xml.etree.ElementTree as ET
import zipfile

from inc_datasources import _XMLMethodNames, _localWorkspace, _outputDirectory, _daGPTools

sys.path.insert(0, _daGPTools)
import arcpy
import pandas as pd
import tempfile
from scripts import dla
from create import *


def clear_feature_classes(directory: str):
    """
   the dla.gdb is the test workspace the feature classes are created in. To pull the one we want, we clear the workspace
   so that the newly created one is the only one that exists. This function clears the workspace.
    :param directory:
    :return:
    """
    arcpy.env.workspace = directory
    featureclasses = arcpy.ListFeatureClasses()
    if featureclasses is not None:
        for featureclass in featureclasses:
            arcpy.Delete_management(os.path.join(directory, featureclass))


def build_correct_fields(xml_location: str, include_globalid: bool = False):
    """
   takes the xml file and creates the fields that should be in the new feature class
    :param xml_location: str
    :param include_globalid: bool
    :return:
    """
    fields = dla.getXmlElements(xml_location, "Field")
    correct_fields = []
    for field in fields:
        if not include_globalid and str.lower(dla.getNodeValue(field, "TargetName")) != "globalid":
            correct_fields.append(dla.getNodeValue(field, "TargetName"))
    return correct_fields


def make_copy(directory: str, lw: dict):
    """
    Copies the target feature class into the dla.gdb for comparison in the tests
    :param directory:  str
    :param lw : dict
    :return:
    """
    arcpy.env.workspace = lw["Target"]
    arcpy.CopyFeatures_management(lw["TargetName"], os.path.join(directory, "copy"))


def xml_compare(x1: ET, x2: ET, reporter=None):
    """
    taken from:
    https://bitbucket.org/ianb/formencode/src/tip/formencode/doctest_xml_compare.py?fileviewer=file-view-default#cl-70
    :param x1:
    :param x2:
    :param reporter:
    :return:
    """
    if x1.tag in ['Source', 'Target'] or x2.tag in ['Source', 'Target']:
        # We skip asserting the data path is correct because our xml file data paths may not match
        return True
    if x1.tag != x2.tag:
        if reporter:
            reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            if reporter:
                reporter('Attributes do not match: %s=%r, %s=%r'
                         % (name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            if reporter:
                reporter('x2 has an attribute x1 is missing: %s'
                         % name)
            return False
    if not text_compare(x1.text, x2.text):
        if reporter:
            reporter('text: %r != %r' % (x1.text, x2.text))
        return False
    if not text_compare(x1.tail, x2.tail):
        if reporter:
            reporter('tail: %r != %r' % (x1.tail, x2.tail))
        return False
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        if reporter:
            reporter('children length differs, %i != %i'
                     % (len(cl1), len(cl2)))
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not xml_compare(c1, c2, reporter=reporter):
            if reporter:
                reporter('children %i do not match: %s'
                         % (i, c1.tag))
            return False
    return True


def text_compare(t1: str, t2: str):
    """
    taken from:
    https://bitbucket.org/ianb/formencode/src/tip/formencode/doctest_xml_compare.py?fileviewer=file-view-default#cl-70
    :param t1:
    :param t2:
    :return:
    """
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()


class UnitTests(unittest.TestCase):
    """
    Runs the unit tests for the various functions for all test cases and data sources
    """

    def __init__(self, test_object, *args, **kwargs):
        super(UnitTests, self).__init__(*args, **kwargs)

        self.testObject = test_object
        self.local_workspace = self.testObject.local_workspace
        self.localDirectory = _outputDirectory
        self.sourceWorkspace = self.local_workspace["Source"]
        self.targetWorkspace = self.local_workspace["Target"]
        self.sourceFC = self.local_workspace["SourceName"]
        self.targetFC = self.local_workspace["TargetName"]
        self.localFC = list()
        self.localDataPath = ""
        self.localFields = tuple()
        self.sourceDataPath = os.path.join(self.local_workspace["Source"], self.local_workspace["SourceName"])
        self.targetDataPath = os.path.join(self.local_workspace["Target"], self.local_workspace["TargetName"])
        self.sourceFields = tuple(arcpy.ListFields(self.sourceDataPath))
        self.targetFields = tuple(arcpy.ListFields(self.targetDataPath))
        self.methods = _XMLMethodNames
        self.xmlLocation = self.local_workspace["xmlLocation"]
        self.outXML = os.path.join(str(pathlib.Path(self.local_workspace["outXML"]).parent),
                                   pathlib.Path(self.local_workspace["outXML"]).stem,
                                   os.path.basename(self.local_workspace["outXML"]))
        self.correctXML = self.local_workspace["correctXML"]

    def test_create(self):
        """
        Creates the feature class or xml file for testing
        :return:
        """
        clear_feature_classes(_outputDirectory)
        self.testObject.main()
        if self.testObject.title != "CreateConfig":
            self.set_local_info()

    def get_default_values(self):
        """
        Returns a dictionary where the key is the field name and the value is that field's default value
        :return: dict
        """
        out_dict = dict()
        for field in self.targetFields:
            out_dict[field.name] = field.defaultValue
        return out_dict

    def set_local_info(self):
        """
        Once the feature class being tested is created, sets the datapath and fields of that feature class
        :return:
        """
        arcpy.env.workspace = self.localDirectory
        self.localFC = arcpy.ListFeatureClasses()[0]
        arcpy.env.workspace = ""
        self.localDataPath = os.path.join(_outputDirectory, self.localFC)
        self.localFields = tuple(arcpy.ListFields(self.localDataPath))

    @staticmethod
    def build_data_frame(data_path: str, columns: tuple):
        """
        Builds and caches a pandas DataFrame object containing the information from the specified feature class
        :param data_path: str
        :param columns: tupe(str)
        :return: pd.DataFrame object
        """
        # creates a searchCursor for a given feature class and returns an array of that table
        return pd.DataFrame(list(arcpy.da.SearchCursor(data_path, columns)), columns=columns)

    @functools.lru_cache()
    def get_xml_parse(self):
        """
        Returns and caches a SourceTargetParser object containing information in it from the specified
        SourceTarget.xml file
        :return: SourceTargetParser object
        """
        return SourceTargetParser(self.xmlLocation)

    def test_fields(self):
        """
        Compares the xml file with the mutated file to ensure that the fields were correctly transferred over
        and not tampered with
        :return:
        """
        if self.testObject.title not in ["Preview", "Stage", "Append", "Replace"]:
            return
        correct_fields = build_correct_fields(self.xmlLocation, self.testObject.globalIDCheck)
        if self.testObject.title in ["Append", "Replace"]:
            fields = arcpy.ListFields(self.targetDataPath)
        else:
            fields = arcpy.ListFields(self.localDataPath)

        fieldnames = []
        for field in fields:
            if self.testObject.globalIDCheck:
                if field.name.lower() not in ["", "objectid", "shape"]:
                    fieldnames.append(field.name)
            else:
                if field.name.lower() not in ["", "objectid", "shape", "globalid"]:
                    fieldnames.append(field.name)

        for cfield in correct_fields:
            self.assertIn(cfield, fieldnames)

    def test_length(self):
        """
        Ensures that the mutated file, depending on which it is, is the correct needed length
        :return:
        """
        if self.testObject.title not in ["Preview", "Stage", "Append", "Replace"]:
            return
        source_table = self.build_data_frame(self.sourceDataPath, tuple([field.name for field in self.sourceFields]))
        local_table = self.build_data_frame(self.localDataPath, tuple([field.name for field in self.localFields]))
        # target_table = (list(arcpy.da.SearchCursor(self.targetDataPath, "*")))
        target_table = self.build_data_frame(self.targetDataPath, tuple([field.name for field in self.targetFields]))
        mode = self.testObject.title  # variable assignment to help with readability
        if mode == "Preview":
            if len(source_table) < self.testObject.RowLimit:
                self.assertEqual(len(local_table), len(source_table))
            else:
                self.assertEqual(len(local_table), self.testObject.RowLimit)
        elif mode == "Stage":
            self.assertEqual(len(local_table), len(source_table))
        elif mode == "Append":
            self.assertEqual(len(target_table), len(local_table) + len(source_table))
        elif mode == "Replace":
            self.assertEqual(len(target_table), len(local_table))
        else:
            self.assertIn(mode, ["Preview", "Stage", "Append", "Replace"])

    def test_replace_data(self):
        """
        Ensures the correct rows were appended and removed and in the correct order
        :return:
        """
        replaced_rows_list = []
        targetfields = list()
        for field in self.targetFields:
            if field.name.lower() not in ['globalid', 'objectid']:
                targetfields.append(field.name)
        localfields = list()
        for field in self.localFields:
            if field.name.lower() not in ['globalid', 'objectid']:
                localfields.append(field.name)

        copy = self.build_data_frame(self.localDataPath, tuple(localfields)).iterrows()
        target = self.build_data_frame(self.targetDataPath, tuple(targetfields)).iterrows()
        replace_dict = self.get_xml_parse().parse_replace()
        for copy_row, targetRow in zip(copy, target):  # will iterate through until all of the copy cursor is exhausted
            copy_row = copy_row[1]
            targetRow = targetRow[1]
            while not targetRow.equals(copy_row):
                replaced_rows_list.append(copy_row)
                copy_row = next(copy)
                copy_row = copy_row[1]

        for targetRow, copy_row in zip(target, replaced_rows_list):
            # now iterates through the rows that should have been
            targetRow = targetRow[1]
            #  these assertions make sure the targetRow SHOULD have been replaced
            if replace_dict["Operator"] == "=":
                self.assertEqual(targetRow[replace_dict["FieldName"]], replace_dict["Value"])
            if replace_dict["Operator"] == "!=":
                self.assertNotEqual(targetRow[replace_dict["FieldName"]], replace_dict["Value"])
            if replace_dict["Operator"] == "Like":
                self.assertIn(replace_dict["Value"], targetRow[replace_dict["FieldName"]])
            self.assertTrue(targetRow.equals(copy_row))
            # appended to ensure order and accuracy. Here the target cursor starts
            # at where the beginning of the re-appended rows should be

    def test_data(self):
        """
        Ensures that the mutated file has the correct data in each row, and that the data asisstant actions were
        performed correctly
        :return:
        """
        source_table = self.build_data_frame(self.sourceDataPath, tuple([field.name for field in self.sourceFields]))
        local_table = self.build_data_frame(self.localDataPath, tuple([field.name for field in self.localFields]))
        target_table = self.build_data_frame(self.targetDataPath, tuple([field.name for field in self.targetFields]))
        parse_object = self.get_xml_parse()
        parse_object.data = parse_object.parse()
        xml_fields = parse_object.get_pairings()
        method_dict = parse_object.get_methods()
        xml_data = parse_object.get_data()
        default_values = self.get_default_values()

        if self.testObject.title in ["Preview", "Stage"]:  # needed so that we can use the same function to test append
            target = local_table
        else:
            if 'GLOBALID' in target_table.columns:
                target_table = target_table.drop('GLOBALID', 1)  # TODO: Might need to omit other itrations of globalid
            if 'GLOBALID' in local_table.columns:
                local_table = local_table.drop('GLOBALID', 1)  # TODO: Might need to omit other itrations of globalid
            # self.assertTrue(local_table.equals(target_table.head(len(local_table))))
            self.assertTrue((local_table == target_table.head(len(local_table))).all().all())
            target = target_table.drop(range(len(local_table)))  # ensures we are only comparing the newly appended data

        for field in xml_fields.keys():
            if method_dict[field] == self.methods["None"]:
                self.none_test(target[field], default_values[field])
            elif method_dict[field] == self.methods["Copy"]:
                self.copy_test(source_table[xml_fields[field]], target[field])
            elif method_dict[field] == self.methods["Set Value"]:
                self.set_value_test(target[field], xml_data[field][self.methods["Set Value"]])
            elif method_dict[field] == self.methods["Value Map"]:
                self.value_map_test(source_table[xml_fields[field]], target[field],
                                    xml_data[field][self.methods["Value Map"]], xml_data[field]["Otherwise"])
            elif method_dict[field] == self.methods["Change Case"]:
                self.change_case_test(source_table[xml_fields[field]], target[field],
                                      xml_data[field][self.methods["Change Case"]])
            elif method_dict[field] == self.methods["Concatenate"]:
                self.concatenate_test(target[field], xml_data[field]["Separator"],
                                      xml_data[field]["Concatenate"])
            elif method_dict[field] == self.methods["Left"]:
                self.left_test(source_table[xml_fields[field]], target[field], xml_data[field]["Left"])
            elif method_dict[field] == self.methods["Right"]:
                self.right_test(source_table[xml_fields[field]], target[field], xml_data[field]["Right"])
            elif method_dict[field] == self.methods["Substring"]:
                self.substring_test(source_table[xml_fields[field]], target[field], xml_data[field]["Start"],
                                    xml_data[field]["Length"])
            elif method_dict[field] == self.methods["Split"]:
                self.split_test(source_table[xml_fields[field]], target[field], xml_data[field]["SplitAt"],
                                xml_data[field]["Part"])
            elif method_dict[field] == self.methods["Conditional Value"]:
                self.conditional_value_test(source_table[xml_fields[field]], target[field],
                                            xml_data[field]["Oper"], xml_data[field]["If"], xml_data[field]["Then"],
                                            xml_data[field]["Else"])
            elif method_dict[field] == self.methods["Domain Map"]:
                self.domain_map_test(source_table[xml_fields[field]], target[field],
                                     xml_data[field][self.methods["Domain Map"]])
            else:
                self.assertIn(method_dict[field], self.methods)

    def none_test(self, target: pd.Series, defaultValue):
        """
        Ensures that the vector is a vector of none
        :param target:
        :param defaultValue:
        :return:
        """
        self.assertTrue(len(target.unique()) == 1 and (
            target.unique()[0] is None or target.unique()[0] == 'None' or target.unique()[0] == defaultValue),
                        target.to_string())

    def copy_test(self, source: pd.Series, target: pd.Series):
        """
         Ensures that the copy source got copied to the target. In other words, ensures that the two vectors are equal.
        """
        self.assertTrue((source == target.astype(source.dtype)).all(),
                        "Mis-match bewteen these fields: " + source.name + " " + target.name)

    def set_value_test(self, target: pd.Series, value: pd.Series):
        """
        Ensures that the target values are all set properly
        :param target:
        :param value:
        :return:
        """
        self.assertTrue(len(target.unique()) == 1 and target.unique() == value)

    def value_map_test(self, source: pd.Series, target: pd.Series, value_dict: dict, otherwise):
        """
        Ensures the values are set to what they need to be based on the preset configuration in the value map
        :param source:
        :param target:
        :param value_dict
        :param otherwise
        :return:
        """
        for s, t in zip(source, target):
            if s in value_dict:
                self.assertTrue(str(t) == str(value_dict[s]), str(t) + " != " + str(value_dict[s]))
            else:
                self.assertTrue(str(t) == str(otherwise))

    def change_case_test(self, source: pd.Series, target: pd.Series, manipulation: str):
        """
        Ensures the row correctly was changed
        :param source:
        :param target:
        :param manipulation: str
        :return:
        """
        if manipulation == "Uppercase":
            self.assertTrue((source.str.upper() == target).all())
        elif manipulation == "Lowercase":
            self.assertTrue((source.str.lower() == target).all())
        elif manipulation == "Capitalize":
            self.assertTrue((source.str.capitalize() == target).all())
        elif manipulation == "Title":
            self.assertTrue((source.str.title() == target).all())
        else:
            self.assertIn(manipulation, ["Uppercase", "Lowercase", "Capitalize", "Title"])

    def concatenate_test(self, target: pd.Series, seperator: str,
                         cfields: list):
        """
        Ensures the row concatenates the correct field values
        :param target:
        :param seperator:
        :param cfields:
        :return:
        """
        source_table = self.build_data_frame(self.sourceDataPath, tuple([field.name for field in self.sourceFields]))
        if seperator == "(space)":
            seperator = " "
        compare_column = source_table[cfields.pop(0)]
        for cfield in cfields:
            right = source_table[cfield].replace("NaN", "").astype(str)
            compare_column = compare_column.astype(str).str.cat(right, sep=seperator)
        self.assertTrue((target == compare_column).all())

    def left_test(self, source: pd.Series, target: pd.Series, number: int):
        """
        Ensures the correct number of charcters from the left were mapped
        :param source:
        :param target
        :param number: int
        :return:
        """
        self.assertTrue((source.astype(str).apply(lambda f: f[:number]) == target.astype(str)).all())

    def right_test(self, source: pd.Series, target: pd.Series, number: int):
        """
        Ensures the correct number of characters from the right were mapped
        :param source:
        :param target:
        :param number:
        :return:
        """
        self.assertTrue((source.astype(str).apply(lambda f: f[:-number]) == target.astype(str)).all())

    def substring_test(self, source: pd.Series, target: pd.Series, start: int, length: int):
        """
        Ensures the correct substring was pulled from each row
        :param source:
        :param target:
        :param start:
        :param length:
        :return:
        """
        self.assertTrue((source.astype(str).apply(lambda f: f[start:length + start]) == target.astype(str)).all())

    def split_test(self, source: pd.Series, target: pd.Series, split_point: str, part: int):
        """
        Ensures the correct split was made and the resulting data is correct
        :param source:
        :param target:
        :param split_point:
        :param part:
        :return:
        """
        for sfield, tfield in zip(source, target):
            self.assertTrue(sfield.split(split_point)[part] == tfield)

    def conditional_value_test(self, source: pd.Series, target: pd.Series, oper: str, if_value,
                               then_value, else_value):
        """
        Ensures that the conditional value evaluates correctly in each row of the column
        :param source:
        :param target:
        :param oper:
        :param if_value:
        :param then_value:
        :param else_value:
        :return:
        """
        for sfield, tfield in zip(source, target):
            if oper == "==":
                if sfield == if_value:
                    self.assertEqual(then_value, tfield)
                else:
                    self.assertEqual(else_value, tfield)
            elif oper == "!'":
                if sfield != if_value:
                    self.assertEqual(then_value, tfield)
                else:
                    self.assertEqual(else_value, tfield)
            elif oper == "<":
                if sfield < if_value:
                    self.assertEqual(then_value, tfield)
                else:
                    self.assertEqual(else_value, tfield)
            elif oper == ">":
                if sfield > if_value:
                    self.assertEqual(then_value, tfield)
                else:
                    self.assertEqual(else_value, tfield)
            else:
                self.assertIn(oper, ["==", "!=", "<", ">"])

    def domain_map_test(self, source: pd.Series, target: pd.Series, mappings: dict):
        """
        Ensures the domain map pairings are correctly mapped in the target column
        :param self:
        :param source:
        :param target:
        :param mappings:
        :return:
        """
        for s, t in zip(source, target):
            if s in mappings:
                if mappings[s] == "(None)":
                    # In the event that a is loaded in the xml but not mapped to any target domain, we want to
                    # make sure that the source and target values are the same
                    self.assertEqual(s, t)
                self.assertEqual(mappings[s], t)

    def test_xml(self):
        """
        Tests to see that the newly created xml file is equal to a pre-determined correct file
        :return:
        """
        if self.testObject.title != "CreateConfig":
            return
        out_xml = ET.parse(self.outXML).getroot()
        correct_xml = ET.parse(self.correctXML).getroot()
        self.assertTrue(xml_compare(out_xml, correct_xml))

    def destage(self):
        """
        After staging is done, the xml reflects there should be a feature class that append can use to append to source.
        This function deletes this line in the xml so the xml can be used again or so append can recreate the mapping.
        :return:
        """
        xml = ET.parse(self.xmlLocation)
        root = xml.getroot()
        datasets = root.getchildren()[0]
        staged = datasets.getchildren()[len(datasets.getchildren()) - 1]
        if staged.tag == "Staged":
            datasets.remove(staged)
            xml.write(self.xmlLocation)

    def main(self):
        """
        Runs all of the tests
        :return:
        """
        if self.testObject.title == "CreateConfig":
            self.test_create()
            self.test_xml()
            return
        else:
            self.test_create()
            self.test_length()
            self.test_fields()
            if self.testObject.title == 'Replace':
                self.test_replace_data()
            else:
                self.test_data()


class SourceTargetParser(object):
    """
    Class designed to store the essential parts of the xml file in readable python data structrues
    """

    def __init__(self, xml_file: str):
        self.xmlLocation = xml_file
        self.xml = ET.parse(self.xmlLocation).getroot()
        self.targetFields = []
        self.methods = _XMLMethodNames  # not actually the methods in this file, just the naming syntax for the xml
        self.data = dict()

    @functools.lru_cache()
    def get_sourcefields(self):
        """
        Returns and caches the source names as specified in the xml. Some might be None if there is no mapping to the
        corresponding target field.
        :return:
        """
        sourcefields = []
        fields = self.xml.find('Fields').getchildren()
        for field in fields:
            sourceName = field.find('SourceName').text
            sourcefields.append(sourceName)
        return sourcefields

    def get_data(self):
        """
        Returns the xml data
        :return: dict
        """
        return self.data

    @functools.lru_cache()
    def get_targetfields(self):
        """
        Returns and caches the target field names as specified in the xml.
        :return:
        """
        targetfields = []
        fields = self.xml.find('Fields').getchildren()
        for field in fields:
            targetName = field.find('TargetName').text
            targetfields.append(targetName)
        return targetfields

    @functools.lru_cache()
    def get_pairings(self) -> dict:
        """
        Returns a dictionary where key is TargetName and value is SourceName for each field
        :return: dict
        """
        pairings = dict()
        fields = self.xml.find('Fields').getchildren()
        for field in fields:
            sourcename = field.find('SourceName').text
            targetname = field.find('TargetName').text
            pairings[targetname] = sourcename
        return pairings

    @functools.lru_cache()
    def get_methods(self) -> dict:
        """
        Returns and caches the methods in order of appearence in the xml file.
        :return:
        """
        method_dict = dict()
        fields = self.xml.find('Fields').getchildren()
        for field in fields:
            targetname = field.find('TargetName').text
            method = field.find('Method').text
            method_dict[targetname] = method
        return method_dict

    @functools.lru_cache()
    def parse_replace(self) -> dict:
        """
        Returns a dictionary with the information used by Replace By Field Value
        :return: dict
        """
        datasets = self.xml.find('Datasets')
        replace_by = datasets.find('ReplaceBy')
        if len(replace_by.getchildren()) == 0:
            raise (AssertionError("ReplaceBy is empty in the XML"))
        outdict = dict()
        outdict["FieldName"] = replace_by.find('FieldName').text
        outdict['Operator'] = replace_by.find('Operator').text
        outdict['Value'] = replace_by.find('Value').text

        return outdict

    def parse(self):
        """
        Interprets the xml file and stores the information in appropriate places
        :return:
        """
        data = dict()
        fields = self.xml.find('Fields').getchildren()
        for field in fields:
            target_name = field.find('TargetName').text
            method = field.find('Method').text  # added for visibility

            if method == self.methods["Set Value"]:
                data[target_name] = dict()
                data[target_name][self.methods["Set Value"]] = field.find(self.methods["Set Value"]).text
            elif method == self.methods["Domain Map"]:
                domain_map = field.find(self.methods["Domain Map"]).getchildren()
                data[target_name] = dict()
                data[target_name][self.methods["Domain Map"]] = dict()
                for tag in domain_map:
                    if tag.tag == "sValue":
                        svalue = tag.text
                    if tag.tag == "tValue":
                        data[target_name][self.methods["Domain Map"]][svalue] = tag.text
                        svalue = ""
            elif method == self.methods["Value Map"]:
                value_map = field.find(self.methods["Value Map"]).getchildren()
                data[target_name] = dict()
                data[target_name][self.methods["Value Map"]] = dict()
                for tag in value_map:
                    if tag.tag == "sValue":
                        svalue = tag.text
                    elif tag.tag == "tValue":
                        data[target_name][self.methods["Value Map"]][svalue] = tag.text
                        svalue = ""
                    elif tag.tag == "Otherwise":
                        data[target_name]["Otherwise"] = tag.text
            elif method == self.methods["Change Case"]:
                data[target_name] = dict()
                data[target_name][self.methods["Change Case"]] = field.find(self.methods["Change Case"]).text
            elif method == self.methods["Concatenate"]:
                data[target_name] = dict()
                data[target_name][self.methods["Concatenate"]] = list()
                data[target_name]["Separator"] = field.find("Separator").text
                cfields = field.find("cFields").getchildren()
                for cfield in cfields:
                    data[target_name][self.methods["Concatenate"]].append(cfield.find('Name').text)
            elif method == self.methods["Left"]:
                data[target_name] = dict()
                data[target_name][self.methods["Left"]] = int(field.find(self.methods["Left"]).text)
            elif method == self.methods["Right"]:
                data[target_name] = dict()
                data[target_name][self.methods["Right"]] = int(field.find(self.methods["Right"]).text)
            elif method == self.methods["Substring"]:
                data[target_name] = dict()
                data[target_name]["Start"] = int(field.find('Start').text)
                data[target_name]["Length"] = int(field.find('Length').text)
            elif method == self.methods["Split"]:
                data[target_name] = dict()
                data[target_name]["SplitAt"] = field.find("SplitAt").text
                data[target_name]["Part"] = int(field.find("Part").text)
            elif method == self.methods["Conditional Value"]:
                data[target_name] = dict()
                data[target_name]["Oper"] = field.find("Oper").text.strip("\'").strip("\"")
                data[target_name]["If"] = field.find("If").text.strip("\'").strip("\"")
                data[target_name]["Then"] = field.find("Then").text.strip("\'").strip("\"")
                data[target_name]["Else"] = field.find("Else").text.strip("\'").strip("\"")
            else:
                assert method in self.methods.values()

        return data


def make_temp_file() -> tempfile.TemporaryDirectory:
    """
    Returns a temporary directory that is used to store the local data for the tests
    :return:
    """
    localfolder = str(pathlib.Path(".\localData").absolute())
    return tempfile.TemporaryDirectory(dir=localfolder)


def change_workspace(lw: list, tmp_name: str) -> list:
    """
    Changes the data paths to reflect the new temporary file made
    :param lw: list
    :param tmp_name: str
    :return:
    """
    out_workspace = lw.copy()
    for workspace in out_workspace:
        the_path = ""
        for part in pathlib.Path(workspace["Source"]).parts:
            the_path = os.path.join(the_path, part)
            if part == 'localData':
                the_path = os.path.join(the_path, tmp_name)
        workspace["Source"] = the_path

        the_path = ""
        for part in pathlib.Path(workspace["Target"]).parts:
            the_path = os.path.join(the_path, part)
            if part == 'localData':
                the_path = os.path.join(the_path, tmp_name)
        workspace["Target"] = the_path

    return out_workspace


def set_up_data(tmpdir: str):
    """
    Unzips all data into local directory
    :param tmpdir:
    :return:
    """
    workspace = str(pathlib.Path(".\localData").absolute())
    for file in os.listdir(workspace):
        if ".zip" in file:
            with zipfile.ZipFile(os.path.join(workspace, file)) as unzipper:
                unzipper.extractall(tmpdir)


def change_xml_path(t_workspace: list):
    """
    Changes the source and target path in the xml files for testing
    :param t_workspace:
    :return:
    """
    for workspace in t_workspace:
        xml = ET.parse(workspace["xmlLocation"])
        root = xml.getroot()
        datasets = root.find('Datasets').getchildren()
        for field in datasets:
            if field.tag == "Source":
                field.text = os.path.join(workspace["Source"], workspace["SourceName"])
            if field.tag == "Target":
                field.text = os.path.join(workspace["Target"], workspace["TargetName"])
        xml.write(workspace["xmlLocation"])


if __name__ == '__main__':
    tmp = make_temp_file()
    temp_workspace = change_workspace(_localWorkspace, pathlib.Path(tmp.name).stem)
    set_up_data(tmp.name)
    change_xml_path(temp_workspace)
    try:
        for local_workspace in temp_workspace:
            UnitTests(CreateConfig(local_workspace)).main()
            UnitTests(Preview(local_workspace)).main()
            stage = UnitTests(Stage(local_workspace))
            stage.main()
            stage.destage()
            UnitTests(Append(local_workspace)).main()
            UnitTests(Replace(local_workspace)).main()
    except:
        traceback.print_exc()
        sys.exit(-1)
    finally:
        try:
            tmp.cleanup()
        except PermissionError:
            print("Unable to delete temporary folder: Permission Error")
            pass
