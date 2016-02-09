# dlaPublish.py - Publish one source to a target
# ----------------------------------------------------------------------------------------------------------------------

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom,os
import json, urllib
import urllib.parse as parse
import urllib.request as request

arcpy.AddMessage("Data Assistant - Publish")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;
#useReplaceSettings = arcpy.GetParameterAsText(1) # indicates whether to replace by field value or just truncate/append
_success = 1 # the last param is the derived output layer

#if useReplaceSettings.lower() == 'true':
#    useReplaceSettings = True
#else:
useReplaceSettings = False # change this from a calling script to make this script replace data.
    
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

_chunkSize = 100

def main(argv = None):
    # this approach makes it easier to call publish from other python scripts with using GP tool method
    publish(xmlFileNames)

def publish(xmlFileNames):
    
    global sourceLayer,targetLayer,_success

    arcpy.SetProgressor("default","Publishing")
    arcpy.SetProgressorLabel("Publishing")
    xmlFiles = xmlFileNames.split(";")
    for xmlFile in xmlFiles: # multi value parameter, loop for each file
        arcpy.AddMessage("Configuration file: " + xmlFile)
        xmlDoc = dla.getXmlDoc(xmlFile) # parse the xml document
        if xmlDoc == None:
            return
        svceS = False
        svceT = False
        if sourceLayer == "" or sourceLayer == None:
            sourceLayer = dla.getNodeValue(xmlDoc,"Source")
            svceS = checkLayerIsService(sourceLayer)
        if targetLayer == "" or targetLayer == None:
            targetLayer = dla.getNodeValue(xmlDoc,"Target")
            svceT = checkLayerIsService(targetLayer)

        if svceS == True or svceT == True:
            token = dla.getSigninToken() # when signed in get the token and use this. Will be requested many times during the publish
            if token == None:
                arcpy.AddError("User must be signed in for this tool to work with services")
                return

        dla.setWorkspace()
        targetName = dla.getTargetName(xmlDoc)
        res = dlaExtractLayerToGDB.extract(xmlFile,None,dla.workspace,sourceLayer,targetName)
        if res != True:
            table = dla.getTempTable(targetName)
            msg = "Unable to export data, there is a lock on existing datasets or another unknown error"
            if arcpy.TestSchemaLock(table) != True:
                msg = "Unable to export data, there is a lock on the intermediate feature class: " + table
            arcpy.AddError(msg)
            print(msg)
            return
        else:
            res = dlaFieldCalculator.calculate(xmlFile,dla.workspace,targetName,False)
            if res == True:
                #arcpy.env.addOutputsToMap = True
                dlaTable = dla.getTempTable(targetName)
                res = doPublish(xmlDoc,dlaTable,targetLayer)
                if res == True and not targetLayer.startswith("GIS Servers\\") == True:
                    layer = targetName
                    layertmp = targetName + "tmp"
                    if arcpy.Exists(layertmp):
                        arcpy.Delete_management(layertmp)
                    arcpy.MakeFeatureLayer_management(dlaTable,layertmp)
                    fieldInfo = dla.getLayerVisibility(layertmp,xmlFile)
                    arcpy.Delete_management(layertmp)
                    if arcpy.Exists(layer):
                        arcpy.Delete_management(layer)
                    
                    arcpy.MakeFeatureLayer_management(targetLayer,layer,None,dla.workspace,fieldInfo)
                    # should make only the target fields visible
                    arcpy.SetParameter(_success,layer)
                else:
                    arcpy.SetParameter(_success,res)

        arcpy.ResetProgressor()
        sourceLayer = None # set source and target back to None for multiple file processing
        targetLayer = None
        if res == False:
            err = "Publish Failed, see messages for details"
            arcpy.AddError("Publish Failed, see messages for details")
            print(err)

