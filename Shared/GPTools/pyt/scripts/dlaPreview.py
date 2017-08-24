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
import datetime
import os

# dlaPreview.py - Preview one source to a target with a limited number of rows
# ------------------------------------------------------------------------------------
import arcpy

from . import dlaExtractLayerToGDB, dlaFieldCalculator, dla


def preview(xmlFileNames, continue_on_error, rowLimit):
    layers = list()
    if xmlFileNames is not list:  # The GPTool UI gives the xmls as a list, but anyone calling the script might use
        xml_file = xmlFileNames  # just a string value. This converts the string to work for the rest of the script
        xmlFileNames = list()

        xmlFileNames.append(xml_file)
    for xmlFileName in xmlFileNames:
        dla.setWorkspace()
        dla._errCount = 0
        arcpy.AddMessage("Data Assistant - Preview")
        xmlFileName = dla.getXmlDocName(xmlFileName)
        xmlDoc = dla.getXmlDoc(xmlFileName)
        # arcpy.AddMessage("rowLimit = " + str(rowLimit) )
        if rowLimit == "" or rowLimit == None:
            rowLimit = 100

        prj = dla.setProject(xmlFileName, dla.getNodeValue(xmlDoc, "Project"))
        # if prj == None:
        # dla.addError("Unable to open your project, please ensure it is in the same folder as your current project or your Config file")
        # return False

        source = dla.getDatasetPath(xmlDoc, "Source")
        target = dla.getDatasetPath(xmlDoc, "Target")

        if dla.isTable(source) or dla.isTable(target):
            datasetType = 'Table'
        else:
            datasetType = 'FeatureClass'
        dte = datetime.datetime.now().strftime("%Y%m%d%H%M")
        targetName = os.path.basename(arcpy.CreateUniqueName(dla.getDatasetName(target) + dte, dla.workspace))
        targetDS = os.path.join(dla.workspace, targetName)
        res = dlaExtractLayerToGDB.extract(xmlFileName, rowLimit, dla.workspace, source, targetDS, datasetType)
        if res == True:
            res = dlaFieldCalculator.calculate(xmlFileName, dla.workspace, targetName, False, False)

            if res == True:
                arcpy.env.addOutputsToMap = True
                layer = targetName
                layertmp = targetName + "tmp"
                if arcpy.Exists(layertmp):
                    arcpy.Delete_management(layertmp)
                if dla.isTable(targetDS):
                    arcpy.MakeTableView_management(targetDS, layertmp)
                else:
                    arcpy.MakeFeatureLayer_management(targetDS, layertmp)
                fieldInfo = dla.getLayerVisibility(layertmp, xmlFileName)
                if dla.isTable(targetDS):
                    arcpy.MakeTableView_management(targetDS, layer, None, dla.workspace, fieldInfo)
                else:
                    arcpy.MakeFeatureLayer_management(targetDS, layer, None, dla.workspace, fieldInfo)
                # should make only the target fields visible
                layers.append(layer)
            else:
                if continue_on_error:
                    continue
                else:
                    return
        else:
            dla.addError("Failed to Extract data")
            print("Failed to Extract data")
            if continue_on_error:
                continue
            else:
                return
        dla.writeFinalMessage("Data Assistant - Preview")
    return layers
