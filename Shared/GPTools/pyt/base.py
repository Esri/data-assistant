import arcpy

from validate import Validator


class DAbase(object):
    """
    Contains methods used across all scripts
    """

    @staticmethod
    def get_xml_parameter(**kwargs):
        """Returns xml parameter object based on specifications in argument"""
        xml_parameter = arcpy.Parameter(name="xml_file",
                                        displayName="Source Configuration File",
                                        direction="Input",
                                        datatype="File",
                                        parameterType="Required")
        xml_parameter.filter.list = ["xml"]
        for k, v in kwargs.items():
            setattr(xml_parameter, k, v)
        return xml_parameter

    @staticmethod
    def get_continue(**kwargs):
        """Returns a parameter object to check if the script should continue on to the next xml after an error"""
        c = arcpy.Parameter(name="continue_on_error",
                            displayName="Continue on error",
                            direction="Input",
                            datatype="Boolean",
                            parameterType="Optional")
        for k, v in kwargs.items():
            setattr(c, k, v)
        return c

    @staticmethod
    def get_output_layer(**kwargs):
        """Returns a parameter specifying an output layer"""
        l = arcpy.Parameter(name="output_layers",
                            displayName="Output Layers",
                            datatype=["GPLayer", "DETable", "DELayer"],
                            multiValue=True,
                            direction="Output",
                            parameterType="Derived")
        for k, v in kwargs.items():
            setattr(l, k, v)
        return l

    @staticmethod
    def get_input_layer(**kwargs):
        """Return an input layer for New File"""
        p = arcpy.Parameter(name="input_layer",
                            displayName="Input Layer",
                            datatype=["GPLayer", "DELayer", "DETable", "DEFeatureClass"],
                            direction="Input",
                            parameterType="Required")
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    @staticmethod
    def get_row_limit(**kwargs):
        """Returns a row limit field for dlaPreview"""
        p = arcpy.Parameter(name="row_limit",
                            displayName="Row Limit",
                            datatype="GPLong",
                            direction="Input",
                            parameterType="Optional")
        p.value = 100
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    @staticmethod
    def create_layers(source, target):
        """Creates layer objects out of the source and target parameters"""
        sDescribe = arcpy.Describe(source)
        tDescribe = arcpy.Describe(target)

        if sDescribe.dataType in ['FeatureLayer', 'Table']:
            source_layer = source
        elif sDescribe.dataType == 'Layer':
            source_layer = arcpy.mp.LayerFile(source).listLayers()[0]
        else:
            source_layer = arcpy.MakeFeatureLayer_management(source, "source")[0]

        if tDescribe.dataType in ['FeatureLayer', 'Table']:
            target_layer = target
        elif tDescribe.dataType == 'Layer':
            target_layer = arcpy.mp.LayerFile(target).listLayers()[0]
        else:
            target_layer = arcpy.MakeFeatureLayer_management(target, "target")[0]

        return [source_layer, target_layer]

    def run_validation(self, parameters, new_file=False):
        """Runs the validation for most GPTool parameters"""
        if not new_file:
            xmls = ParamWrapper(parameters[0]).getValues()
            for i in range(len(xmls)):
                validator = Validator.from_xml(xmls[i])
                validator.validate()
                if validator.source_error is not None:
                    if validator.source_error.severity == "ERROR":
                        parameters[0].setErrorMessage("xml " + str(i+1)+":"+validator.source_error.message)
                    else:
                        parameters[0].setWarningMessage("xml " + str(i+1)+":"+validator.source_error.message)
                elif validator.target_error is not None:
                    if validator.target_error.severity == "ERROR":
                        parameters[0].setErrorMessage("xml " + str(i+1)+":"+validator.target_error.message)
                    else:
                        parameters[0].setWarningMessage("xml " + str(i+1)+":"+validator.target_error.message)
        else:
            params = [ParamWrapper(p).getValues() for p in parameters]
            source, target, xml = params
            if source is None or target is None:
                return  # Don't want to run validation until both a source and target are chosen
            # slayer, tlayer = self.create_layers(source, target)
            validator = Validator(source=source, target=target)
            validator.validate()
            if validator.source_error is not None:
                if validator.source_error.severity == "ERROR":
                    parameters[0].setErrorMessage(validator.source_error.message)
                else:
                    parameters[0].setWarningMessage(validator.source_error.message)
            if validator.target_error is not None:
                if validator.target_error.severity == "ERROR":
                    parameters[1].setErrorMessage(validator.target_error.message)
                else:
                    parameters[1].setWarningMessage(validator.target_error.message)


class ParamWrapper(object):
    def __init__(self, param):
        self._p = param
        # We're assuming that objects with parameterType properties are arcpy.Parameter() objects
        if hasattr(self._p, 'parameterType'):
            self._values = self.__convert()
        else:
            self._values = param

    @staticmethod
    def __get_value(value_obj):
        try:
            return value_obj.values
        except (AttributeError, NameError):
            if hasattr(value_obj, 'value'):
                while hasattr(value_obj, 'value'):
                    # Special case for DEUtilityNetwork datatype that is accessed as p.value.value
                    value_obj = value_obj.value
                ret = value_obj
            else:
                ret = value_obj

            # Convert empty strings to None
            if isinstance(ret, str) and not ret:
                ret = None
            return ret

    def __convert(self):
        values = self.__get_value(self._p)
        # Value Table is a special parameter type
        if type(self._p.datatype) is not list and self._p.datatype.upper() == 'VALUE TABLE':
            return [[self.__get_value(cell) for cell in row] for row in values or []]
        elif self._p.multiValue:
            if values is None:
                # If an optional multivalue parameter is not specified, None is the value.
                # Change this to an empty list as the code will *generally* be expecting a list to iterate over.
                return []
            else:
                return [self.__get_value(v) for v in values]
        else:
            return values

    def getValues(self):
        return self._values
