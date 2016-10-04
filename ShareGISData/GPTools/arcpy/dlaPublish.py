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
# dlaPublish.py - Publish one source to a target
# ----------------------------------------------------------------------------------------------------------------------
'''
This script is called by both Append Data and Replace Data tools. It has several options for running
the tool using as a Geoprocessing script directly or by callng dlaPublish.publish from another script.

Note in the GP script approach a source and target dataset can be provided as parameters to override the settings
in the Xml Config file. In this case just a single xml file should be passed with the datasets as the 2nd and 3rd
parameters. By default this will use the Append approach, to use replace by settings you can also make the
useReplaceSettings variable to change the behavior (see example at the end of this script).
'''

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dla,xml.dom.minidom,os
import json, urllib
import urllib.parse as parse
import urllib.request as request

arcpy.AddMessage("Data Assistant")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;

useReplaceSettings = False # change this from a calling script to make this script replace data.
    
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

_chunkSize = 100

def main(argv = None):
    # this approach makes it easier to call publish from other python scripts with using GP tool method
    publish(xmlFileNames)

def publish(xmlFileNames):
    # function called from main or from another script, performs the data update processing
    global sourceLayer,targetLayer,_success
    dla._errCount = 0

    arcpy.SetProgressor("default","Data Assistant")
    arcpy.SetProgressorLabel("Data Assistant")
    xmlFiles = xmlFileNames.split(";")
    for xmlFile in xmlFiles: # multi value parameter, loop for each file
        dla.addMessage("Configuration file: " + xmlFile)
        xmlDoc = dla.getXmlDoc(xmlFile) # parse the xml document
        if xmlDoc == None:
            return
        svceS = False
        svceT = False
        if sourceLayer == "" or sourceLayer == None:
            sourceLayer = dla.getNodeValue(xmlDoc,"Source")
            svceS = dla.checkLayerIsService(sourceLayer)
        if targetLayer == "" or targetLayer == None:
            targetLayer = dla.getNodeValue(xmlDoc,"Target")
            svceT = dla.checkLayerIsService(targetLayer)

        dla.addMessage(targetLayer)
        ## Added May2016. warn user if capabilities are not correct, exit if not a valid layer
        if not dla.checkServiceCapabilities(sourceLayer,True):
            return False
        if not dla.checkServiceCapabilities(targetLayer,True):
            return False

        if svceS == True or svceT == True:
            token = dla.getSigninToken() # when signed in get the token and use this. Will be requested many times during the publish
            if token == None:
                dla.addError("User must be signed in for this tool to work with services")
                return

        expr = getWhereClause(xmlDoc)
        if useReplaceSettings == True and (expr == '' or expr == None):
            dla.addError("There must be an expression for replacing by field value, current value = " + str(expr))
            return False

        dla.setWorkspace()
        targetName = dla.getTargetName(xmlDoc)
        res = dlaExtractLayerToGDB.extract(xmlFile,None,dla.workspace,sourceLayer,targetName)
        if res != True:
            table = dla.getTempTable(targetName)
            msg = "Unable to export data, there is a lock on existing datasets or another unknown error"
            if arcpy.TestSchemaLock(table) != True:
                msg = "Unable to export data, there is a lock on the intermediate feature class: " + table
            dla.addError(msg)
            print(msg)
            return
        else:
            res = dlaFieldCalculator.calculate(xmlFile,dla.workspace,targetName,False)
            if res == True:
                dlaTable = dla.getTempTable(targetName)
                res = doPublish(xmlDoc,dlaTable,targetLayer)

        arcpy.ResetProgressor()
        sourceLayer = None # set source and target back to None for multiple file processing
        targetLayer = None
        if res == False:
            err = "Data Assistant Update Failed, see messages for details"
            dla.addError(err)
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
        dla.addError("There must be an expression for replacing by field value, current value = '" + str(expr) + "'")
        return False

    if targetLayer.startswith("GIS Servers\\") == True or targetLayer.startswith("http") == True:
        targetLayer = dla.getLayerSourceUrl(targetLayer)
        success = doPublishPro(dlaTable,targetLayer,expr)
    else:
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

def deleteFeatures(sourceLayer,targelUrl,expr):
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


def addFeatures(sourceLayer,targelUrl,expr):
    # add features using _chunkSize
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
                    dla.addMessage("Add features to Feature Service failed")
                    dla.showTraceback()
                    dla.addError(json.dumps(result))
                    error = True
            featuresProcessed += chunk
    except:
        retval = False
        dla.addMessage("Add features to Feature Service failed")
        dla.showTraceback()
        error = True
        pass

    return retval
    

def doPublishPro(sourceLayer,targelUrl,expr):
    # logic for publishing to service registered on Portal or ArcGIS Online
    retval = True
    token = dla.getSigninToken()
    if token == None:
        dla.addError("Unable to retrieve token, exiting")
        return False
    dla.setupProxy()
    if expr != '' and useReplaceSettings == True:
        retval = deleteFeatures(sourceLayer,targelUrl,expr)
    if retval == True:
        retval = addFeatures(sourceLayer,targelUrl,expr)

    return retval

def featureclass_to_json(fc):
    # converts a feature class to a json dictionary representation 
    featureSet = arcpy.FeatureSet(fc)# Load the feature layer into a feature set
    desc = arcpy.Describe(featureSet)# use the json property of the feature set
    return json.loads(desc.json)

def handleGeometryChanges(sourceDataset,targetLayer):
    # simplfiy polygons
    desc = arcpy.Describe(sourceDataset) # assuming local file gdb
    dataset = sourceDataset
    if desc.ShapeType == "Polygon" and (targetLayer.lower().startswith("gis servers") == True or targetLayer.lower().startswith("http://") == True):
        dataset = simplifyPolygons(sourceDataset)
    else:
        dataset = sourceDataset    

    return dataset

def simplifyPolygons(sourceDataset):
    # simplfy polygons using approach developed by Chris Bus.
    dla.addMessage("Simplifying (densifying) Parcel Geometry")
    arcpy.Densify_edit(sourceDataset)
    simplify = sourceDataset + '_simplified'
    if arcpy.Exists(simplify):
        arcpy.Delete_management(simplify)
    if arcpy.Exists(simplify + '_Pnt'):
        arcpy.Delete_management(simplify + '_Pnt')
        
    arcpy.SimplifyPolygon_cartography(sourceDataset, simplify, "POINT_REMOVE", "1 Meters")
    return simplify

def getWhereClause(xmlDoc):
    # get the where clause using the xml document or return ''
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
    # get the target field type
    for tfield in xmlDoc.getElementsByTagName('TargetField'):       
        nm = tfield.getAttribute("Name")
        if nm == fname:
            return tfield.getAttribute("Type")


'''
some scrapyard items
#_success = 1 # the last param is the derived output layer
# this section was commented out since Publish is being called from replace and append scripts now. This could
# be used in the future to also have a GP tool with option to replace/append. Right now it will just do append...
# unless useReplaceSettings is set to True.
#useReplaceSettings = arcpy.GetParameterAsText(1) # indicates whether to replace by field value or just truncate/append

#if useReplaceSettings.lower() == 'true':
#    useReplaceSettings = True
#else:
'''


if __name__ == "__main__":
    main()


