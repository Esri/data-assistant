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

arcpy.AddMessage("Data Assistant - Stage")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter
_derived = 1 # the last param is the derived output layer
source = None
target = None
rowLimit = None

def main(argv = None):
    stage(xmlFileNames)

def stage(xmlFileNames):
    global source,target,rowLimit

    dla.setWorkspace()
    dla._errCount = 0
    outlayers = []

    for xmlFileName in xmlFileNames.split(';'):
        xmlFileName = dla.getXmlDocName(xmlFileName)
        xmlDoc = dla.getXmlDoc(xmlFileName)
        if rowLimit == "" or rowLimit == None:
            rowLimit = None
        if source == "" or source == None:
            source = dla.getNodeValue(xmlDoc,"Source")
        if target == "" or target == None:
            target = dla.getNodeValue(xmlDoc,"Target")

        if dla.isTable(source) or dla.isTable(target):
            datasetType = 'Table'
        else:
            datasetType = 'FeatureClass'

        #dte = datetime.datetime.now().strftime("%Y%m%d%H%M")
        targetName = dla.getStagingName(source,target)
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
                outlayers.append(layer)
                ''' *** need to insert tag in xml file...'''
                dla.insertStagingElement(xmlDoc)

                xmlDoc.writexml(open(xmlFileName, 'wt', encoding='utf-8'))

                dla.addMessage('Staging element written to config file')
                xmlDoc.unlink()
        else:
            dla.addError("Failed to Extract data")
            print("Failed to Extract data")
    if outlayers != []:
        arcpy.SetParameter(_derived,";".join(outlayers))
    dla.writeFinalMessage("Data Assistant - Stage")

if __name__ == "__main__":
    main()


def setSourceTarget(root,xmlDoc,name,dataset):
    # set source and target elements
    sourcetarget = xmlDoc.createElement(name)
    nodeText = xmlDoc.createTextNode(dataset)
    sourcetarget.appendChild(nodeText)
    root.appendChild(sourcetarget)