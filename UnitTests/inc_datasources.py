import os
import pathlib

# Path to Data Assistant tools
_daGPTools = str((pathlib.Path(__file__).parents[1] / "Shared\\GPTools\\pyt").absolute())
# location for local output
_localOutputPath = str(pathlib.Path(__file__).parents[0] / 'testOutput')
_outputDirectory = os.path.join(_daGPTools, 'scripts', 'dla.gdb')

########### Source and Target ##########
_localWorkspace = list()
'''
Local workspace is a list that contains a dictionary storing the paths relevant for the tests to work. Below is a
template of what it should look like. All keys must have values attached for the tests to work.
'''
template = {"Source": "A string that contains the absolute path to the source data",
            "Target": "A string that contains the absolute patht to the target data",
            "SourceName": "The name of the feature class, table, layer, or layer file",
            "TargetName": "The name of the feature class, table, layer, or layer file",
            "xmlLocation": "The absolute path to a pre-created xml file that will be run for the tests",
            "outXML": "The absolute path to the XML that will be created during New File testing",
            "correctXML": "The absolute path to an XML that should match the newly created XML made from New File."
                          "This file is to test the match library on a New File test as well as to test whether or not New File worked",
            "MatchLibrary": "The absolute path to the match library xml that should be used when New File is tested"}

########## XML Syntax ############
# XML Method Names. Change these if XML formatting ever changes
_XMLMethodNames = {"None": "None",
                   "Copy": "Copy",
                   "Set Value": "SetValue",
                   "Value Map": "ValueMap",
                   "Change Case": "ChangeCase",
                   "Concatenate": "Concatenate",
                   "Left": "Left",
                   "Right": "Right",
                   "Substring": "Substring",
                   "Split": "Split",
                   "Conditional Value": "ConditionalValue",
                   "Domain Map": "DomainMap"}
