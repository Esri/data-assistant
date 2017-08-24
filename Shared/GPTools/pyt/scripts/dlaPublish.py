import os
import DATools
import validate
import arcpy

from . import dlaExtractLayerToGDB, dlaFieldCalculator, dla, dlaService

"""
-------------------------------------------------------------------------------
 | Copyright 2016 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 ------------------------------------------------------------------------------
 """
# dlaPublish.py - Publish one source to a target
# ----------------------------------------------------------------------------------------------------------------------
'''
This script is called by both Append Data and Replace Data tools. It has several options for running
the tool using as a Geoprocessing script directly or by callng dlaPublish.publish from another script.

Note in the GP script approach a source and target dataset can be provided as parameters to override the settings
in the Xml Config file. In this case just a single xml file should be passed with the datasets as the 2nd and 3rd
parameters. By default this will use the Append approach, to use replace by settings you can also make the
useReplaceSettings variable to change the behavior (see example at the end of this script).
'''


def publish(xmlFileNames, continue_on_error, _useReplaceSettings):
    arcpy.AddMessage("Data Assistant")
    # function called from main or from another script, performs the data update processing
    dla._errCount = 0
    arcpy.SetProgressor("default", "Data Assistant")
    arcpy.SetProgressorLabel("Data Assistant")
    layers = list()

    if type(xmlFileNames) is not list:
        xml_file = xmlFileNames
        xmlFileNames = list()
        xmlFileNames.append(xml_file)

    for xmlFile in xmlFileNames:  # multi value parameter, loop for each file

        validator = validate.Validator.from_xml(xmlFile)
        validator.validate()

        if validator.source_error is not None:
            if validator.source_error.severity == "ERROR":
                dla.addError(validator.source_error.message)
                if continue_on_error:
                    continue
                else:
                    return
            else:
                arcpy.AddWarning(validator.source_error.message)
        if validator.target_error is not None:
            if validator.target_error.severity == "ERROR":
                dla.addError(validator.target_error.message)
                if continue_on_error:
                    continue
                else:
                    return
            else:
                arcpy.AddWarning(validator.target_error.message)

        xmlFile = dla.getXmlDocName(xmlFile)
        dla.addMessage("Configuration file: " + xmlFile)
        xmlDoc = dla.getXmlDoc(xmlFile)  # parse the xml document
        if xmlDoc == None:
            dla.addError("No XML document could be parsed. Please ensure the path to the xml document is correct")
            if continue_on_error:
                continue
            else:
                return
        prj = dla.setProject(xmlFile, dla.getNodeValue(xmlDoc, "Project"))
        if prj == None:
            dla.addError(
                "Unable to open your project, please ensure it is in the same folder as your current project or your Config file")
            if continue_on_error:
                continue
            else:
                return False

        source = dla.getDatasetPath(xmlDoc, "Source")
        target = dla.getDatasetPath(xmlDoc, "Target")
        targetName = dla.getDatasetName(target)
        dla.addMessage(source)
        dla.addMessage(target)

        if dlaService.checkLayerIsService(source) or dlaService.checkLayerIsService(target):
            token = dlaService.getSigninToken()  # when signed in get the token and use this. Will be requested many times during the publish
            # exit here before doing other things if not signed in
            if token == None:
                dla.addError("User must be signed in for this tool to work with services")
                if continue_on_error:
                    continue
                else:
                    return False

        expr = getWhereClause(xmlDoc)
        if _useReplaceSettings == True and (expr == '' or expr == None):
            dla.addError("There must be an expression for replacing by field value, current value = " + str(expr))
            if continue_on_error:
                continue
            else:
                return False

        errs = False
        if dlaService.validateSourceUrl(source) == False:
            dla.addError("Source path does not appear to be a valid feature layer")
            errs = True

        if _useReplaceSettings == True:
            if dlaService.validateTargetReplace(target) == False:
                dla.addError("Target path does not have correct privileges")
                errs = True
        elif _useReplaceSettings == False:
            if dlaService.validateTargetAppend(target) == False:
                dla.addError("Target path does not have correct privileges")
                errs = True

        if errs:
            if continue_on_error:
                continue
            else:
                return False

        dla.setWorkspace()

        if dla.isTable(source) or dla.isTable(target):
            datasetType = 'Table'
        else:
            datasetType = 'FeatureClass'

        # if not dla.isStaged(xmlDoc):
        res = dlaExtractLayerToGDB.extract(xmlFile, None, dla.workspace, source, target, datasetType)
        if res != True:
            table = dla.getTempTable(targetName)
            msg = "Unable to export data, there is a lock on existing datasets or another unknown error"
            if arcpy.TestSchemaLock(table) != True and arcpy.Exists(table) == True:
                msg = "Unable to export data, there is a lock on the intermediate feature class: " + table
            dla.addError(msg)
            print(msg)
            if continue_on_error:
                continue
            else:
                return
        else:
            res = dlaFieldCalculator.calculate(xmlFile, dla.workspace, targetName, False,
                                               continue_on_error)
            if res == True:
                dlaTable = dla.getTempTable(targetName)
                res = doPublish(xmlDoc, dlaTable, target, _useReplaceSettings, continue_on_error)
        # else:
        #     dla.addMessage('Data previously staged, will proceed using intermediate dataset')
        #     dlaTable = dla.workspace + os.sep + dla.getStagingName(source, target)
        #     res = doPublish(xmlDoc, dlaTable, target, _useReplaceSettings, continue_on_error)
        #     if res == True:
        #         dla.removeStagingElement(xmlDoc)
        #         xmlDoc.writexml(open(xmlFile, 'wt', encoding='utf-8'))
        #         dla.addMessage('Staging element removed from config file')

        arcpy.ResetProgressor()
        if res == False:
            err = "Data Assistant Update Failed, see messages for details"
            dla.addError(err)
            print(err)
        else:
            layers.append(target)

    return layers


