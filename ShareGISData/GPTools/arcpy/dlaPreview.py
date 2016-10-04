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
_success = 2 # the last param is the derived output layer
try:
    rowLimit = arcpy.GetParameterAsText(1) # Row limit for preview
    rowLimit = int(rowLimit)
    if rowLimit == "" or rowLimit == "#":
        rowLimit = None
except:
    rowLimit = None
    
try:
    sourceLayer = arcpy.GetParameterAsText(2) # Source Layer File to load from
    if sourceLayer == "" or sourceLayer == "#":
        sourceLayer = None
except:
    sourceLayer = None

try:
    targetLayer = arcpy.GetParameterAsText(3) # Target Layer File to load to
    if targetLayer == "" or targetLayer == "#":
        targetLayer = None
except:
    targetLayer = None
    
def main(argv = None):
    preview(xmlFileName)

def preview(xmlFileName):
    global sourceLayer,targetLayer,rowLimit

    dla.setWorkspace()
    dla._errCount = 0

    xmlDoc = dla.getXmlDoc(xmlFileName)
    arcpy.AddMessage("rowLimit = " + str(rowLimit) )
    if rowLimit == "" or rowLimit == None:
        rowLimit = 100
    if sourceLayer == "" or sourceLayer == None:
        sourceLayer = dla.getNodeValue(xmlDoc,"Source")
    if targetLayer == "" or targetLayer == None:
        targetLayer = dla.getNodeValue(xmlDoc,"Target")
        dte = datetime.datetime.now().strftime("%Y%m%d%H%M")
        targetName = dla.getTargetName(xmlDoc) + dte
        targetFC = os.path.join(dla.workspace,targetName)
    res = dlaExtractLayerToGDB.extract(xmlFileName,rowLimit,dla.workspace,sourceLayer,targetFC)
    if res == True:
        res = dlaFieldCalculator.calculate(xmlFileName,dla.workspace,targetName,False)
        if res == True:
            arcpy.env.addOutputsToMap = True
            layer = targetName
            layertmp = targetName + "tmp"
            if arcpy.Exists(layertmp):
                arcpy.Delete_management(layertmp)               
            arcpy.MakeFeatureLayer_management(targetFC,layertmp)
            fieldInfo = dla.getLayerVisibility(layertmp,xmlFileName)
            arcpy.MakeFeatureLayer_management(targetFC,layer,None,dla.workspace,fieldInfo)
            # should make only the target fields visible
            arcpy.SetParameter(_success,layer)
    else:
        dla.addError("Failed to Extract data")
        print("Failed to Extract data")
    dla.writeFinalMessage("Data Assistant - Preview")

if __name__ == "__main__":
    main()
