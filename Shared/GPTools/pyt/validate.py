import xml.etree.cElementTree as ET
from collections import namedtuple

import arcpy
from arcpy import _mp

message = namedtuple("message", ["message", "function"])


class Validator(object):
    """Validator class that handles high level syntax validation"""

    def __init__(self, source: arcpy._mp.Layer, target: arcpy._mp.Layer):
        self.source = source
        self.target = target
        self.message = namedtuple("message", ["message", "severity"])
        self.describe_source = arcpy.Describe(source)
        self.describe_target = arcpy.Describe(target)
        self.source_is_table = self.describe_source.dataType == 'Table'
        self.target_is_table = self.describe_target.dataType == 'Table'
        self.source_error = None
        self.target_error = None

    @classmethod
    def from_xml(cls, xml):
        """Parses xml to find the source and target layer objects or table path"""
        tree = ET.parse(xml)
        root = tree.getroot()
        datasets = root.find("Datasets")
        source_path = datasets.find("Source").text
        target_path = datasets.find("Target").text
        if arcpy.Describe(source_path).dataType != "Table":
            source = arcpy.MakeFeatureLayer_management(source_path)[0]
        else:
            source = source_path
        if arcpy.Describe(target_path).dataType != "Table":
            target = arcpy.MakeFeatureLayer_management(target_path)[0]
        else:
            target = target_path
        # source =source_path
        # target = target_path
        return cls(source, target)

    def validate_broken(self, param):
        """Ensures the layer files are connected to their data sources"""
        if param.isBroken:
            return self.message("{}'s  dataset is corrupted or not connected to this layer".format(param.name), "ERROR")

    def validate_same_shape(self, param):
        """Validates the two datasets are of the same shape type"""
        try:
            if self.describe_source.shapeType != self.describe_target.shapeType:
                return self.message("Source and target must be of the same shape type", "ERROR")
        except AttributeError:  # Weird and fringe case that the describe object does not have shapeType. A different
            pass  # validation error should trigger if this is that case

    def validate_datatype(self, param):
        """Validates the underlying dataType of the two inputs are the same"""
        sd = self.describe_source.datasetType
        td = self.describe_target.datasetType
        if sd != td:
            return self.message("Unable to map data type " + sd + " to data type " + td, "ERROR")

    def validate_target_join(self, param):
        """Validates that the target layer is not a joined layer"""
        if "join_type" in param.connectionProperties:
            return self.message("Target layer cannot be a joined layer", "ERROR")

    def validate_featurelayer(self, param):
        """Validate the layer is FeatureLayer type"""
        if not param.isFeatureLayer:
            return self.message("{} must be a feature layer".format(param.name), "ERROR")

    def validate_source_length(self, param):
        """Validate that source has more than zero rows"""
        if not int(arcpy.GetCount_management(param)[0]):
            return self.message("Source has 0 rows", "WARNING")

    def validate(self):
        """Runs the other validations and returns a report"""
        if self.source_is_table or self.target_is_table:
            self.target_error = self.validate_datatype(self.target)
        else:
            source_funcs = [self.validate_featurelayer, self.validate_broken, self.validate_source_length]
            for func in source_funcs:
                result = func(self.source)
                if result is not None:
                    self.source_error = result
                    break

            target_funcs = [self.validate_same_shape, self.validate_datatype, self.validate_target_join,
                            self.validate_featurelayer, self.validate_broken]
            for func in target_funcs:
                result = func(self.target)
                if result is not None:
                    self.target_error = result
                    break
