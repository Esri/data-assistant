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
# dlaCreateSourceTarget.py - take a list of 2 datasets and export a Configuration file
# December 2015
# Loop through the source and target datasets and write an xml document

import os, sys, traceback, time, xml.dom.minidom, arcpy, dla
from xml.dom.minidom import Document, parse, parseString
import xml.etree.ElementTree as etree
import re

# Local variables...
debug = False 
# Parameters
sourceDataset = arcpy.GetParameterAsText(0) # source dataset to analyze
targetDataset = arcpy.GetParameterAsText(1) # target dataset to analyze
xmlFileName = arcpy.GetParameterAsText(2) # output file name argument
matchLibrary = 'true' # arcpy.GetParameterAsText(3) always use automatch now. When starting the match library is blank anyway
#  so this will have no effect until the user starts working with it.

if not xmlFileName.lower().endswith(".xml"):
    xmlFileName = xmlFileName + ".xml"

if matchLibrary.lower() == 'true':
    matchLibrary = True
else:
    matchLibrary = False

dir = os.path.dirname(os.path.realpath(__file__))
arcpy.AddMessage(dir)
matchxslt = os.path.join(dir,"FieldMatcher.xsl")
matchfile = os.path.join(dir,"MatchLocal.xml")

def main(argv = None):
    global sourceDataset,targetDataset,xmlFileName   
    dla.addMessage("Source: " + sourceDataset)
    dla.addMessage("Target: " + targetDataset)
    dla.addMessage("File: " + xmlFileName)
    if not os.path.exists(matchxslt):
        msg = matchxslt + " does not exist, exiting"
        arcpy.AddError(msg)
        print(msg)
        return
    if not os.path.exists(matchfile):
        msg = matchfile + " does not exist, exiting"
        arcpy.AddError(msg)
        print(msg)
        return
    createDlaFile(sourceDataset,targetDataset,xmlFileName)

def createDlaFile(sourceDataset,targetDataset,xmlFileName):

    # entry point for calling this tool from another python script
    writeDocument(sourceDataset,targetDataset,xmlFileName)
    
    return True

def writeDocument(sourceDataset,targetDataset,xmlFileName):

    sourcePath = getLayerPath(sourceDataset)
    targetPath = getLayerPath(targetDataset)

    if sourcePath == None or targetPath == None:
        return False

    ## Added May2016. warn user if capabilities are not correct, exit if not a valid layer
    if not dla.checkServiceCapabilities(sourcePath,False):
        dla.addMessage(sourceDataset + ' Does not appear to be a feature service layer, exiting. Check that you selected a layer not a service')
        return False
    if not dla.checkServiceCapabilities(targetPath,False):
        dla.addMessage(targetDataset + ' Does not appear to be a feature service layer, exiting. Check that you selected a layer not a service')
        return False

    desc = getDescribe(sourcePath,sourceDataset)
    descT = getDescribe(targetPath,targetDataset)

    xmlDoc = Document()
    root = xmlDoc.createElement('SourceTargetMatrix')
    xmlDoc.appendChild(root)
    root.setAttribute("version",'1.1')
    root.setAttribute("xmlns:esri",'http://www.esri.com')
    #root.setAttribute("encoding",'UTF-8')

    dataset = xmlDoc.createElement("Datasets")
    root.appendChild(dataset)
    prj = arcpy.mp.ArcGISProject("CURRENT")
    setSourceTarget(dataset,xmlDoc,"Project",prj.filePath)
    setSourceTarget(dataset,xmlDoc,"Source",getDataPath(sourcePath,sourceDataset))
    setSourceTarget(dataset,xmlDoc,"Target",getDataPath(targetPath,targetDataset))

    setSpatialReference(dataset,xmlDoc,desc,"Source")
    setSpatialReference(dataset,xmlDoc,descT,"Target")

    setSourceTarget(dataset,xmlDoc,"ReplaceBy","")

    fieldroot = xmlDoc.createElement("Fields")
    root.appendChild(fieldroot)

    fields = getFields(descT,targetDataset)
    sourceFields = getFields(desc,sourceDataset)
    sourceNames = [field.name[field.name.rfind(".")+1:] for field in sourceFields]
    upperNames = [nm.upper() for nm in sourceNames]

    #try:
    for field in fields:

        fNode = xmlDoc.createElement("Field")
        fieldroot.appendChild(fNode)
        fieldName = field.name[field.name.rfind(".")+1:]
        matchSourceFields(xmlDoc,fNode,field,fieldName,sourceNames,upperNames)

    # write the source field values
    setSourceFields(root,xmlDoc,sourceFields)
    setTargetFields(root,xmlDoc,fields)
    # Should add a template section for value maps, maybe write domains...
    # could try to preset field mapping and domain mapping...

    # add some data to the document
    writeDataSample(xmlDoc,root,sourceNames,sourceDataset,10)
    # write it out
    xmlDoc.writexml( open(xmlFileName, 'wt', encoding='utf-8'),indent="  ",addindent="  ",newl='\n')
    xmlDoc.unlink()

