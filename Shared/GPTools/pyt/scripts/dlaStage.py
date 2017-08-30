import os
import DATools
import validate
import arcpy

from . import dla, dlaExtractLayerToGDB, dlaFieldCalculator

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


# dlaPreview.py - Preview one source to a target with a limited number of rows
# ------------------------------------------------------------------------------------

def stage(xmlFileNames, continue_on_error):
    arcpy.AddMessage("Data Assistant - Stage")

    dla.setWorkspace()
    dla._errCount = 0
    outlayers = list()
    if type(xmlFileNames) is not list:
        xml_file = xmlFileNames
        xmlFileNames = list()
        xmlFileNames.append(xml_file)

    for xmlFileName in xmlFileNames:
        try:
            validator = validate.Validator.from_xml(xmlFileName)
            validator.validate()
        except:
            arcpy.AddMessage("Validation unable to be completed")
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

        xmlFileName = dla.getXmlDocName(xmlFileName)
        xmlDoc = dla.getXmlDoc(xmlFileName)
        prj = dla.setProject(xmlFileName, dla.getNodeValue(xmlDoc, "Project"))
        if prj is None:
            dla.addError(
                "Unable to open your project, please ensure it is in the same folder as your current project or your Config file")

        source = dla.getDatasetPath(xmlDoc, "Source")
        target = dla.getDatasetPath(xmlDoc, "Target")

        if dla.isTable(source) or dla.isTable(target):
            datasetType = 'Table'
        else:
            datasetType = 'FeatureClass'

        targetName = dla.getStagingName(source, target)
        targetDS = os.path.join(dla.workspace, targetName)

        res = dlaExtractLayerToGDB.extract(xmlFileName, None, dla.workspace, source, targetDS, datasetType)
        if res == True:
            res = dlaFieldCalculator.calculate(xmlFileName, dla.workspace, targetName, False)

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
                outlayers.append(layer)
                ### *** need to insert tag in xml file...
                dla.insertStagingElement(xmlDoc)
                try:
                    xmlDoc.writexml(open(xmlFileName, 'wt', encoding='utf-8'))
                    dla.addMessage('Staging element written to config file')
                except:
                    dla.addMessage("Unable to write data to xml file")
                xmlDoc.unlink()
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
    if outlayers != []:
        return outlayers
    dla.writeFinalMessage("Data Assistant - Stage")
