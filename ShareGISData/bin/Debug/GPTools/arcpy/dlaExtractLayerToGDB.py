# ---------------------------------------------------------------------------
# dlaExtractLayerToGDB.py
# Description: Import a .lyr file or feature layer to Geodatabase.
# ---------------------------------------------------------------------------

import os, sys, traceback, time, arcpy, dla

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

    xmlDoc = dla.getXmlDoc(xmlFileName)
    if dla.workspace == "" or dla.workspace == "#" or dla.workspace == None:  
        dla.workspace = arcpy.env.scratchGDB
    if sourceLayer == "" or sourceLayer == None:
        sourceLayer = dla.getNodeValue(xmlDoc,"Source")
    if targetLayer == "" or targetLayer == None:
        targetLayer = dla.getNodeValue(xmlDoc,"Target")
    if success == False:
        dla.addError("Errors occurred during process")

    success = extract(xmlFileName,rowLimit,dla.workspace,sourceLayer,targetLayer)
    arcpy.SetParameter(SUCCESS, success)

def extract(xmlFileName,rowLimit,workspace,sourceLayer,targetFC):          

    xmlDoc = dla.getXmlDoc(xmlFileName)
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
            if targetFC == '' or targetFC == '#':
                targetName = dla.getTargetName(xmlDoc)
            else:
                targetName = targetFC[targetFC.rfind(os.sep)+1:]

            sourceName = dla.getSourceName(xmlDoc)
            arcpy.SetProgressorLabel("Loading " + sourceName + " to " + targetName +"...")
            #if not arcpy.Exists(sourceLayer):
            #    dla.addError("Layer " + sourceLayer + " does not exist, exiting")
            #    return
            
            target = dla.getTempTable(targetName)
            if arcpy.Exists(target):
                arcpy.Delete_management(target)

            retVal = exportDataset(xmlDoc,sourceLayer,dla.workspace,targetName,rowLimit)
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
    
def exportDataset(xmlDoc,sourceLayer,workspace,targetName,rowLimit):
    result = True
    xmlFields = xmlDoc.getElementsByTagName("Field")
    dla.addMessage("Exporting Layer from " + sourceLayer)
    whereClause = ""
    try:
        if rowLimit != None:
            try:
                whereClause = getObjectIdWhereClause(sourceLayer,rowLimit)
            except:
                dla.addMessage("Unable to obtain where clause to Preview " + sourceLayer + ", continuing with all records")
                
        if whereClause != '' and whereClause != ' ':
            dla.addMessage("Where " + str(whereClause))
        sourceName = dla.getSourceName(xmlDoc)
        viewName = sourceName + "_View"
        dla.addMessage(viewName)
        
        #try:
        targetRef = getSpatialReference(xmlDoc,"Target")
        #sourceRef = getSpatialReference(xmlDoc,"Source")
        
        if targetRef != '':
            if arcpy.Exists(targetName):
                arcpy.Delete_management(targetName)
                
            arcpy.env.workspace = workspace
            view = dla.makeFeatureViewForLayer(dla.workspace,sourceLayer,viewName,whereClause,xmlFields)
            dla.addMessage("View Created")            
            count = arcpy.GetCount_management(view).getOutput(0)
            dla.addMessage(str(count) + " source rows")
            
            arcpy.CreateFeatureclass_management(workspace,targetName,template=sourceLayer,spatial_reference=targetRef)
            arcpy.Append_management(inputs=view,target=targetName,schema_type="NO_TEST")
            dla.addMessage(arcpy.GetMessages(2)) # only serious errors
            count = arcpy.GetCount_management(targetName).getOutput(0)
            dla.addMessage(str(count) + " source rows exported to " + targetName)
            if str(count) == '0':
                result = False
                dla.addError("Failed to load to " + targetName + ", it is likely that your data falls outside of the target Spatial Reference Extent")
                dla.addMessage("To verify please use the Append tool to load some data to the target dataset")
    except:
        err = "Failed to create new dataset " + targetName
        dla.showTraceback()
        dla.addError(err)
        result = False
    return result

def getSpatialReference(xmlDoc,lyrtype):
    spref = ''
    # try factoryCode first
    sprefstr = dla.getNodeValue(xmlDoc,lyrtype + "FactoryCode")
    if sprefstr != '':
        #arcpy.AddMessage(lyrtype + ":" + sprefstr)
        spref = arcpy.SpatialReference(sprefstr)
    else:    
        sprefstr = dla.getNodeValue(xmlDoc,lyrtype + "SpatialReference")
        if sprefstr != '':
            arcpy.AddMessage(lyrtype + ":" + sprefstr)
            spref = arcpy.SpatialReference()
            spref.loadFromString(sprefstr)

    if spref == '' and spref != None:
        arcpy.AddError("Unable to retrieve Spatial Reference for " + lyrtype + " layer")

    return spref

def getObjectIdWhereClause(table,rowLimit):
    # build a where clause, assume that oids are sequential or at least in row order...
    oidname = arcpy.Describe(table).oidFieldName
    searchCursor = arcpy.da.SearchCursor(table,["OID@"])
    i = 0
    ids = []
    # use the oidname in the where clause
    where = oidname + " <= " + str(rowLimit)
    for row in searchCursor:
        if i < rowLimit:
            ids.append(row[0])
        elif i == rowLimit:
            break
        i += 1

    if i > 0:
        minoid = min(ids)
        maxoid = max(ids)
        where = oidname + " >= " + str(minoid) + " AND " + oidname + " <= " + str(maxoid)
    del searchCursor
    return where

def theProjectWay():
    """
    This function is currently not used. It is an alternative to the create feature class/append approach
    currently being used. It is slower because the entire dataset is projected first, and it is less
    straightforward because it adds the transform method that append seems to know how to handle already.
    It is better though because it will actually raise trappable errors while Append fails silently...
    The solution in the other function is to count the resulting records and report issues.
    """
    if targetRef != '':
        if arcpy.Exists(targetName):
            arcpy.Delete_management(targetName)
        inttable = workspace+os.sep+targetName+"_prj"
        arcpy.env.workspace = workspace
        xform = None
        desc = arcpy.Describe(sourceLayer)
        xforms = arcpy.ListTransformations(desc.spatialReference, targetRef, desc.extent)            
        #if sourceRef.exportToString().find("NAD_1983") > -1 and targetRef.exportToString().find("WGS_1984") > -1:
        xform = xforms[0]
        #for xform in xforms:
        dla.addMessage("Transform: " + xform)
        try:
            res = arcpy.Project_management(sourceLayer,inttable,out_coor_system=targetRef,transform_method=xform)
        except:
            dla.showTraceback()
            err = "Unable to project the data to the target spatial reference, please check settings and try projecting manually in ArcGIS"
            dla.addError(err)
            return False
        dla.addMessage("Features projected")            
        view = dla.makeFeatureViewForLayer(dla.workspace,inttable,viewName,whereClause,xmlFields)
        dla.addMessage("View Created")            
        #except:
        #    arcpy.AddError("Unabled to create feature View " + viewName)
        count = arcpy.GetCount_management(view).getOutput(0)
        dla.addMessage(str(count) + " source rows")
        #sourceRef = getSpatialReference(xmlDoc,"Source")
        #res = arcpy.CreateFeatureclass_management(workspace,targetName,template=sourceLayer,spatial_reference=targetRef)
        res = arcpy.CopyFeatures_management(view,targetName)
        dla.addMessage("Features copied")     

if __name__ == "__main__":
    main()
