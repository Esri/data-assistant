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
# dlaService - functions that interact with ArcGIS Online/Portal Services - refactored from dla.py and dlaPublish.py in Dec 2016
# ----------------------------------------------------------------------------------------------------------------------
'''
'''
import arcpy,dla,xml.dom.minidom,os
import json, urllib
import urllib.parse as parse
import urllib.request as request

_chunkSize = 100

def getOIDs(targetUrl,expr):
    # get the list of oids.
    ids = []
    arcpy.SetProgressor("default","Querying Existing Rows")
    arcpy.SetProgressorLabel("Querying Existing Rows")
    url = targetUrl + '/query'
    #dla.addMessage("Url:"+url)
    token = getSigninToken()
    if expr != '':
        params = {'f': 'pjson', 'where': expr,'token':token,'returnIdsOnly':'true'}
    else:
        params = {'f': 'pjson', 'where': '1=1','token':token,'returnIdsOnly':'true'}
        
    #dla.addMessage("Params:"+json.dumps(params))
    result = sendRequest(url,params)            
    try:
        if result['error'] != None:
            retval = False
            dla.addMessage("Query Rows from Service failed")
            dla.addMessage(json.dumps(result))
            error = True
    except:
        ids = result['objectIds']
        lenFound = len(ids)
        msg = str(lenFound) + " Rows found in existing Service"
        print(msg)
        dla.addMessage(msg)
        retval = True

    return ids    

def deleteRows(source,targetUrl,expr):
    # delete Rows using chunks of _chunkSize
    retval = False
    error = False
    # delete section
    ids = getOIDs(targetUrl,expr)
    try:
        lenDeleted = 100
        #Chunk deletes using chunk size at a time
        rowsProcessed = 0
        numFeat = len(ids)
        if numFeat == 0:
            dla.addMessage("0 Rows to Delete, exiting")            
            return True # nothing to delete is OK
        if numFeat > _chunkSize:
            chunk = _chunkSize
        else:
            chunk = numFeat
        arcpy.SetProgressor("default","Deleting Rows")
        while rowsProcessed < numFeat and error == False:
            #Chunk deletes using chunk size at a time
            next = rowsProcessed + chunk
            msg = "Deleting rows " + str(rowsProcessed) + ":" + str(next)
            dla.addMessage(msg)
            arcpy.SetProgressorLabel(msg)
            oids = ",".join(str(e) for e in ids[rowsProcessed:next])
            url = targetUrl + '/deleteFeatures'
            token = getSigninToken()
            params = {'f': 'pjson', 'objectIds': oids,'token':token}
            result = sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    dla.addMessage("Delete rows from Service failed")
                    dla.addMessage(json.dumps(result))
                    error = True
            except:
                try:
                    lenDeleted = len(result['deleteResults'])
                    msg = str(lenDeleted) + " rows deleted, " + str(rowsProcessed + chunk) + "/" + str(numFeat)
                    print(msg)
                    dla.addMessage(msg)
                    retval = True
                except:
                    retval = False
                    error = True
                    dla.showTraceback()
                    dla.addMessage("Delete rows from Service failed")
                    dla.addError(json.dumps(result))
            rowsProcessed += chunk
    except:
        retval = False
        error = True
        dla.showTraceback()
        dla.addMessage("Delete rows from Service failed")
        pass

    return retval

def addRows(source,targetUrl,expr):
    # add rows using _chunkSize
    retval = False
    error = False
    # add section
    try:
        arcpy.SetProgressor("default","Adding Rows")
        arcpy.SetProgressorLabel("Adding Rows")
        rowjs = rowsToJson(source)
        url = targetUrl + '/addFeatures'  
        try:
            numFeat = len(rowjs['features'])
        except:
            numFeat = 0
        if numFeat == 0:
            dla.addMessage("0 Rows to Add, exiting")            
            return True # nothing to add is OK
        if numFeat > _chunkSize:
            chunk = _chunkSize
        else:
            chunk = numFeat
        rowsProcessed = 0
        while rowsProcessed < numFeat  and error == False:
            next = rowsProcessed + chunk
            rows = rowjs['features'][rowsProcessed:next]
            msg = "Adding rows " + str(rowsProcessed) + ":" + str(next)
            dla.addMessage(msg)
            arcpy.SetProgressorLabel(msg)
            token = getSigninToken()
            params = {'rollbackonfailure': 'true','f':'json', 'token':token, 'features': json.dumps(rows)}
            result = sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    dla.addMessage("Add rows to Service failed")
                    dla.addMessage(json.dumps(result))
                    error = True
            except:
                try:
                    lenAdded = len(result['addResults']) 
                    msg = str(lenAdded) + " rows added, " + str(rowsProcessed + chunk) + "/" + str(numFeat)
                    print(msg)
                    dla.addMessage(msg)
                    retval = True
                except:
                    retval = False
                    dla.addMessage("Add rows to Service failed. Unfortunately you will need to re-run this tool.")
                    #dla.showTraceback()
                    #dla.addError(json.dumps(result))
                    error = True
            rowsProcessed += chunk
    except:
        retval = False
        dla.addMessage("Add rows to Service failed")
        dla.showTraceback()
        error = True
        pass

    return retval
    
def doPublishPro(source,targetUrl,expr,useReplaceSettings):
    # logic for publishing to service registered on Portal or ArcGIS Online
    retval = True
    token = getSigninToken()
    if token == None:
        dla.addError("Unable to retrieve token, exiting")
        return False
    dla.setupProxy()
    if expr != '' and useReplaceSettings == True:
        retval = deleteRows(source,targetUrl,expr)
    if retval == True:
        retval = addRows(source,targetUrl,expr)

    return retval

