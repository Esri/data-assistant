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
# ---------------------------------------------------------------------------
# dlaExtractLayerToGDB.py
# Description: Import a .lyr file or feature layer to Geodatabase.
# ---------------------------------------------------------------------------

import os, sys, traceback, time, arcpy, dla

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
try:
    source = arcpy.GetParameterAsText(1) # Source Layer File to load from
except:
    source = None
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
    global source,target

    xmlDoc = dla.getXmlDoc(xmlFileName)
    if dla.workspace == "" or dla.workspace == "#" or dla.workspace == None:  
        dla.workspace = arcpy.env.scratchGDB
    if source == "" or source == None:
        source = dla.getNodeValue(xmlDoc,"Source")
    if target == "" or target == None:
        target = dla.getNodeValue(xmlDoc,"Target")
    if success == False:
        dla.addError("Errors occurred during process")
    if dla.isTable(source) or dla.isTable(target):
        datasetType = 'Table'
    else:
        datasetType = 'FeatureClass'

    success = extract(xmlFileName,rowLimit,dla.workspace,source,target,datasetType)
    arcpy.SetParameter(SUCCESS, success)

def extract(xmlFileName,rowLimit,workspace,source,target,datasetType):          

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

            if source == '' or source == '#':                
                source = dla.getNodeValue(xmlDoc,"Datasets/Source")
            else:
                source = source
            if target == '' or target == '#':
                target = dla.getNodeValue(xmlDoc,"Datasets/Target")

            targetName = dla.getDatasetName(target)
            sourceName = dla.getDatasetName(source)
            arcpy.SetProgressorLabel("Loading " + sourceName + " to " + targetName +"...")

            if not arcpy.Exists(source):
                dla.addError("Layer " + source + " does not exist, exiting")
                return

            retVal = exportDataset(xmlDoc,source,dla.workspace,targetName,rowLimit,datasetType)
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
    
def exportDataset(xmlDoc,source,workspace,targetName,rowLimit,datasetType):
    result = True
    xmlFields = xmlDoc.getElementsByTagName("Field")
    dla.addMessage("Exporting Data from " + source)
    whereClause = ""
    if rowLimit != None:
        whereClause = getObjectIdWhereClause(source,rowLimit)
            
    if whereClause != '' and whereClause != ' ':
        dla.addMessage("Where " + str(whereClause))
    sourceName = dla.getSourceName(xmlDoc)
    viewName = sourceName + "_View"
    dla.addMessage(viewName)
    
    targetRef = getSpatialReference(xmlDoc,"Target")
    if datasetType == 'Table':
        isTable = True
    elif targetRef != '':
        isTable = False

    arcpy.env.workspace = workspace
    if isTable:
        view = dla.makeTableView(dla.workspace,source,viewName,whereClause,xmlFields)
    elif not isTable:
        view = dla.makeFeatureView(dla.workspace,source,viewName,whereClause,xmlFields)

    dla.addMessage("View Created")            
    srcCount = arcpy.GetCount_management(view).getOutput(0)
    dla.addMessage(str(srcCount) + " source rows")
    if str(srcCount) == '0':
        result = False
        dla.addError("Failed to extract " + sourceName + ", Nothing to export")
    else:
        arcpy.env.overwriteOutput = True
        ds = workspace + os.sep + targetName

        if dla.processGlobalIds(xmlDoc): # both datasets have globalids and the spatial references match
            arcpy.env.preserveGlobalIds = True # try to preserve
            addMessage("Proceeding to copy rows and attempt to preserve GlobalIDs")
            if isTable:
                arcpy.TableToTable_conversion(in_rows=view,out_path=workspace,out_name=targetName)
            else:
                arcpy.FeatureClassToFeatureClass_conversion(in_features=view,out_path=workspace,out_name=targetName)
        else:
            arcpy.env.preserveGlobalIds = False # try to preserve
            if isTable:
                if not createDataset('Table',workspace,targetName,xmlDoc,source,None):
                    arcpy.AddError("Unable to create intermediate table, exiting: " + workspace + os.sep + targetName)
                    return False

            elif not isTable:
                if not createDataset('FeatureClass',workspace,targetName,xmlDoc,source,targetRef):
                    arcpy.AddError("Unable to create intermediate feature class, exiting: " + workspace + os.sep + targetName)
                    return False
            fieldMap = getFieldMap(view,ds)
            arcpy.Append_management(view,ds,schema_type="NO_TEST",field_mapping=fieldMap)

        dla.addMessage(arcpy.GetMessages(2)) # only serious errors
        count = arcpy.GetCount_management(ds).getOutput(0)
        dla.addMessage(str(count) + " source rows exported to " + targetName)
        if str(count) == '0':
            result = False
            dla.addError("Failed to load to " + targetName + ", it is likely that your data falls outside of the target Spatial Reference Extent")
            dla.addMessage("To verify please use the Append tool to load some data to the target dataset")
    return result

