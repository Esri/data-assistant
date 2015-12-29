# ---------------------------------------------------------------------------
# dlaExtractLayerToGDB.py
# Description: Import a .lyr file or feature layer to Geodatabase.
# ---------------------------------------------------------------------------

import os, sys, traceback, time, arcpy, xml.dom.minidom, dla

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
try:
    sourceLayer = arcpy.GetParameterAsText(1) # Source Layer File to load from
except:
    sourceLayer = None
try:
    dla.workspace = arcpy.GetParameterAsText(2) # Geodatabase
except:
    dla.workspace = arcpy.env.scratchGDB
try:    
    rowLimit = arcpy.GetParameterAsText(3) # Number of records to extract
except:
    rowLimit = None
SUCCESS = 4 # parameter number for output success value

def main(argv = None):
    global sourceLayer,targetLayer

    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    if dla.workspace == "" or dla.workspace == "#" or dla.workspace == None:  
        dla.workspace = arcpy.env.scratchGDB
    if sourceLayer == "" or sourceLayer == None:
        sourceLayer = dla.getNodeValue(xmlDoc,"Datasets/Source")
    if targetLayer == "" or targetLayer == None:
        targetLayer = dla.getNodeValue(xmlDoc,"Datasets/Target")
    if success == False:
        dla.addError("Errors occurred during process")

    success = extract(xmlFileName,rowLimit,dla.workspace,sourceLayer,targetLayer)
    arcpy.SetParameter(SUCCESS, success)

def extract(xmlFileName,rowLimit,workspace,sourceLayer,targetLayer):          

    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    if workspace == "" or workspace == "#" or workspace == None:  
        dla.workspace = arcpy.env.scratchGDB
    else:
        dla.workspace = workspace
    fields = dla.getFields(xmlFileName)
    success = True
    name = ''
    try:
        if not arcpy.Exists(dla.workspace):
            dla.addMessage(dla.workspace + " does not exist, attempting to create")
            dla.createGeodatabase()
        if len(fields) > 0:
            arcpy.SetProgressor("step", "Importing Layer...",0,1,1)

            if sourceLayer == '' or sourceLayer == '#':                
                source = dla.getNodeValue(xmlDoc,"Datasets/Source")
            else:
                source = sourceLayer
            if targetLayer == '' or targetLayer == '#':
                target = dla.getNodeValue(xmlDoc,"Datasets/Target")
            else:
                target = targetLayer
            sourceName = source[source.rfind(os.sep)+1:]
            targetName = target[target.rfind(os.sep)+1:]
            arcpy.SetProgressorLabel("Loading " + sourceName + " to " + targetName +"...")
            if not arcpy.Exists(sourceLayer):
                dla.addError("Layer " + sourceLayer + " does not exist, exiting")
                return
            
            target = dla.getTempTable(targetName)
            if arcpy.Exists(target):
                arcpy.Delete_management(target)

            xmlFields = xmlDoc.getElementsByTagName("Field")
            retVal = exportDataset(sourceLayer,target,xmlFields,rowLimit)
            if retVal == False:
                success = False

        arcpy.SetProgressorPosition()
    except:
        dla.addError("A Fatal Error occurred")
        dla.showTraceback()
        success = False
    finally:
        arcpy.ResetProgressor()
        #arcpy.RefreshCatalog(dla.workspace)
        arcpy.ClearWorkspaceCache_management(dla.workspace)

    return success
    
def exportDataset(sourceLayer,target,xmlFields,rowLimit):
    result = True
    dla.addMessage("Exporting Layer from " + sourceLayer)
    whereClause = ""
    try:
        if rowLimit != None:
            whereClause = getObjectIdWhereClause(sourceLayer,rowLimit)
        dla.addMessage("Where " + str(whereClause))
        sourceName = sourceLayer[sourceLayer.rfind(os.sep)+1:sourceLayer.lower().rfind(".lyr")]
        viewName = sourceName + "_View"
        dla.addMessage(viewName)
        
        view = dla.makeFeatureViewForLayer(dla.workspace,sourceLayer,viewName,whereClause,xmlFields)
        count = arcpy.GetCount_management(view).getOutput(0)
        dla.addMessage(str(count) + " source rows exported to " + target)
        arcpy.FeatureClassToFeatureClass_conversion(view,dla.workspace,target[target.rfind(os.sep)+1:])
    except:
        err = "Failed to create new dataset " + target
        dla.showTraceback()
        dla.addError(err)
        result = False
    return result

def getObjectIdWhereClause(table,rowLimit):
    # build a where clause, assume that oids are sequential or at least in row order...
    searchCursor = arcpy.da.SearchCursor(table,["OID@"])
    i = 0
    ids = []
    where = "OBJECTID <= " + str(rowLimit)
    for row in searchCursor:
        ids.append(row[0])
        if i == rowLimit:
            minoid = ids[0]
            maxoid = ids[i-1]
            where = "OBJECTID >= " + str(minoid) + " AND OBJECTID <= " + str(maxoid)
            del searchCursor            
            return where
        i += 1

    del searchCursor
    return where


if __name__ == "__main__":
    main()