def getDataPath(layerPath,layer):
    if layerPath.startswith('CIMWKSP'):
        pth = layer
        dla.addMessage('layer pth '+ pth)
    else:
        pth = layerPath
        dla.addMessage('layerPath pth '+ pth)
    return pth

def getDescribe(layerPath,layer):
    try:
        desc = arcpy.Describe(layerPath) # if CIM workspace this fails
    except:
        desc = arcpy.Describe(layer)

    return desc

def getLayerPath(pth): # requires string for layer argument
    # altered May31 2016 to handle no .path for layer...
    # altered August 2016 - Pro 1.3.1 changes in urls for feature service layers
    #if pth != None:
    #    pthurl = dla.getLayerSourceUrl(pth)
        #desc = arcpy.Describe(pthurl)
        #try:
        #    pth = desc.catalogPath
        #    dla.addMessage("catalogPath:" + pth)
        #except:
            #try:
            #    pth = desc.path
            #    dla.addMessage("path:" + pth) # this never seems to be useful in 1.3.1 - the parent folder or catalog location
            #except:
        #    dla.addError('Unable to obtain a catalog path for this layer. Please select a feature layer and re-run this tool')
        #    pth = None
    if pth != None:
        pth = dla.getLayerServiceUrl(pth)
        dla.addMessage("Output path:" + pth)
    return pth

def setSpatialReference(dataset,xmlDoc,desc,lyrtype):
    try:
        spref = str(desc.spatialReference.factoryCode)
        setSourceTarget(dataset,xmlDoc,lyrtype + "FactoryCode",spref)
    except:
        try:
            setSourceTarget(dataset,xmlDoc,lyrtype + "SpatialReference",desc.spatialReference.exportToString())
        except:
            dla.showTraceback()
            arcpy.AddError("Could not set Spatial Reference for " + lyrtype + " Layer")

def matchSourceFields(xmlDoc,fNode,field,fieldName,sourceNames,upperNames):
    # match source field names - with and without automap
    enode = None
    count = 0
    nmupper = fieldName.upper()
    if matchLibrary == True: # only do this if matchLibrary parameter is True
        doc = etree.parse(matchfile)
        nodes = doc.findall(".//Field[TargetName='"+fieldName+"']")
        for node in nodes:
            try: # get the highest count value for this target name where the source name is valid
                nodecount = int(node.get('count'))
                if nodecount > count:
                    sname = node.find("SourceName").text
                    if sname in sourceNames or sname == '' or sname == None or sname == dla.noneName:
                        enode = node
                        count = nodecount
            except:
                pass

    if count > 0 and enode != None:
        addElements(xmlDoc,fNode,enode,fieldName)
    elif fieldName in sourceNames and enode == None:
        # no previous match but match on field name
        addFieldElement(xmlDoc,fNode,"SourceName",fieldName)
        addFieldElement(xmlDoc,fNode,"TargetName",fieldName)
        addFieldElement(xmlDoc,fNode,"Method",'Copy')
    elif nmupper in upperNames and enode == None:
        # logic for uppercase field name match, later the field will be renamed to essentially force a copy/rename unless something else set by user
        idx = upperNames.index(nmupper)
        addFieldElement(xmlDoc,fNode,"SourceName",sourceNames[idx]) # use the original source name
        addFieldElement(xmlDoc,fNode,"TargetName",fieldName) # use the original target name
        addFieldElement(xmlDoc,fNode,"Method",'Copy')
    else:
        # otherwise just add None
        addFieldElement(xmlDoc,fNode,"SourceName",dla.noneName)
        addFieldElement(xmlDoc,fNode,"TargetName",fieldName)
        addFieldElement(xmlDoc,fNode,"Method",'None')

def addElements(xmlDoc,fNode,enode,fieldName):
    for item in enode:
        strval = etree.tostring(item)
        xml = parseString(strval)
        removeBlanks(xml)
        xml.normalize()
        fNode.appendChild(xml.documentElement)

def removeBlanks(node):
    for x in node.childNodes:
        if x.nodeType == node.TEXT_NODE:
            if x.nodeValue:
                x.nodeValue = x.nodeValue.strip()
        elif x.nodeType == node.ELEMENT_NODE:
            removeBlanks(x)

