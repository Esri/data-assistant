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
import arcpy, os, dlaExtractLayerToGDB,dlaFieldCalculator,dla,datetime

arcpy.AddMessage("Data Assistant - Preview")

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
try:
    rowLimit = arcpy.GetParameterAsText(1) # Row limit for preview
    rowLimit = int(rowLimit)
    if rowLimit == "" or rowLimit == "#":
        rowLimit = None
except:
    rowLimit = None
_success = 2 # the last param is the derived output layer
source = None
target = None
        
def main(argv = None):
    preview(xmlFileName)

def preview(xmlFileName):
    global source,target,rowLimit

    dla.setWorkspace()
    dla._errCount = 0

    xmlFileName = dla.getXmlDocName(xmlFileName)
    xmlDoc = dla.getXmlDoc(xmlFileName)
    #arcpy.AddMessage("rowLimit = " + str(rowLimit) )
    if rowLimit == "" or rowLimit == None:
        rowLimit = 100

    prj = dla.setProject(xmlFileName,dla.getNodeValue(xmlDoc,"Project"))
    if prj == None:
        dla.addError("Unable to open your project, please ensure it is in the same folder as your current project or your Config file")
        return False

    if source == "" or source == None:
        source = dla.getDatasetPath(xmlDoc,"Source")
    if target == "" or target == None:
        target = dla.getDatasetPath(xmlDoc,"Target")

    if dla.isTable(source) or dla.isTable(target):
        datasetType = 'Table'
    else:
        datasetType = 'FeatureClass'
    dte = datetime.datetime.now().strftime("%Y%m%d%H%M")
    targetName = dla.getDatasetName(target) + dte
    targetDS = os.path.join(dla.workspace,targetName)
    res = dlaExtractLayerToGDB.extract(xmlFileName,rowLimit,dla.workspace,source,targetDS,datasetType)
    if res == True:
        res = dlaFieldCalculator.calculate(xmlFileName,dla.workspace,targetName,False)

        if res == True:
            arcpy.env.addOutputsToMap = True
            layer = targetName
            layertmp = targetName + "tmp"
            if arcpy.Exists(layertmp):
                arcpy.Delete_management(layertmp)
            if dla.isTable(targetDS):
                arcpy.MakeTableView_management(targetDS,layertmp)
            else:
                arcpy.MakeFeatureLayer_management(targetDS,layertmp)
            fieldInfo = dla.getLayerVisibility(layertmp,xmlFileName)
            if dla.isTable(targetDS):
               arcpy.MakeTableView_management(targetDS,layer,None,dla.workspace,fieldInfo)
            else:
               arcpy.MakeFeatureLayer_management(targetDS,layer,None,dla.workspace,fieldInfo)
            # should make only the target fields visible
            arcpy.SetParameter(_success,layer)
    else:
        dla.addError("Failed to Extract data")
        print("Failed to Extract data")
    dla.writeFinalMessage("Data Assistant - Preview")

if __name__ == "__main__":
    main()
