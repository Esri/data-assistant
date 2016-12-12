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
# dlaAGOService - functions that interact with ArcGIS Online Services
# ----------------------------------------------------------------------------------------------------------------------
'''
'''

import arcpy,dla,xml.dom.minidom,os
import json, urllib
import urllib.parse as parse
import urllib.request as request

_chunkSize = 100

def getOIDs(targelUrl,expr):
    # get the list of oids.
    ids = []
    arcpy.SetProgressor("default","Querying Existing Features")
    arcpy.SetProgressorLabel("Querying Existing Features")
    url = targelUrl + '/query'
    #dla.addMessage("Url:"+url)
    token = dla.getSigninToken()
    if expr != '':
        params = {'f': 'pjson', 'where': expr,'token':token,'returnIdsOnly':'true'}
    else:
        params = {'f': 'pjson', 'where': '1=1','token':token,'returnIdsOnly':'true'}
        
    #dla.addMessage("Params:"+json.dumps(params))
    result = dla.sendRequest(url,params)            
    try:
        if result['error'] != None:
            retval = False
            dla.addMessage("Query features from Feature Service failed")
            dla.addMessage(json.dumps(result))
            error = True
    except:
        ids = result['objectIds']
        lenFound = len(ids)
        msg = str(lenFound) + " features found in existing Service"
        print(msg)
        dla.addMessage(msg)
        retval = True

    return ids    

def deleteFeatures(source,targelUrl,expr):
    # delete features using chunks of _chunkSize
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
            dla.addMessage("0 Features to Delete, exiting")            
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
            dla.addMessage(msg)
            arcpy.SetProgressorLabel(msg)
            oids = ",".join(str(e) for e in ids[featuresProcessed:next])
            url = targelUrl + '/deleteFeatures'
            token = dla.getSigninToken()
            params = {'f': 'pjson', 'objectIds': oids,'token':token}
            result = dla.sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    dla.addMessage("Delete features from Feature Service failed")
                    dla.addMessage(json.dumps(result))
                    error = True
            except:
                try:
                    lenDeleted = len(result['deleteResults'])
                    msg = str(lenDeleted) + " features deleted, " + str(featuresProcessed + chunk) + "/" + str(numFeat)
                    print(msg)
                    dla.addMessage(msg)
                    retval = True
                except:
                    retval = False
                    error = True
                    dla.showTraceback()
                    dla.addMessage("Delete features from Feature Service failed")
                    dla.addError(json.dumps(result))
            featuresProcessed += chunk
    except:
        retval = False
        error = True
        dla.showTraceback()
        dla.addMessage("Delete features from Feature Service failed")
        pass

    return retval


def addFeatures(source,targelUrl,expr):
    # add features using _chunkSize
    retval = False
    error = False
    # add section
    try:
        arcpy.SetProgressor("default","Adding Features")
        arcpy.SetProgressorLabel("Adding Features")
        featurejs = featureclass_to_json(source)
        url = targelUrl + '/addFeatures'  
        try:
            numFeat = len(featurejs['features'])
        except:
            numFeat = 0
        if numFeat == 0:
            dla.addMessage("0 Features to Add, exiting")            
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
            dla.addMessage(msg)
            arcpy.SetProgressorLabel(msg)
            token = dla.getSigninToken()
            params = {'rollbackonfailure': 'true','f':'json', 'token':token, 'features': json.dumps(features)}
            result = dla.sendRequest(url,params)            
            try:
                if result['error'] != None:
                    retval = False
                    dla.addMessage("Add features to Feature Service failed")
                    dla.addMessage(json.dumps(result))
                    error = True
            except:
                try:
                    lenAdded = len(result['addResults']) 
                    msg = str(lenAdded) + " features added, " + str(featuresProcessed + chunk) + "/" + str(numFeat)
                    print(msg)
                    dla.addMessage(msg)
                    retval = True
                except:
                    retval = False
                    dla.addMessage("Add features to Feature Service failed. Unfortunately you will need to re-run this tool.")
                    #dla.showTraceback()
                    #dla.addError(json.dumps(result))
                    error = True
            featuresProcessed += chunk
    except:
        retval = False
        dla.addMessage("Add features to Feature Service failed")
        dla.showTraceback()
        error = True
        pass

    return retval
    

def doPublishPro(source,targelUrl,expr):
    # logic for publishing to service registered on Portal or ArcGIS Online
    retval = True
    token = dla.getSigninToken()
    if token == None:
        dla.addError("Unable to retrieve token, exiting")
        return False
    dla.setupProxy()
    if expr != '' and useReplaceSettings == True:
        retval = deleteFeatures(source,targelUrl,expr)
    if retval == True:
        retval = addFeatures(source,targelUrl,expr)

    return retval

def featureclass_to_json(fc):
    # converts a feature class to a json dictionary representation 
    featureSet = arcpy.FeatureSet(fc)# Load the feature layer into a feature set
    desc = arcpy.Describe(featureSet)# use the json property of the feature set
    return json.loads(desc.json)



