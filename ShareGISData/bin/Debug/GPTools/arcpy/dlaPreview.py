## dlaPreview.py - Preview one source to a target with a limited number of rows

import arcpy,os,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom,datetime

arcpy.AddMessage("Data Assistant - Publish")

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
_success = 2 # the last param is the derived output layer
try:
    rowLimit = arcpy.GetParameterAsText(1) # Row limit for preview
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
    
    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    if rowLimit == "" or rowLimit == None:
        rowLimit = 100
    if sourceLayer == "" or sourceLayer == None:
        sourceLayer = dla.getNodeValue(xmlDoc,"Source")
    if targetLayer == "" or targetLayer == None:
        #targetLayer = dla.getNodeValue(xmlDoc,"Target")
        dte = datetime.datetime.now().strftime("%Y%m%d%H%M")
        targetName = dla.getTargetName(xmlDoc) + dte
        targetLayer = os.path.join(dla.workspace,targetName)
    res = dlaExtractLayerToGDB.extract(xmlFileName,rowLimit,dla.workspace,sourceLayer,targetLayer)
    if res == True:
        res = dlaFieldCalculator.calculate(xmlFileName,dla.workspace,targetName,False)
        if res == True:
            arcpy.env.addOutputsToMap = True
            layer = targetName
            layertmp = targetName + "tmp"
            if arcpy.Exists(layertmp):
                arcpy.Delete_management(layertmp)               
            arcpy.MakeFeatureLayer_management(targetLayer,layertmp)
            fieldInfo = dla.getLayerVisibility(layertmp,xmlFileName)
            arcpy.MakeFeatureLayer_management(targetLayer,layer,None,dla.workspace,fieldInfo)
            # should make only the target fields visible
            arcpy.SetParameter(_success,layer)

        
if __name__ == "__main__":
    main()


#arcpy.SaveToLayerFile_management("TEST", "TEST.lyrx", "RELATIVE")
#addLayerToMap("TEST.lyrx")
      
#try:
#    aprx = arcpy.mp.ArcGISProject("CURRENT")
#except:
#    aprx = None
#if aprx != None:
#    m = aprx.listMaps()[0]
#    dla.addMessage(layer)
#    m.addLayer(layer)
