## dlaPublish.py - Publish one source to a target

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom
import json, urllib
import urllib.parse as parse
import urllib.request as request
uselib2 = False
try:
    import urllib2
    uselib2 = True
except:
    pass    

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

        arcpy.ResetProgressor()
        if res == False:
            arcpy.AddError("Publish Failed, see messages for details")

def doPublish(xmlDoc,sourceLayer,targetLayer):
    # either truncate and replace or replace by field value
    # run locally or update agol
    success = False
    expr = ''
    if useReplaceSettings == True:
        expr = getWhereClause(xmlDoc)

    if targetLayer.startswith("GIS Servers\\") == True:
        targetLayer = dla.getLayerSourceUrl(targetLayer)
        success = doPublishAgo(sourceLayer,targetLayer,expr)
    else:
        if expr != '':
            if dla.deleteRows(targetLayer,expr) == True:
                success = dla.appendRows(sourceLayer,targetLayer,expr)
            else:
                success = False       
        else:
            success = dla.doInlineAppend(sourceLayer,targetLayer)

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

def doPublishAgo(sourceLayer,targelUrl,expr):
    token = getToken()
    if token == None:
        arcpy.AddError("Unable to retrieve token, exiting")
        return False

    retval = False

    # delete section
    try:
        lenDeleted = 100
        while lenDeleted > 0:
            arcpy.SetProgressor("default","Deleting Features")
            arcpy.SetProgressorLabel("Deleting Features")
            url = targelUrl + '/deleteFeatures'
            arcpy.AddMessage("Url:"+url)
            where = expr
            params = {'f': 'pjson', 'where': expr,'token':token}
            arcpy.AddMessage("Params:"+json.dumps(params))
            response = openRequest(url,params)            
            val = response.readall().decode('utf-8')
            result = json.loads(val)
            try:
                if result['error'] != None:
                    retval = False
                    arcpy.AddMessage("Delete features from Feature Service failed")
                    arcpy.AddMessage(json.dumps(result))
            except:
                lenDeleted = len(result['deleteResults'])
                msg = str(lenDeleted) + " features deleted"
                print(msg)
                arcpy.AddMessage(msg)
                retval = True
    except:
        retval = False
        dla.showTraceback()
        arcpy.AddMessage("Delete features from Feature Service failed")
        pass
    if retval == True:
        retval = False
        # add section
        try:
            arcpy.SetProgressor("default","Adding Features")
            arcpy.SetProgressorLabel("Adding Features")
            featurejs = featureclass_to_json(sourceLayer)
            #print(featurejs['features'][1])
            url = targelUrl + '/addFeatures'  
            arcpy.AddMessage(url)
            params = {'rollbackonfailure': 'true','f':'json', 'token':token, 'features': json.dumps(featurejs['features'])}
            #arcpy.AddMessage(json.dumps(params))
            response = openRequest(url,params)            
            val = response.readall().decode('utf-8')
            result = json.loads(val)
            try:
                if result['error'] != None:
                    retval = False
                    arcpy.AddMessage("Add features to Feature Service failed")
                    arcpy.AddMessage(json.dumps(result))
            except:
                msg = str(len(result['addResults'])) + " features added"
                print(msg)
                arcpy.AddMessage(msg)
                retval = True
                        
        except:
            retval = False
            arcpy.AddMessage("Add features to Feature Service failed")
            dla.showTraceback()
            pass


    return retval

def openRequest(url,params):
    response = None
    if uselib2 == True:
        data = urllib2.urlencode(params)
        arcpy.AddMessage("Encode data")
        data = data.encode('utf8')
        arcpy.AddMessage("Prep request")
        req = urllib2.Request(url,data)  
        arcpy.AddMessage("Opening request...")
        response = urllib2.urlopen(req)
    else:
        data = parse.urlencode(params)
        arcpy.AddMessage("Encode data")
        data = data.encode('utf8')
        arcpy.AddMessage("Prep request")
        req = request.Request(url,data)
        arcpy.AddMessage("Opening request...")
        response = request.urlopen(req)
    return response

def featureclass_to_json(fc):
    """ converts a feature class to a json dictionary representation """
    featureSet = arcpy.FeatureSet(fc)# Load the feature layer into a feature set
    desc = arcpy.Describe(featureSet)# use the json property of the feature set
    return json.loads(desc.json)


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
    return expr

def getTargetType(xmlDoc,fname):
    for tfield in xmlDoc.getElementsByTagName('TargetField'):       
        nm = tfield.getAttribute("Name")
        if nm == fname:
            return tfield.getAttribute("Type")

if __name__ == "__main__":
    main()