def doPublish(xmlDoc, dlaTable, target, useReplaceSettings, continue_on_error):
    # either truncate and replace or replace by field value
    # run locally or update agol
    success = False
    expr = ''
    dlaTable = handleGeometryChanges(dlaTable, target)

    if useReplaceSettings == True:
        expr = getWhereClause(xmlDoc)
    if useReplaceSettings == True and (expr == '' or expr == None):
        dla.addError("There must be an expression for replacing by field value, current value = '" + str(expr) + "'")
        return False
    currGlobalIDs = arcpy.env.preserveGlobalIds
    if dla.processGlobalIds(
            xmlDoc) and currGlobalIDs == False:  # both datasets have globalids in the correct workspace types
        arcpy.env.preserveGlobalIds = True
    target = dla.getNodeValue(xmlDoc, "Target")
    if target.startswith("http") == True:
        success = dlaService.doPublishHttp(dlaTable, target, expr, useReplaceSettings)
    else:
        # logic change - if not replace field settings then only append
        if expr != '' and useReplaceSettings == True:
            if dla.deleteRows(target, expr) == True:
                success = dla.appendRows(dlaTable, target, expr, continue_on_error)
            else:
                success = False
        else:
            success = dla.appendRows(dlaTable, target, '', continue_on_error)

    if currGlobalIDs != arcpy.env.preserveGlobalIds:
        arcpy.env.preserveGlobalIds = currGlobalIDs
    return success


def getWhereClause(xmlDoc):
    # get the where clause using the xml document or return ''
    repl = xmlDoc.getElementsByTagName("ReplaceBy")[0]
    fieldName = dla.getNodeValue(repl, "FieldName")
    operator = dla.getNodeValue(repl, "Operator")
    value = dla.getNodeValue(repl, "Value")
    expr = ''
    type = getTargetType(xmlDoc, fieldName)
    if fieldName != '' and fieldName != '(None)' and operator != "Where":
        if type == 'String':
            value = "'" + value + "'"
        expr = fieldName + " " + operator + " " + value

    elif operator == 'Where':
        expr = value
    else:
        expr = ''  # empty string by default

    return expr


def getTargetType(xmlDoc, fname):
    # get the target field type
    for tfield in xmlDoc.getElementsByTagName('TargetField'):
        nm = tfield.getAttribute("Name")
        if nm == fname:
            return tfield.getAttribute("Type")


def handleGeometryChanges(sourceDataset, target):
    # simplfiy polygons
    if dla.isTable(sourceDataset):
        return sourceDataset
    desc = arcpy.Describe(sourceDataset)  # assuming local file gdb
    dataset = sourceDataset
    if desc.ShapeType == "Polygon" and (
                    target.lower().startswith("http://") == True or target.lower().startswith("https://") == True):
        dataset = simplifyPolygons(sourceDataset)
    else:
        dataset = sourceDataset

    return dataset


def simplifyPolygons(sourceDataset):
    # simplify polygons using approach developed by Chris Bus.
    dla.addMessage("Simplifying (densifying) Geometry")
    arcpy.Densify_edit(sourceDataset)
    simplify = sourceDataset + '_simplified'
    if arcpy.Exists(simplify):
        arcpy.Delete_management(simplify)
    if arcpy.Exists(simplify + '_Pnt'):
        arcpy.Delete_management(simplify + '_Pnt')

    arcpy.SimplifyPolygon_cartography(sourceDataset, simplify, "POINT_REMOVE", "1 Meters")
    return simplify