def doPublish(xmlDoc,dlaTable,targetLayer):
    # either truncate and replace or replace by field value
    # run locally or update agol
    success = False
    expr = ''
    dlaTable = handleGeometryChanges(dlaTable,targetLayer)

    if useReplaceSettings == True:
        expr = getWhereClause(xmlDoc)
    if useReplaceSettings == True and (expr == '' or expr == None):
        dla.addError("There must be an expression for replacing by field value, current value = " + str(expr))
        return False

    if targetLayer.startswith("GIS Servers\\") == True or targetLayer.startswith("http") == True:
        targetLayer = dla.getLayerSourceUrl(targetLayer)
        success = doPublishPro(dlaTable,targetLayer,expr)
    else:
        dlaTable = handleGeometryChanges(dlaTable,targetLayer)
        # logic change - if not replace field settings then only append
        if expr != '' and useReplaceSettings == True:
            if dla.deleteRows(targetLayer,expr) == True:
                success = dla.appendRows(dlaTable,targetLayer,expr)
            else:
                success = False       
        else:
            success = dla.doInlineAppend(dlaTable,targetLayer)

    return success

def getOIDs(targelUrl,expr):
    ids = []
    arcpy.SetProgressor("default","Querying Existing Features")
    arcpy.SetProgressorLabel("Querying Existing Features")
    url = targelUrl + '/query'
    arcpy.AddMessage("Url:"+url)
    token = dla.getSigninToken()
    if expr != '':
        params = {'f': 'pjson', 'where': expr,'token':token,'returnIdsOnly':'true'}
    else:
        params = {'f': 'pjson', 'where': '1=1','token':token,'returnIdsOnly':'true'}
        
    arcpy.AddMessage("Params:"+json.dumps(params))
    result = dla.sendRequest(url,params)            
    try:
        if result['error'] != None:
            retval = False
            arcpy.AddMessage("Query features from Feature Service failed")
            arcpy.AddMessage(json.dumps(result))
            error = True
    except:
        ids = result['objectIds']
        lenFound = len(ids)
        msg = str(lenFound) + " features found in existing Service"
        print(msg)
        arcpy.AddMessage(msg)
        retval = True

    return ids    

def deleteFeatures(sourceLayer,targelUrl,expr):
    retval = False
    error = False
    # delete section
    ids = getOIDs(targelUrl,expr)
    try:
        lenDeleted = 100
        #Chunk deletes using chunk size at a time
        featuresProcessed = 0
        numFeat = len(ids)
        if numFeat == 0:
            arcpy.AddMessage("0 Features to Delete, exiting")            
            return True # nothing to delete is OK
        if numFeat > _chunkSize:
            chunk = _chunkSize
        else:
            chunk = numFeat
        arcpy.SetProgressor("default","Deleting Features")
        while featuresProcessed < numFeat and error == False:
            #Chunk deletes using chunk size at a time
            next = featuresProcessed + chunk
            msg = "Deleting features " + str(featuresProcessed) + ":" + str(next)
            arcpy.AddMessage(msg)
            arcpy.SetProgressorLabel(msg)
            oids = ",".join(str(e) for e in ids[featuresProcessed:next])
            url = targelUrl + '/deleteFeatures'
            token = dla.getSigninToken()
            params = {'f': 'pjson', 'objectIds': oids,'token':token}
            result = dla.sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    arcpy.AddMessage("Delete features from Feature Service failed")
                    arcpy.AddMessage(json.dumps(result))
                    error = True
            except:
                lenDeleted = len(result['deleteResults'])
                msg = str(lenDeleted) + " features deleted, " + str(featuresProcessed + chunk) + "/" + str(numFeat)
                print(msg)
                arcpy.AddMessage(msg)
                retval = True
                featuresProcessed += chunk
    except:
        retval = False
        error = True
        dla.showTraceback()
        arcpy.AddMessage("Delete features from Feature Service failed")
        pass

    return retval


