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
        source = dla.getDatasetPath(xmlDoc,"Source")
    if target == "" or target == None:
        target = dla.getDatasetPath(xmlDoc,"Target")
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
        dla.workspace = dla.setWorkspace()
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
  
    sourceName = dla.getDatasetName(source)
    viewName = sourceName + "_View"
    dla.addMessage(viewName)
    
    targetRef = getSpatialReference(xmlDoc,"Target")
    sourceRef = getSpatialReference(xmlDoc,"Source")
    if datasetType == 'Table':
        isTable = True
    elif targetRef != '':
        isTable = False

    arcpy.env.workspace = workspace
    if source.lower().endswith('.lyrx') and not dla.hasJoin(source):
        view = dla.getLayerFromString(source)
    elif isTable:
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
        currentPreserveGlobalIDs = arcpy.env.preserveGlobalIds
        if dla.processGlobalIds(xmlDoc): # both datasets have globalids in the correct workspace types
            arcpy.env.preserveGlobalIds = True # try to preserve
            dla.addMessage("Attempting to preserve GlobalIDs")
        else:
            arcpy.env.preserveGlobalIds = False # don't try to preserve
            dla.addMessage("Unable to preserve GlobalIDs")
        if isTable:
            arcpy.TableToTable_conversion(in_rows=view,out_path=workspace,out_name=targetName)
        else:
            spRefMatch = dla.compareSpatialRef(xmlDoc)
            currentRef = arcpy.env.outputCoordinateSystem # grab currrent env settings
            currentTrans = arcpy.env.geographicTransformations

            if not spRefMatch:
                arcpy.env.outputCoordinateSystem = targetRef
                transformations = arcpy.ListTransformations(sourceRef, targetRef)
                transformations = ";".join(transformations) # concat the values - format change for setting the values.
                arcpy.env.geographicTransformations = transformations

            arcpy.FeatureClassToFeatureClass_conversion(in_features=view,out_path=workspace,out_name=targetName)

            if not spRefMatch: # set the spatial reference back
                arcpy.env.outputCoordinateSystem = currentRef
                arcpy.env.geographicTransformations = currentTrans
            arcpy.env.preserveGlobalIds = currentPreserveGlobalIDs

        removeDefaultValues(ds) # don't want to turn nulls into defaultValues in the intermediate data

        # not needed if doing the transformations approach above...
        #    if isTable: 
        #        if not createDataset('Table',workspace,targetName,None,xmlDoc,source,None):
        #            arcpy.AddError("Unable to create intermediate table, exiting: " + workspace + os.sep + targetName)
        #            return False

        #    elif not isTable:
        #        geomType = arcpy.Describe(source).shapeType
        #        if not createDataset('FeatureClass',workspace,targetName,geomType,xmlDoc,source,targetRef):
        #            arcpy.AddError("Unable to create intermediate feature class, exiting: " + workspace + os.sep + targetName)
        #            return False
        #    fieldMap = getFieldMap(view,ds)
        #    arcpy.Append_management(view,ds,schema_type="NO_TEST",field_mapping=fieldMap)

        dla.addMessage(arcpy.GetMessages(2)) # only serious errors
        count = arcpy.GetCount_management(ds).getOutput(0)
        dla.addMessage(str(count) + " source rows exported to " + targetName)
        if str(count) == '0':
            result = False
            dla.addError("Failed to load to " + targetName + ", it is likely that your data falls outside of the target Spatial Reference Extent or there is another basic issue")
            dla.addError("To verify please use the Append and/or Copy Features tool to load some data to an intermediate dataset:")
            dla.addError(ds)
            dla.showTraceback()
    return result

def getFieldMap(view,ds):

    fieldMaps = arcpy.FieldMappings()
    fieldMaps.addTable(ds)
    inFields = [field.name for field in arcpy.ListFields(view) if field.name.upper() not in dla._ignoreFields] # not field.required removed after .Enabled issue 
    removenames = []
    for i in range(fieldMaps.fieldCount):
        field = fieldMaps.fields[i]
        fmap = fieldMaps.getFieldMap(i)
        fName = field.name
        for s in range(0,fmap.inputFieldCount):
            try:
                fmap.removeInputField(0)
            except:
                pass
        try:
            f = -1
            try:
                f = inFields.index(fName) # simple case where names are equal
            except:
                f = inFields.index(fName.replace('_','.',1)) # just replace the first char - more complex case like xfmr.phase_designation
            if f > -1:
                inField = inFields[f]
                fmap.addInputField(view,inField)
                fieldMaps.replaceFieldMap(i,fmap)
        except:
            removenames.append(fName)

    for name in removenames:
        i = fieldMaps.findFieldMapIndex(name)
        fieldMaps.removeFieldMap(i)
        dla.addMessage(name + ' removed from fieldMappings')
        
    return fieldMaps

#def printFieldMap(fieldMap):

#    for i in range(fieldMap.fieldCount):
#        fmap = fieldMap.getFieldMap(i)
#        dla.addMesage(str(fmap.getInputFieldName(0)) + ': ' + str(fmap.outputField.name))

#    return


def createDataset(dsType,workspace,targetName,geomType,xmlDoc,source,targetRef):

    if source.lower().endswith('.lyrx') and dla.hasJoin(source):
        if dsType == 'Table':
            arcpy.CreateTable_management(workspace,targetName)
        else:
            arcpy.CreateFeatureclass_management(workspace,targetName,geometry_type=geomType,spatial_reference=targetRef)

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
    #dla.addMessage(table + ' - ' + oidname)
    searchCursor = arcpy.da.SearchCursor(table,[oidname])
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

def removeDefaultValues(dataset):
    # exported source fields may contain DefaultValues, which can replace None/null values in field calculations
    sourceFields = arcpy.ListFields(dataset) # xmlDoc.getElementsByTagName("SourceField")
    #stypes = arcpy.da.ListSubtypes(dataset) # my current understanding is that the intermediate/exported dataset will not have subtypes, just default/0 subtype if present in source dataset.

    dla.addMessage("Removing Default Value property from intermediate database fields")
    for sfield in sourceFields:
        fname = sfield.name
        if fname != dla._noneFieldName and sfield.defaultValue != None:
            try:
                arcpy.AssignDefaultToField_management(in_table=dataset,field_name=fname,default_value=None,clear_value=True) # clear the Defaults
            except:
                dla.addMessage("Unable to set DefaultValue for " + fname) # skip GlobalIDs/other fields that cannot be updated. Should not have a default set in these cases 

if __name__ == "__main__":
    main()