def getFieldMap(view,ds):

    fieldMap = arcpy.FieldMappings()
    fieldMap.addTable(ds)
    inFields = [field.name for field in arcpy.ListFields(view) if not field.required]
    for inField in inFields:
        for i in range(fieldMap.fieldCount):
            fmap = fieldMap.getFieldMap(i)
            if fmap.getInputFieldName(0) == inField.replace('.','_'):
                fmap.addInputField(view,inField)
                fieldMap.replaceFieldMap(i,fmap)
    return fieldMap

def createDataset(dsType,workspace,targetName,xmlDoc,source,targetRef):

    if source.lower().endswith('.lyrx'):
        if dsType == 'Table':
            arcpy.CreateTable_management(workspace,targetName)
        else:
            arcpy.CreateFeatureclass_management(workspace,targetName,spatial_reference=targetRef)

        sourceFields = xmlDoc.getElementsByTagName("SourceField")
        for sfield in sourceFields:
            # <SourceField AliasName="FIPS_CNTRY" Length="2" Name="SampleData.FIPS_CNTRY" Type="String" />
            fname = sfield.getAttributeNode('Name').nodeValue
            if fname.count('.') > 0:
                fname = fname.replace('.','_')
                ftype = sfield.getAttributeNode('Type').nodeValue
                flength = sfield.getAttributeNode('Length').nodeValue
                dla.addDlaField(os.path.join(workspace,targetName),fname,sfield,[],ftype,flength) # attrs is empty list
    else:
        if dsType == 'Table':
            try:
                arcpy.CreateTable_management(workspace,targetName,template=source)
            except:
                dla.addError("Unable to Create intermediate table")
                return False
        else:
            try:
                arcpy.CreateFeatureclass_management(workspace,targetName,template=source,spatial_reference=targetRef)
            except:
                dla.addError("Unable to Create intermediate feature class")
                return False

    return True

def getSpatialReference(xmlDoc,lyrtype):
    spref = None
    # try factoryCode first
    sprefstr = dla.getNodeValue(xmlDoc,lyrtype + "FactoryCode")
    if sprefstr != '':
        #arcpy.AddMessage(lyrtype + ":" + sprefstr)
        spref = arcpy.SpatialReference(int(sprefstr))
    else:    
        sprefstr = dla.getNodeValue(xmlDoc,lyrtype + "SpatialReference")
        if sprefstr != '':
            #arcpy.AddMessage(lyrtype + ":" + sprefstr)
            spref = arcpy.SpatialReference()
            spref.loadFromString(sprefstr)

    if spref == '' and spref != None:
        arcpy.AddError("Unable to retrieve Spatial Reference for " + lyrtype + " layer")

    return spref

def getObjectIdWhereClause(table,rowLimit):
    # build a where clause, assume that oids are sequential or at least in row order...
    oidname = arcpy.Describe(table).oidFieldName
    searchCursor = arcpy.da.SearchCursor(table,["OID@"])
    #i = 0
    ids = []
    # use the oidname in the where clause
    where = oidname + " <= " + str(rowLimit)
    
    for row in searchCursor:
        ids.append(row[0]) # sql server db does not always return OBJECTIDs sorted, no shortcut

    if len(ids) > 0:
        ids.sort() # sort the list and take the rowLimit number of rows
        minoid = ids[0]
        if len(ids) > rowLimit:
            maxoid = ids[rowLimit-1]
        else:
            maxoid = ids[len(ids)-1]

        where = oidname + " >= " + str(minoid) + " AND " + oidname + " <= " + str(maxoid)

    del ids
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
        desc = arcpy.Describe(source)
        xforms = arcpy.ListTransformations(desc.spatialReference, targetRef, desc.extent)            
        #if sourceRef.exportToString().find("NAD_1983") > -1 and targetRef.exportToString().find("WGS_1984") > -1:
        xform = xforms[0]
        #for xform in xforms:
        dla.addMessage("Transform: " + xform)
        try:
            res = arcpy.Project_management(source,inttable,out_coor_system=targetRef,transform_method=xform)
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
        #res = arcpy.CreateFeatureclass_management(workspace,targetName,template=source,spatial_reference=targetRef)
        res = arcpy.CopyFeatures_management(view,targetName)
        dla.addMessage("Features copied")     

if __name__ == "__main__":
    main()