def addFeatures(sourceLayer,targelUrl,expr):
    retval = False
    error = False
    # add section
    try:
        arcpy.SetProgressor("default","Adding Features")
        arcpy.SetProgressorLabel("Adding Features")
        featurejs = featureclass_to_json(sourceLayer)
        url = targelUrl + '/addFeatures'  
        numFeat = len(featurejs['features'])
        if numFeat == 0:
            arcpy.AddMessage("0 Features to Add, exiting")            
            return True # nothing to add is OK
        if numFeat > _chunkSize:
            chunk = _chunkSize
        else:
            chunk = numFeat
        featuresProcessed = 0
        while featuresProcessed < numFeat  and error == False:
            next = featuresProcessed + chunk
            features = featurejs['features'][featuresProcessed:next]
            msg = "Adding features " + str(featuresProcessed) + ":" + str(next)
            arcpy.AddMessage(msg)
            arcpy.SetProgressorLabel(msg)
            token = dla.getSigninToken()
            params = {'rollbackonfailure': 'true','f':'json', 'token':token, 'features': json.dumps(features)}
            result = dla.sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    arcpy.AddMessage("Add features to Feature Service failed")
                    arcpy.AddMessage(json.dumps(result))
                    error = True
            except:
                lenAdded = len(result['addResults']) 
                msg = str(lenAdded) + " features added, " + str(featuresProcessed + chunk) + "/" + str(numFeat)
                print(msg)
                arcpy.AddMessage(msg)
                retval = True
            featuresProcessed += chunk
    except:
        retval = False
        arcpy.AddMessage("Add features to Feature Service failed")
        dla.showTraceback()
        error = True
        pass

    return retval
    

def doPublishPro(sourceLayer,targelUrl,expr):
    
    token = dla.getSigninToken()
    if token == None:
        arcpy.AddError("Unable to retrieve token, exiting")
        return False
    if expr != '' and useReplaceSettings == True:
        retval = deleteFeatures(sourceLayer,targelUrl,expr)
    else:
        retval = True
    if retval == True:
        retval = addFeatures(sourceLayer,targelUrl,expr)

    return retval

def featureclass_to_json(fc):
    """ converts a feature class to a json dictionary representation """
    featureSet = arcpy.FeatureSet(fc)# Load the feature layer into a feature set
    desc = arcpy.Describe(featureSet)# use the json property of the feature set
    return json.loads(desc.json)

def handleGeometryChanges(sourceDataset,targetLayer):
    desc = arcpy.Describe(sourceDataset) # assuming local file gdb
    dataset = sourceDataset
    if desc.ShapeType == "Polygon" and (targetLayer.lower().startswith("gis servers") == True or targetLayer.lower().startswith("http://") == True):
        dataset = simplifyPolygons(sourceDataset)
    else:
        dataset = sourceDataset    

    return dataset

def simplifyPolygons(sourceDataset):
    arcpy.AddMessage("Simplifying (densifying) Parcel Geometry")
    arcpy.Densify_edit(sourceDataset)
    simplify = sourceDataset + '_simplified'
    if arcpy.Exists(simplify):
        arcpy.Delete_management(simplify)
    if arcpy.Exists(simplify + '_Pnt'):
        arcpy.Delete_management(simplify + '_Pnt')
        
    arcpy.SimplifyPolygon_cartography(sourceDataset, simplify, "POINT_REMOVE", "1 Meters")
    return simplify

def getWhereClause(xmlDoc):

    repl = xmlDoc.getElementsByTagName("ReplaceBy")[0]
    fieldName = dla.getNodeValue(repl,"FieldName")
    operator = dla.getNodeValue(repl,"Operator")
    value = dla.getNodeValue(repl,"Value")
    expr = ''
    type = getTargetType(xmlDoc,fieldName)
    if fieldName != '' and fieldName != '(None)' and operator != "Where":
        if type == 'String':
            value = "'" + value + "'"
        expr = fieldName + " " + operator + " " + value
        
    elif operator == 'Where':
        expr = value
    else: 
        expr = '' # empty string by default
        
    return expr

def getTargetType(xmlDoc,fname):
    for tfield in xmlDoc.getElementsByTagName('TargetField'):       
        nm = tfield.getAttribute("Name")
        if nm == fname:
            return tfield.getAttribute("Type")

def checkLayerIsService(layerStr):
    if layerStr.find("http:") > -1 or layerStr.startswith("GIS Servers") == True:
        return True
    else:
        return False


if __name__ == "__main__":
    main()


