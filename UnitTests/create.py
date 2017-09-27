import os
import shutil
import sys
from inc_datasources import _outputDirectory, _daGPTools
sys.path.insert(0, _daGPTools)
from scripts import dlaCreateSourceTarget, dlaPreview, dlaPublish, dlaStage
import test_All


class BaseClass(object):
    """
    Class used for inheritance that contains basic common information
    """

    def __init__(self, lw):
        self.local_workspace = lw
        self.RowLimit = 0
        self.xmlLocation = lw["xmlLocation"]
        self.globalIDCheck = False  # self.globalIDCheck = dla.processGlobalIds(dla.getXmlDoc(self.xmlLocation))
        self.title = self.__class__.__name__

    def main(self) -> object:
        """
        Will run the specific test script before any tests are done
        :return: bool
        """
        return True


class CreateConfig(BaseClass):
    """
    A class that is designed to create and house information to test dlaCreateSourceTarget
    """

    def __init__(self, lw: list):
        super().__init__(lw)

    # def importUtilNetworkToolbox():
    #     parentPath = os.path.join(str(pathlib.Path(__file__).parents[1]), 'UtilityNetworkConfigurationTools')
    #     python_toolbox = os.path.join(parentPath, 'UtilityNetworkConfigurationTools.pyt')
    #     sys.path.insert(0, parentPath)
    #     if sys.version_info[:2] >= (3, 5):
    #         # import importlib.util
    #         # spec = importlib.util.spec_from_file_location("UtilityNetworkSchemaTools.pyt", parentPath)
    #         # return importlib.util.module_from_spec(spec)
    #         import types
    #         from importlib.machinery import SourceFileLoader
    #         loader = SourceFileLoader("UtilityNetworkConfigurationTools", python_toolbox)
    #         pyt = types.ModuleType(loader.name)
    #         loader.exec_module(pyt)
    #         return pyt
    #     elif sys.version_info[:2] >= (3, 4):
    #         import types
    #         from importlib.machinery import SourceFileLoader
    #         loader = SourceFileLoader("UtilityNetworkConfigurationTools", python_toolbox)
    #         pyt = types.ModuleType(loader.name)
    #         loader.exec_module(pyt)
    #         return pyt
    #     elif sys.version_info[:2] >= (3, 3):
    #         from importlib.machinery import SourceFileLoader
    #         return SourceFileLoader('UtilityNetworkConfigurationTools', python_toolbox).load_module()
    #     else:
    #         import imp
    #         return imp.load_source('UtilityNetworkConfigurationTools', python_toolbox)

    def main(self):
        """
        Runs the initial action of the test and returns it
        :return: boolean
        """
        source_path = os.path.join(self.local_workspace["Source"], self.local_workspace["SourceName"])
        target_path = os.path.join(self.local_workspace["Target"], self.local_workspace["TargetName"])
        field_matcher = os.path.join(_daGPTools,"scripts")
        shutil.copy(self.local_workspace["MatchLibrary"], field_matcher)
        return dlaCreateSourceTarget.createDlaFile(source_path, target_path, self.local_workspace["outXML"])


class Preview(BaseClass):
    """
    A class that is designed to create and house information to test dlaPreview
    """

    def __init__(self, lw, rl=100):
        super().__init__(lw)
        self.RowLimit = rl

    def main(self):
        """
        Creates a preview feature class in dla.gdb for testing
        :return: None or False
        """
        return dlaPreview.preview(self.xmlLocation, False, self.RowLimit)  # creates the new feature class


class Stage(BaseClass):
    """
    A class that is designed to create and house information to test dlaStage
    """

    def __init__(self, lw):
        super().__init__(lw)

    def main(self):
        """
        Creates a staged version of the code in a feature class in dla.gdb for testing
        :return: None or False
        """
        return dlaStage.stage(self.xmlLocation, False)  # creates the new feature class


class Append(BaseClass):
    """
    A class that is designed to create and house information to test dlaAppend
    """

    def __init__(self, lw: dict):
        super().__init__(lw)
        self.directory = _outputDirectory

    def main(self):
        """
        Creates a copy of the target data and saves it to a feature class in dla.gdb. It then appends data
        onto the end of target for testing
        :return:
        """
        test_All.make_copy(self.directory, self.local_workspace)
        dlaPublish._useReplaceSettings = False
        return dlaPublish.publish(self.xmlLocation, False, False)


class Replace(BaseClass):
    """
    A class that is designed to create and house information to test dlaReplaceByField
    """

    def __init__(self, lw: dict):
        super().__init__(lw)
        self.directory = _outputDirectory

    def main(self):
        """
        Applys the ReplaceByField operation specified in the xml file to the data for testing
        :return: None or False
        """
        test_All.make_copy(self.directory, self.local_workspace)
        dlaPublish._useReplaceSettings = True
        return dlaPublish.publish(self.xmlLocation, False, True)
