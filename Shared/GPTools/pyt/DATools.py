import scripts
from base import DAbase, ParamWrapper
import arcpy
from validate import Validator

class Append(DAbase):
    """
    Tool calling the Append tool in Data Assistant
    """

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Append Data"
        self.description = "Appends data to target dataset"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        xml_parameter = self.get_xml_parameter(multiValue=True)
        continue_on_error = self.get_continue()
        output_layer = self.get_output_layer()
        return [xml_parameter, continue_on_error, output_layer]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        params = [ParamWrapper(p).getValues() for p in parameters[:-1]]
        xml, continue_on_error = params
        results = self.run(xml, continue_on_error)
        arcpy.SetParameter(len(params)-1, results)

    @staticmethod
    def run(xml: list, continue_on_error: bool):
        """Calls the dla script"""
        return scripts.dlaPublish.publish(xml, continue_on_error, False)

class Replace(DAbase):
    """
    Tool calling the Append tool in Data Assistant
    """

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Replace Data"
        self.description = "Replace rows in target data set based on a certain field"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        xml_parameter = self.get_xml_parameter(multiValue=True)
        continue_on_error = self.get_continue()
        output_layer = self.get_output_layer()
        return [xml_parameter, continue_on_error, output_layer]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        params = [ParamWrapper(p).getValues() for p in parameters[:-1]]
        xml, continue_on_error = params
        results = self.run(xml, continue_on_error)
        arcpy.SetParameter(len(params)-1, results)

    @staticmethod
    def run(xml: list, continue_on_error: bool):
        """Calls the dla script"""
        return scripts.dlaPublish.publish(xml, continue_on_error, True)


class NewFile(DAbase):
    """Tool calling the Stage tool in Data Assitant"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Source-Target Configuration File"
        self.description = "Build the xml file for a specified source and target data set"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        source_layer = self.get_input_layer(name="source", displayName="Source Dataset")
        target_layer = self.get_input_layer(name="target", displayName="Target Dataset")
        output_xml = self.get_xml_parameter(direction="Output")
        parameters = [source_layer, target_layer, output_xml]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        params = [ParamWrapper(p).getValues() for p in parameters]
        source, target, xml = params
        results = self.run(source, target, xml)
        arcpy.SetParameter(len(params)-1, results)

    @staticmethod
    def run(source, target, xml):
        """Calls the dla script"""
        return scripts.dlaCreateSourceTarget.createDlaFile(source, target, xml)


class Stage(DAbase):
    """Tool calling the Stage tool in Data Assitant"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stage Data"
        self.description = "Stages data to intermediate dataset"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        xml_parameter = self.get_xml_parameter(multiValue=True)
        continue_on_error = self.get_continue()
        output_layer = self.get_output_layer()
        parameters = [xml_parameter, continue_on_error, output_layer]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        params = [ParamWrapper(p).getValues() for p in parameters[:-1]]
        xml_param, continue_on_error = params
        results = self.run(xml_param, continue_on_error)
        arcpy.SetParameter(len(parameters)-1, results)

    @staticmethod
    def run(xml: list, continue_on_error: bool):
        """Calls the dla script"""
        return scripts.dlaStage.stage(xml, continue_on_error)


class Preview(DAbase):
    """Tool calling the Stage tool in Data Assitant"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Preview Data"
        self.description = "Previews a set number of rows of data to intermediate dataset"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        xml_parameter = self.get_xml_parameter(multiValue=True)
        continue_on_error = self.get_continue()
        row_parameter = self.get_row_limit()
        output_layer = self.get_output_layer()
        parameters = [xml_parameter, continue_on_error, row_parameter, output_layer]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        params = [ParamWrapper(p).getValues() for p in parameters[:-1]]
        xml_param, continue_on_error, row_param = params
        results = self.run(xml_param, continue_on_error, row_param)
        if results:
            arcpy.SetParameter(len(parameters)-1, results)

    @staticmethod
    def run(xml: list, continue_on_error: bool, rlimit: int):
        """Calls the dla script"""
        return scripts.dlaPreview.preview(xml, continue_on_error, rlimit)