def rowsToJson(dataset):
    # converts a feature class/table to a json dictionary representation
    try: 
        rows = arcpy.FeatureSet(dataset) # Load the feature layer into a feature set
    except:
        rows = arcpy.RecordSet(dataset) # Load the feature layer into a feature set

    desc = arcpy.Describe(rows) # use the json property of the feature set
    return json.loads(desc.json)

def sendRequest(url, qDict=None, headers=None):
    """Robust request maker - from github https://github.com/khibma/ArcGISProPythonAssignedLicensing/blob/master/ProLicense.py"""
    #Need to handle chunked response / incomplete reads. 2 solutions here: http://stackoverflow.com/questions/14442222/how-to-handle-incompleteread-in-python
    #This function sends a request and handles incomplete reads. However its found to be very slow. It adds 30 seconds to chunked
    #responses. Forcing the connection to HTTP 10 (1.0) at the top, for some reason makes it faster.         
    
    qData = parse.urlencode(qDict).encode('UTF-8') if qDict else None    
    reqObj = request.Request(url)
    
    if headers != None:
        for k, v in headers.items():
            reqObj.add_header(k, v)
            
    try:
        if qDict == None:  #GET            
            r = request.urlopen(reqObj)
        else:  #POST            
            r = request.urlopen(reqObj, qData)
        responseJSON=""
        while True:
            try:                            
                responseJSONpart = r.read()                
            except client.IncompleteRead as icread:                
                responseJSON = responseJSON + icread.partial.decode('utf-8')
                continue
            else:                
                responseJSON = responseJSON + responseJSONpart.decode('utf-8')
                break       
        
        return (json.loads(responseJSON))
       
    except Exception as RESTex:
        print("Exception occurred making REST call: " + RESTex.__str__()) 

def openRequest(url,params):
    """
    Open an http request, handles the difference between urllib and urllib2 implementations if the includes are
    done correctly in the imports section of this file. Currently disabled.
    """
    response = None
    if uselib2 == True:
        data = urllib.urlencode(params)
        data = data.encode('utf8')
        req = urllib2.Request(url,data)  
        response = urllib2.urlopen(req)
    else:
        data = parse.urlencode(params)
        data = data.encode('utf8')
        req = request.Request(url,data)
        response = request.urlopen(req)
    
    return response

def getSigninToken():
    data = arcpy.GetSigninToken()
    token = None
    if data is not None:
        token = data['token']
        #expires = data['expires']
        #referer = data['referer']
    else:
        arcpy.AddMessage("Error: No token - Please sign in to ArcGIS Online or your Portal to continue")
    return token

## Added May 2016 
def hasCapabilities(url,token,checkList):
    hasit = False
    if token != None and isFeatureLayerUrl(url):
        params = {'f': 'pjson', 'token':token}
        response = sendRequest(url,params)
        if response != None:
            try:
                error = json.dumps(response['error'])
                addError('Unable to access service properties ' + error)
                return False
            except:
                hasit = True
            
            try:
                capabilities = json.dumps(response['capabilities'])
                dla.addMessage('Service REST capabilities: ' + capabilities)
                for item in checkList:
                    if capabilities.find(item) == -1:
                        dla.addMessage('Service does not support: ' + item)
                        hasit = False
                    else:
                        dla.addMessage('Service supports: ' + item)
            except:
                addError('Unable to access service capabilities')                
                hasit = False
        else:
            addError('Unable to access service')                
            hasit = False
        
    return hasit

def getServiceName(url):
    parts = url.split('/')
    lngth = len(parts)
    if len(parts) > 8:
        dla.addMessage("Service Name: " + parts[7])
        return parts[7]

def isFeatureLayerUrl(url):
    # assume layer string has already had \ and GIS Servers or other characters switched to be a url
    parts = url.split('/')
    lngth = len(parts)
    try: 
        # check for number at end
        # last = int(parts[lngth-1])
        if parts[lngth-2] == 'FeatureServer':
            return True
    except:
        addError("2nd last part of url != 'FeatureServer'")
        return False

def checkLayerIsService(layerStr):
    ## moved here from dlaPublish
    # Check if the layer string is a service
    if layerStr.lower().startswith("http") == True or layerStr.lower().startswith("gis servers") == True:
        return True
    else:
        return False

def checkServiceCapabilities(sourcePath,required):
    ## Added May2016. Ensure that feature layer has been added and warn if capabilities are not available
    if sourcePath == None:
        dla.addMessage('Error: No path available for layer')            
        return False
    #dla.addMessage('Checking: ' + sourcePath)    
    if checkLayerIsService(sourcePath):
        url = sourcePath
        if isFeatureLayerUrl(url):
            data = arcpy.GetSigninToken()
            token = data['token']
            name = getServiceName(url)
            #print('Service',name)
            res = hasCapabilities(url,token,['Create','Delete'])
            if res != True and required == False:
                dla.addMessage('WARNING: ' + name + ' does not have Create and Delete privileges')
                dla.addMessage('Verify the service properties for: ' + url)
                dla.addMessage('This tool might continue but other tools will not run until this is addressed')
            elif res != True and required == True:
                addError('WARNING: ' + name + ' does not have Create and Delete privileges')
                dla.addMessage('Verify the service properties for: ' + url)
                dla.addMessage('This tool will not run until this is addressed')
            return res
        else:
            dla.addMessage(sourcePath + ' Does not appear to be a feature service layer, exiting. Check that you selected a layer not a service')
            return False
    else:
        return True

## end May 2016 section