def setSourceTarget(root,xmlDoc,name,dataset):
    # set source and target elements
    sourcetarget = xmlDoc.createElement(name)
    nodeText = xmlDoc.createTextNode(dataset)
    sourcetarget.appendChild(nodeText)
    root.appendChild(sourcetarget)
    
def setSourceFields(root,xmlDoc,fields):
    # Set SourceFields section of document
    sourceFields = xmlDoc.createElement("SourceFields")
    # add a blank entry at the start for "dla.noneName"
    fNode = xmlDoc.createElement("SourceField")
    sourceFields.appendChild(fNode)
    fNode.setAttribute("Name",dla.noneName)
        
    for field in fields:
        fNode = xmlDoc.createElement("SourceField")
        sourceFields.appendChild(fNode)
        fieldName = field.name[field.name.rfind(".")+1:]
        fNode.setAttribute("Name",fieldName)
        fNode.setAttribute("AliasName",field.aliasName)
        fNode.setAttribute("Type",field.type)
        #if field.length != None:
        fNode.setAttribute("Length",str(field.length))

    root.appendChild(sourceFields)

def setTargetFields(root,xmlDoc,fields):
    # Set TargetFields section of document
    targetFields = xmlDoc.createElement("TargetFields")
        
    for field in fields:
        fNode = xmlDoc.createElement("TargetField")
        targetFields.appendChild(fNode)
        fieldName = field.name[field.name.rfind(".")+1:]
        fNode.setAttribute("Name",fieldName)
        fNode.setAttribute("AliasName",field.aliasName)
        fNode.setAttribute("Type",field.type)
        #if field.length != None:
        fNode.setAttribute("Length",str(field.length))

    root.appendChild(targetFields)

def addFieldElement(xmlDoc,node,name,value):
    xmlName = xmlDoc.createElement(name)
    node.appendChild(xmlName)
    nodeText = xmlDoc.createTextNode(value)
    xmlName.appendChild(nodeText)

def getFields(desc,dataset):
    fields = []
    ignore = ['OBJECTID','GlobalID','GLOBALID','SHAPE','SHAPE_AREA','SHAPE_LENGTH','STLength()','StArea']
    for name in ['OIDFieldName','ShapeFieldName','LengthFieldName','AreaFieldName','GlobalID']:
        val = getFieldExcept(desc,name)
        if val != None:
            val = val[val.rfind('.')+1:] 
            ignore.append(val)
    for field in arcpy.ListFields(dataset):
        if field.name[field.name.rfind('.')+1:] not in ignore:
            fields.append(field)

    return fields

def getFieldExcept(desc,name):
    val = None
    try:
        val = eval("desc." + name)
    except:
        val = None
    return val

def writeDataSample(xmlDoc,root,sourceFields,sourceDataset,rowLimit):
    # get a subset of data for preview and other purposes
    i = 0
    data = xmlDoc.createElement("Data")
    root.appendChild(data)

    cursor = arcpy.da.SearchCursor(sourceDataset,sourceFields)
    i = 0
    #dla.addMessage(str(sourceFields))
    for row in cursor:
        if i == 10:
            return
        xrow = xmlDoc.createElement("Row")
        for f in range(0,len(sourceFields)):
            try:
                xrow.setAttribute(sourceFields[f],str(row[f])) # handles numeric values and simple strings
            except:
                try:
                    attrval = row[f].encode('utf-8', errors='replace').decode('utf-8',errors='backslashreplace') # handles non-utf-8 codes
                    xrow.setAttribute(sourceFields[f],attrval)
                except:
                    dla.showTraceback()
                    pass # backslashreplace should never throw a unicode decode error...
                
        data.appendChild(xrow)
        i += 1

    del cursor

if __name__ == "__main__":
    main()


##def automatchDocument(xmlFileName): couldn't get this to work in ArcGIS Pro
    
##    xml_input = etree.XML(open(xmlFileName, 'r').read())
##   xslt_root = etree.XML(open(matchxslt, 'r').read())
##    transform = etree.XSLT(xslt_root)
##   print(str(transform(xml_input)))
##    import win32com.client.dynamic
##    xslt = win32com.client.dynamic.Dispatch("Msxml2.DOMDocument.6.0")
##    xslt.async = 0
##    xslt.load(matchxslt)
##    xml = win32com.client.dynamic.Dispatch("Msxml2.DOMDocument.6.0")
##    xml.async = 0
##    xml.load(xmlFileName)
##    xml.setProperty("AllowDocumentFunction",True)
##    xslt.setProperty("AllowDocumentFunction",True)
##    output = ''
##    output = xml.transformNode(xslt)
##    xmlFile = xmlFileName.replace(".xml","1.xml")
##    xml.loadXML(output)
##    xml.save(xmlFileName)
