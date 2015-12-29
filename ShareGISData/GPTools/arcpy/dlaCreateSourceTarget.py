## dlaCreateSourceTarget.py - take a list of 2 datasets and export a Configuration file
## December 2015
## Loop through the source and target datasets and write an xml document

import os, sys, traceback, time, xml.dom.minidom, arcpy
from xml.dom.minidom import Document
import re

# Local variables...
debug = False
# Parameters
sourceDataset = arcpy.GetParameterAsText(0) # source dataset to analyze
targetDataset = arcpy.GetParameterAsText(1) # target dataset to analyze
xmlFileName = arcpy.GetParameterAsText(2) # output file name argument

if not xmlFileName.lower().endswith(".xml"):
    xmlFileName = xmlFileName + ".xml"
successParameterNumber = 3
xmlStr = ""

def main(argv = None):
    global sourceDataset,targetDataset,xmlFileName   
    print(sourceDataset)
    print(targetDataset)
    print(xmlFileName)
    createDlaFile(sourceDataset,targetDataset,xmlFileName)

def createDlaFile(sourceDataset,targetDataset,xmlFileName):

    writeDocument(sourceDataset,targetDataset,xmlFileName)
    return True

def writeDocument(sourceDataset,targetDataset,xmlFileName):

    desc = arcpy.Describe(sourceDataset)
    descT = arcpy.Describe(targetDataset)

    xmlDoc = Document()
    root = xmlDoc.createElement('SourceTargetMatrix')
    xmlDoc.appendChild(root)
    root.setAttribute("version",'1.1')
    root.setAttribute("xmlns:esri",'http://www.esri.com')

    dataset = xmlDoc.createElement("Datasets")
    root.appendChild(dataset)
    setSourceTarget(dataset,xmlDoc,"Source",desc.catalogPath)
    setSourceTarget(dataset,xmlDoc,"Target",descT.catalogPath)
    setSourceTarget(dataset,xmlDoc,"ReplaceBy","")
    
    fieldroot = xmlDoc.createElement("Fields")
    root.appendChild(fieldroot)

    fields = getFields(descT,targetDataset)
    sourceFields = getFields(desc,sourceDataset)
    sourceNames = [field.name[field.name.rfind(".")+1:] for field in sourceFields]
    #try:
    for field in fields:
        fNode = xmlDoc.createElement("Field")
        fieldroot.appendChild(fNode)
        fieldName = field.name[field.name.rfind(".")+1:]
        method = 'None'
        if fieldName in sourceNames:
            addFieldElement(xmlDoc,fNode,"SourceName",fieldName)
            method = 'Copy'
        else:
            addFieldElement(xmlDoc,fNode,"SourceName","(None)") #"*"+fieldName+"*") magic needed here...

        addFieldElement(xmlDoc,fNode,"TargetName",fieldName)
        addFieldElement(xmlDoc,fNode,"Method",method)

    # write the source field values
    setSourceFields(root,xmlDoc,sourceFields)
    setTargetFields(root,xmlDoc,fields)
    # Should add a template section for value maps, maybe write domains...
    # could try to preset field mapping and domain mapping...

    # add some data to the document
    writeDataSample(xmlDoc,root,sourceNames,sourceDataset,10)
    # write it out
    xmlStr = xmlDoc.toprettyxml()
    xmlDoc.writexml( open(xmlFileName, 'w'),indent="  ",addindent="  ",newl='\n')
    xmlDoc.unlink()   

def setSourceTarget(root,xmlDoc,name,dataset):
    # set source and target elements
    sourcetarget = xmlDoc.createElement(name)
    nodeText = xmlDoc.createTextNode(dataset)
    sourcetarget.appendChild(nodeText)
    root.appendChild(sourcetarget)
    
def setSourceFields(root,xmlDoc,fields):
    # Set SourceFields section of document
    sourceFields = xmlDoc.createElement("SourceFields")
    # add a blank entry at the start for "(None)"
    fNode = xmlDoc.createElement("SourceField")
    sourceFields.appendChild(fNode)
    fNode.setAttribute("Name","(None)")
        
    for field in fields:
        fNode = xmlDoc.createElement("SourceField")
        sourceFields.appendChild(fNode)
        fieldName = field.name[field.name.rfind(".")+1:]
        fNode.setAttribute("Name",fieldName)
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
    ignore = []
    for name in ["OIDFieldName","ShapeFieldName","LengthFieldName","AreaFieldName","GlobalID"]:
        val = getFieldExcept(desc,name)
        if val != None:
            val = val[val.rfind(".")+1:]
            ignore.append(val)
    for field in arcpy.ListFields(dataset):
        if field.name[field.name.rfind(".")+1:] not in ignore:
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

    for row in cursor:
        if i == 10:
            return
        xrow = xmlDoc.createElement("Row")
        for f in range(0,len(sourceFields)):
            xrow.setAttribute(sourceFields[f],str(row[f]))
        data.appendChild(xrow)
        i += 1

    del cursor

if __name__ == "__main__":
    main()
