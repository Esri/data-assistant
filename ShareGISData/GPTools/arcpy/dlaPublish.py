## dlaPublish.py - Publish one source to a target

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom

arcpy.AddMessage("Data Assistant - Publish")

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter

_success = 1 # the last param is the derived output layer

try:
    sourceLayer = arcpy.GetParameterAsText(1) # Source Layer File to load from
    if sourceLayer == "" or sourceLayer == "#":
        sourceLayer = None
except:
    sourceLayer = None

try:
    targetLayer = arcpy.GetParameterAsText(2) # Target Layer File to load to
    if targetLayer == "" or targetLayer == "#":
        targetLayer = None
except:
    targetLayer = None
    
def main(argv = None):
    publish(xmlFileName)

def publish(xmlFileName):
    
    global sourceLayer,targetLayer,_success

    for xmlfile in xmlFileName.split(";"): # multi value parameter
        xmlDoc = xml.dom.minidom.parse(xmlfile)
        if sourceLayer == "" or sourceLayer == None:
            sourceLayer = dla.getNodeValue(xmlDoc,"Source")
        if targetLayer == "" or targetLayer == None:
            targetLayer = dla.getNodeValue(xmlDoc,"Target")
        dla.setWorkspace()
        res = dlaExtractLayerToGDB.extract(xmlfile,None,dla.workspace,sourceLayer,targetLayer)
        targetName = dla.getTargetName(xmlDoc)
        if res == True:
            res = dlaFieldCalculator.calculate(xmlfile,dla.workspace,targetName,False)
            if res == True:
                arcpy.env.addOutputsToMap = True
                src = dla.getTempTable(targetName)
                dla.doInlineAppend(src,targetLayer)
                layer = targetName
                layertmp = targetName + "tmp"
                if arcpy.Exists(layertmp):
                    arcpy.Delete_management(layertmp)               
                arcpy.MakeFeatureLayer_management(targetLayer,layertmp)
                fieldInfo = dla.getLayerVisibility(layertmp,xmlfile)
                arcpy.MakeFeatureLayer_management(targetLayer,layer,None,dla.workspace,fieldInfo)
                # should make only the target fields visible
                arcpy.AddMessage("Success param="+str(_success))
                arcpy.AddMessage("param count="+str(arcpy.GetArgumentCount()))
                arcpy.SetParameter(_success,layer)

                  
if __name__ == "__main__":
    main()


