## dlaPublish.py - Publish one source to a target

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom
import json, urllib
import urllib.parse as parse
import urllib.request as request
uselib2 = False
#try: looks like just import urllib parts the 'new' python way works best. lib2 is old python 2 approach
#    import urllib2
#    uselib2 = True
#except:
#    pass    

arcpy.AddMessage("Data Assistant - Publish")

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
useReplaceSettings = arcpy.GetParameterAsText(1) # indicates whether to replace by field value or just truncate/append
_success = 2 # the last param is the derived output layer

if useReplaceSettings.lower() == 'true':
    useReplaceSettings = True
else:
    useReplaceSettings = False
    
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
    publish(xmlFileName)

def publish(xmlFileName):
    
    global sourceLayer,targetLayer,_success
    arcpy.SetProgressor("default","Publishing")
    arcpy.SetProgressorLabel("Publishing")
    for xmlfile in xmlFileName.split(";"): # multi value parameter
        xmlDoc = xml.dom.minidom.parse(xmlfile)
        if sourceLayer == "" or sourceLayer == None:
            sourceLayer = dla.getNodeValue(xmlDoc,"Source")
        if targetLayer == "" or targetLayer == None:
            targetLayer = dla.getNodeValue(xmlDoc,"Target")
        dla.setWorkspace()
        targetName = dla.getTargetName(xmlDoc)
        res = dlaExtractLayerToGDB.extract(xmlfile,None,dla.workspace,sourceLayer,targetName)
        if res == True:
            res = dlaFieldCalculator.calculate(xmlfile,dla.workspace,targetName,False)
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
                    fieldInfo = dla.getLayerVisibility(layertmp,xmlfile)
                    arcpy.Delete_management(layertmp)
                    if arcpy.Exists(layer):
                        arcpy.Delete_management(layer)
                    
                    arcpy.MakeFeatureLayer_management(targetLayer,layer,None,dla.workspace,fieldInfo)
                    # should make only the target fields visible
                    arcpy.SetParameter(_success,layer)
                else:
                    arcpy.SetParameter(_success,res)

        arcpy.ResetProgressor()
        if res == False:
            arcpy.AddError("Publish Failed, see messages for details")

def doPublish(xmlDoc,dlaTable,targetLayer):
    # either truncate and replace or replace by field value
    # run locally or update agol
    success = False
    expr = ''
    dlaTable = handleGeometryChanges(dlaTable,targetLayer)

    if useReplaceSettings == True:
        expr = getWhereClause(xmlDoc)

    if targetLayer.startswith("GIS Servers\\") == True:
        targetLayer = dla.getLayerSourceUrl(targetLayer)
        success = doPublishAgo(dlaTable,targetLayer,expr)
    else:
        dlaTable = handleGeometryChanges(dlaTable,targetLayer)
        if expr != '':
            if dla.deleteRows(targetLayer,expr) == True:
                success = dla.appendRows(dlaTable,targetLayer,expr)
            else:
                success = False       
        else:
            success = dla.doInlineAppend(dlaTable,targetLayer)

    return success

def getToken():
    
    data = arcpy.GetSigninToken()

    token = None
    if data is not None:
        token = data['token']
        arcpy.AddMessage("Using current token")
    else:
        arcpy.AddMessage("Error: No token - creating one")
        username = "***"  # Should never need this section in ArcGIS Pro...
        password = "***"  
          
        portal = arcpy.GetActivePortalURL()
        tokenURL = portal + '/sharing/rest/generateToken'  
        params = {'f': 'pjson', 'username': username, 'password': password, 'referer': portal}  
        params = urllib2.urlencode(params)
        params = params.encode('utf8')
        req = urllib.request.Request(tokenURL, params)
        #url = tokenURL + "?" + str(params)
        response = urllib.request.urlopen(req)
        result = response.readall().decode('utf-8')
        
        data = json.loads(result)  
        token = data['token']
    return token

def getOIDs(targelUrl,expr,token):
    ids = []
    arcpy.SetProgressor("default","Querying Existing Features")
    arcpy.SetProgressorLabel("Querying Existing Features")
    url = targelUrl + '/query'
    arcpy.AddMessage("Url:"+url)
    if expr != '':
        params = {'f': 'pjson', 'where': expr,'token':token,'returnIdsOnly':'true'}
    else:
        params = {'f': 'pjson', 'where': '1=1','token':token,'returnIdsOnly':'true'}
        
    arcpy.AddMessage("Params:"+json.dumps(params))
    response = openRequest(url,params)            
    val = response.readall().decode('utf-8')
    result = json.loads(val)
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
    


def deleteFeatures(sourceLayer,targelUrl,expr,token):
    retval = False
    error = False
    # delete section
    ids = getOIDs(targelUrl,expr,token)
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
            params = {'f': 'pjson', 'objectIds': oids,'token':token}
            response = openRequest(url,params)            
            val = response.readall().decode('utf-8')
            result = json.loads(val)
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


def addFeatures(sourceLayer,targelUrl,expr,token):
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
            params = {'rollbackonfailure': 'true','f':'json', 'token':token, 'features': json.dumps(features)}
            response = openRequest(url,params)            
            val = response.readall().decode('utf-8')
            result = json.loads(val)
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
    

def doPublishAgo(sourceLayer,targelUrl,expr):
    token = getToken()
    if token == None:
        arcpy.AddError("Unable to retrieve token, exiting")
        return False
    retval = deleteFeatures(sourceLayer,targelUrl,expr,token)
    if retval == True:
        retval = addFeatures(sourceLayer,targelUrl,expr,token)

    return retval

def openRequest(url,params):
    response = None
    if uselib2 == True:
        data = urllib2.urlencode(params)
        data = data.encode('utf8')
        req = urllib2.Request(url,data)  
        response = urllib2.urlopen(req)
    else:
        data = parse.urlencode(params)
        data = data.encode('utf8')
        req = request.Request(url,data)
        response = request.urlopen(req)
    return response

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
        expr = '1=1'
    return expr

def getTargetType(xmlDoc,fname):
    for tfield in xmlDoc.getElementsByTagName('TargetField'):       
        nm = tfield.getAttribute("Name")
        if nm == fname:
            return tfield.getAttribute("Type")

if __name__ == "__main__":
    main()


