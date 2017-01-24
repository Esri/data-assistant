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

import arcpy,dlaExtractLayerToGDB,dlaFieldCalculator,dlaService,dla,dlaService,xml.dom.minidom,os

arcpy.AddMessage("Data Assistant")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;
_outParam = 1
_useReplaceSettings = False # change this from a calling script to make this script replace data.

_chunkSize = 100

def main(argv = None):
    # this approach makes it easier to call publish from other python scripts with using GP tool method
    publish(xmlFileNames)

def publish(xmlFileNames):
    # function called from main or from another script, performs the data update processing
    global _useReplaceSettings
    dla._errCount = 0

    arcpy.SetProgressor("default","Data Assistant")
    arcpy.SetProgressorLabel("Data Assistant")
    xmlFiles = xmlFileNames.split(";")
    layers = []
    for xmlFile in xmlFiles: # multi value parameter, loop for each file
        dla.addMessage("Configuration file: " + xmlFile)
        xmlDoc = dla.getXmlDoc(xmlFile) # parse the xml document
        if xmlDoc == None:
            return
        source = dla.getNodeValue(xmlDoc,"Source")
        target = dla.getNodeValue(xmlDoc,"Target")
        targetName = dla.getDatasetName(target)
        dla.addMessage(source)
        dla.addMessage(target)

        svceS = dlaService.checkLayerIsService(source)
        svceT = dlaService.checkLayerIsService(target)

        ## Added May2016. warn user if capabilities are not correct, exit if not a valid layer
        if not dlaService.checkServiceCapabilities(source,True):
            return False
        if not dlaService.checkServiceCapabilities(target,True):
            return False

        if svceS == True or svceT == True:
            token = dlaService.getSigninToken() # when signed in get the token and use this. Will be requested many times during the publish
            if token == None:
                dla.addError("User must be signed in for this tool to work with services")
                return

        expr = getWhereClause(xmlDoc)
        if _useReplaceSettings == True and (expr == '' or expr == None):
            dla.addError("There must be an expression for replacing by field value, current value = " + str(expr))
            return False

        dla.setWorkspace()

        if dla.isTable(source) or dla.isTable(target):
            datasetType = 'Table'
        else:
            datasetType = 'FeatureClass'
        
        res = dlaExtractLayerToGDB.extract(xmlFile,None,dla.workspace,source,target,datasetType)
        if res != True:
            table = dla.getTempTable(targetName)
            msg = "Unable to export data, there is a lock on existing datasets or another unknown error"
            if arcpy.TestSchemaLock(table) != True and arcpy.Exists(table) == True:
                msg = "Unable to export data, there is a lock on the intermediate feature class: " + table
            dla.addError(msg)
            print(msg)
            return
        else:
            res = dlaFieldCalculator.calculate(xmlFile,dla.workspace,targetName,False)
            if res == True:
                dlaTable = dla.getTempTable(targetName)
                res = doPublish(xmlDoc,dlaTable,target,_useReplaceSettings)

        arcpy.ResetProgressor()
        if res == False:
            err = "Data Assistant Update Failed, see messages for details"
            dla.addError(err)
            print(err)
        else:
            layers.append(target)

    arcpy.SetParameter(_outParam,';'.join(layers))

def doPublish(xmlDoc,dlaTable,target,useReplaceSettings):
    # either truncate and replace or replace by field value
    # run locally or update agol
    success = False
    expr = ''
    dlaTable = handleGeometryChanges(dlaTable,target)

    if useReplaceSettings == True:
        expr = getWhereClause(xmlDoc)
    if useReplaceSettings == True and (expr == '' or expr == None):
        dla.addError("There must be an expression for replacing by field value, current value = '" + str(expr) + "'")
        return False
    target = dla.getLayerPath(target)
    if target.startswith("http") == True:
        success = dlaService.doPublishHttp(dlaTable,target,expr,useReplaceSettings)
    else:
        # logic change - if not replace field settings then only append
        if expr != '' and useReplaceSettings == True:
            if dla.deleteRows(target,expr) == True:
                success = dla.appendRows(dlaTable,target,expr)
            else:
                success = False       
        else:
            success = dla.appendRows(dlaTable,target,'')
    return success

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

def handleGeometryChanges(sourceDataset,target):
    # simplfiy polygons
    if dla.isTable(sourceDataset):
        return sourceDataset
    desc = arcpy.Describe(sourceDataset) # assuming local file gdb
    dataset = sourceDataset
    if desc.ShapeType == "Polygon" and target.lower().startswith("http://") == True:
        dataset = simplifyPolygons(sourceDataset)
    else:
        dataset = sourceDataset    

    return dataset

def simplifyPolygons(sourceDataset):
    # simplify polygons using approach developed by Chris Bus.
    dla.addMessage("Simplifying (densifying) Geometry")
    arcpy.Densify_edit(sourceDataset)
    simplify = sourceDataset + '_simplified'
    if arcpy.Exists(simplify):
        arcpy.Delete_management(simplify)
    if arcpy.Exists(simplify + '_Pnt'):
        arcpy.Delete_management(simplify + '_Pnt')
        
    arcpy.SimplifyPolygon_cartography(sourceDataset, simplify, "POINT_REMOVE", "1 Meters")
    return simplify

if __name__ == "__main__":
    main()


