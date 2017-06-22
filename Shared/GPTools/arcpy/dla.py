﻿"""
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
# dla - Data Loading Assistant common functions
# Dec 2015
# ---------------------------------------------------------------------------
'''
Contains a collection of support functions used by dla tools to provide error handling and other supporting
functions, typically an expansion of underlying arcpy functions with a bit more logic and testing.

Generally functions return data or a True/False result depending on the situation and the arcpy functions.
'''
import sys,os,traceback,xml.dom.minidom,time,datetime,re,gc,arcpy

import json, urllib
import urllib.parse as parse
import urllib.request as request
from xml.dom.minidom import Document

debug = False # print field calculator messages.
startTime = time.localtime() # start time for a script
workspace = "dla.gdb" # default, override in script
successParameterNumber = 3 # parameter number to set at end of script to indicate success of the program
maxErrorCount = 20000 # max errors before a script will stop
_errCount = 0 # count the errors and only report things > maxRowCount errors...
_proxyhttp = None # "127.0.0.1:80" # ip address and port for proxy, you can also add user/pswd like: username:password@proxy_url:port
_proxyhttps = None # same as above for any https sites - not needed for these tools but your proxy setup may require it.
_project = None
_xmlFolder = None

_noneFieldName = '(None)'
_dirName = os.path.dirname( os.path.realpath( __file__) )
maxrows = 10000000

_ignoreFields = ['FID','OBJECTID','SHAPE','SHAPE_AREA','SHAPE_LENGTH','SHAPE_LEN','SHAPELENGTH','SHAPEAREA','STLENGTH()','STAREA()','RASTER','GLOBALID']
_ignoreFieldNames = ['OIDFieldName','ShapeFieldName','LengthFieldName','AreaFieldName','RasterFieldName','GlobalIDFieldName']
_CIMWKSP = 'CIMWKSP'
_lyrx = '.lyrx'
_http = 'http://'
_https = 'https://'
_sde = '.sde\\'
_gdb = '.gdb\\'
import string
import random
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# helper functions
def timer(input):
    # time difference
    return time.time() - input

def getDBTime():
    # format time val for db insert
    return getStrTime(time.localtime())

def getStrTime(timeVal):
    # get string time for a time value
    return time.strftime("%Y-%m-%d %H:%M:%S", timeVal)

def getTimeFromStr(timeStr):
    # get timeVal from a string
    return time.strptime(timeStr,"%d/%m/%Y %I:%M:%S %p")

def addMessage(val):
    # write a message to the screen
    try:
        if sys.stdin.isatty():
            #arcpy.AddMessage(str(val))
            print (str(val))
        else:
            arcpy.AddMessage(str(val))
            print(str(val))
    except:
        arcpy.AddMessage(str(val))

def addMessageLocal(val):
    # write a message to the screen
    try:
        if sys.stdin.isatty():
            print(str(val))
        else:
            arcpy.AddMessage(str(val))
    except:
        arcpy.AddMessage(str(val))

def addError(val):
    # add an error to the screen output
    #arcpy.AddMessage("Error: " + str(val))
    global _errCount
    _errCount += 1
    arcpy.AddError(str(val))

def writeFinalMessage(msg):
    global _errCount
    if msg != None:
        addMessage(str(msg))
    addMessage("Process completed with " + str(_errCount) + " errors")
    if _errCount > 0:
        addMessage("When any errors are encountered tools will report a general failure - even though the results may be still be satisfactory.")
        addMessage("Check the Geoprocessing log and errors reported along with the output data to confirm.")

def strToBool(s):
    # return a boolean for values like 'true'
    return s.lower() in ("yes", "true", "t", "1")

def showTraceback():
    # get the traceback object and print it out
    tBack = sys.exc_info()[2]
    # tbinfo contains the line number that the code failed on and the code from that line
    tbinfo = traceback.format_tb(tBack)
    tbStr = ""
    for i in range(0,len(tbinfo)):
        tbStr = tbStr + str(tbinfo[i])
    # concatenate information together concerning the error into a message string
    pymsg = "Python Error messages:\nTraceback Info:\n" + tbStr # + "Error Info:    " + str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
    # print messages for use in Python/PythonWin
    addError(pymsg)

def getFields(xmlFile):
    # get the list of datasets from XML doc
    dsTypes = ["Fields"]
    for atype in dsTypes:
        fields = getXmlElements(xmlFile,atype)
        if fields != []:
            return fields

def getIgnoreFieldNames(desc, include_globalID):

    ignore = _ignoreFields
    field_check = _ignoreFields
    if include_globalID:
        if 'GLOBALID' in field_check:
            field_check.pop(field_check.index('GLOBALID'))
    for name in field_check:
        val = getFieldByName(desc,name)
        if val != None:
            val = val[val.rfind('.')+1:]
            ignore.append(val)
    return ignore

def getFieldByName(desc,name):
    val = None
    try:
        val = eval('desc.' + name)
    except:
        val = None
    if val == '':
        val = None
    return val

def collect_text(node):
    # "A function that collects text inside 'node', returning that text."
    s = ""
    for child_node in node.childNodes:
        if child_node.nodeType == child_node.TEXT_NODE:
            s += child_node.nodeValue
        else:
            s += collect_text(child_node)
    return s

def getNodeValue(xmlDoc,nodeName):
    # get an xml node value
    node = xmlDoc.getElementsByTagName(nodeName)
    try:
        str = collect_text(node.item(0))
    except:
        str = ""
    return str

def getTextValue(node):
    try:
        str = collect_text(node)
    except:
        str = ""
    return str

def getArcpyErrorMessage():
    # parse out python exception content into the part after the "." - the message
    parts = str(sys.exc_value).split(".")
    if len(parts) == 1:
        retVal = parts[0]
    else:
        retVal = parts[1][1:] # first char after dot always appears to be newline char
    return retVal

def testSchemaLock(dataset):
    # test if a schema lock is possible
    res = arcpy.TestSchemaLock(dataset)
    return res

def cleanupGarbage():
    # cleanup python garbage
    for obj in gc.garbage:
        del obj # remove local reference so the node can be deleted
    del gc.garbage[:]
    for i in range(2):
        if debug == True:
            addMessageLocal('cleanup pass: ' + str(i))
        n = gc.collect()
        if debug == True:
            print('Unreachable objects:' + str(n))
            print('Remaining Garbage:' + str(gc.garbage))

def cleanup(inWorkspace):
    # general cleanup function
    cleanupGarbage()
    arcpy.ClearWorkspaceCache_management(inWorkspace)

def getCleanName(nameVal):
    # strip leading database prefix values
    cleanName = nameVal
    dotCount = nameVal.count(".")
    if dotCount > 0:
        cleanName = nameVal.split(".")[dotCount]
    return cleanName

def makeFeatureView(workspace,sourceFC,viewName,whereClause,xmlFields):
    # make a feature view using the where clause
    if arcpy.Exists(sourceFC):
        if arcpy.Exists(viewName):
            arcpy.Delete_management(viewName) # delete view if it exists
        desc = arcpy.Describe(sourceFC)
        fields = arcpy.ListFields(sourceFC)
        fStr = getViewString(fields,xmlFields)
        try:
            if str(whereClause).strip() == '':
                whereClause = None
            arcpy.MakeFeatureLayer_management(sourceFC, viewName, whereClause,None, fStr),
        except:
            showTraceback()
            if whereClause is None:
                whereClause = "(None)"
            addMessage("Error occured, where clause: " + whereClause)
        #addMessage("Feature Layer " + viewName + " created for " + str(whereClause))
    else:
        addError(sourceFC + " does not exist, exiting")

    if not arcpy.Exists(viewName):
        exit(-1)
    return(viewName)

def makeTableView(workspace,sourceTable,viewName,whereClause,xmlField):
    # make a table view using the where clause
    if arcpy.Exists(sourceTable):
        if arcpy.Exists(workspace + os.sep + viewName):
            arcpy.Delete_management(workspace + os.sep + viewName) # delete view if it exists
        desc = arcpy.Describe(sourceTable)
        fields = arcpy.ListFields(sourceTable)
        fStr = getViewString(fields,xmlField)
        arcpy.MakeTableView_management(sourceTable, viewName , whereClause, workspace, fStr)
    else:
        addError(sourceTable + " does not exist, exiting")

    if not arcpy.Exists(viewName):
        exit(-1)
    return(viewName)

def getViewString(fields,xmlFields):
    # get the string for creating a view
    viewStr = ""
    for field in fields: # drop any field prefix from the source layer (happens with map joins)
        thisFieldName = field.name[field.name.rfind(".")+1:]
        for xmlField in xmlFields:
            sourcename = getNodeValue(xmlField,"SourceName")
            if sourcename == thisFieldName:
                targetname = getNodeValue(xmlField,"TargetName")
                if sourcename != targetname and sourcename.upper() == targetname.upper():
                    # this is a special case where the source name is different case but the same string as the target
                    # need to create table so that the name matches the target name so there is no conflict later
                    thisFieldName = targetname

        thisFieldStr = field.name + " " + thisFieldName + " VISIBLE NONE;"
        viewStr += thisFieldStr

    if viewStr.endswith(';'):
        viewStr = viewStr[:-1]
    return viewStr

def getWhereClause(dataset):
    whereClause = ''
    try:
        whereClause = getNodeValue(dataset,"WhereClause")
    except:
        whereClause = ''
    if whereClause != '' and whereClause != ' ' and whereClause != None:
        addMessageLocal("Where '" + whereClause + "'")
    else:
        addMessageLocal("No Where Clause")

    return whereClause

def deleteRows(table,expr):
    # delete rows in dataset with an expression
    if debug:
        addMessageLocal(table)
    retcode = False
    targTable = getDatasetName(table)
    vname = targTable + "_ViewDelete"

    if arcpy.Exists(vname):
        arcpy.Delete_management(vname) # delete view if it exists

    arcpy.MakeTableView_management(table, vname ,  expr)
    arcpy.DeleteRows_management(vname)
    addMessageLocal("Existing " + targTable + " rows deleted ")
    try:
        arcpy.Delete_management(vname) # delete view if it exists
        retcode = True
    except:
        addMessageLocal("Could not delete view, continuing...")

    return retcode

def appendRows(sourceTable,targetTable,expr):
    # append rows in dataset with a where clause
    retcode = False

    sTable = getDatasetName(sourceTable)
    view = sTable + "_ViewAppend" + id_generator(size=3)
    if isTable(targetTable):
        deType = 'Table'
    else:
        deType = 'FeatureClass'

    view = makeView(deType,workspace,sourceTable,view,expr,[])

    numSourceFeat = arcpy.GetCount_management(view).getOutput(0)
    addMessage("Appending " + sTable + " TO " + getDatasetName(targetTable))

    if targetTable.lower().endswith(_lyrx):
        targetTable = getLayerFromString(targetTable)
    try:
        result = arcpy.Append_management(inputs=view,target=targetTable,schema_type='NO_TEST')
    except:
        msgs = arcpy.GetMessages()
        addError(msgs)
        return False

    addMessageLocal('Rows appended')

    numTargetFeat = arcpy.GetCount_management(targetTable).getOutput(0)
    addMessage(numSourceFeat + " features in source dataset")
    addMessage(numTargetFeat + " features in target dataset")
    msgs = arcpy.GetMessages()
    arcpy.AddMessage(msgs)
    retcode = True

    if int(numTargetFeat) != int(numSourceFeat):
        arcpy.AddMessage("WARNING: Different number of rows in target dataset, " + numTargetFeat )
    if int(numTargetFeat) == 0:
        addError("ERROR: 0 Features in target dataset")
        retcode = False

    return retcode

def listDatasets(gdb):
    # list all of the datasets and tables
    dsNames = []
    dsFullNames = []
    arcpy.env.workspace = gdb
    addMessageLocal("Getting list of Datasets from " + gdb)
    wsDatasets = arcpy.ListDatasets()
    wsTables = arcpy.ListTables()
    if wsDatasets:
        for fds in wsDatasets:
            desc = arcpy.Describe(fds)
            if desc.DatasetType == "FeatureDataset" :
                arcpy.env.workspace = desc.CatalogPath
                fcs = arcpy.ListFeatureClasses()
                for fc in fcs:
                    descfc = arcpy.Describe(fc)
                    if descfc.DatasetType == "FeatureClass":
                        dsNames.append(baseName(fc))
                        dsFullNames.append(desc.CatalogPath + os.sep + fc)
                        if debug:
                            arcpy.AddMessage(desc.CatalogPath + os.sep + fc)
            arcpy.env.workspace = gdb

    arcpy.env.workspace = gdb
    fcs = arcpy.ListFeatureClasses()
    for fClass in fcs:
        descfc = arcpy.Describe(fClass)
        if descfc.DatasetType == "FeatureClass":
            dsNames.append(baseName(fClass))
            dsFullNames.append(gdb + os.sep + fClass)
            if debug:
                arcpy.AddMessage(gdb + os.sep + fClass)

    arcpy.env.workspace = gdb
    for table in wsTables:
        descfc = arcpy.Describe(table)
        if descfc.DatasetType == "Table":
            dsNames.append(baseName(table))
            dsFullNames.append(gdb + os.sep + table)
            if debug:
                arcpy.AddMessage(gdb + os.sep + table)

    return([dsNames,dsFullNames])

def getFullName(searchName,names,fullNames):
    # find full name for searchName string
    try:
        # look for the matching name in target names
        t = names.index(searchName.upper())
        fullName = fullNames[t]
        return fullName
    except:
        # will get here if no match
        t = -1

    return ""

def baseName(name):
    # trim any database prefixes from table names
    if name.lower().endswith(_lyrx):
        name = name[:len(name)-len(_lyrx)]
    if name.count(".") > 0:
        return name.split(".")[name.count(".")].upper()
    else:
        return name.upper()

def getFieldValues(mode,fields,datasets):
    # get a list of field values, returns all values and the unique values.
    theValues = [] # unique list of values
    theDiff = [] # all values
    for dataset in datasets:
        name = dataset.getAttributeNode("name").nodeValue
        table = os.path.join(workspace,name)
        desc = arcpy.Describe(table)
        try:
            cursor = arcpy.SearchCursor(table)
            row = cursor.next()
        except (Exception, ErrorDesc):
            printMsg( "Unable to read the Dataset, Python error is: ")
            msg = str(getTraceback(Exception, ErrorDesc))
            printMsg(msg[msg.find("Error Info:"):])
            row = None

        numFeat = int(arcpy.GetCount_management(table).getOutput(0))
        addMessageLocal(table + ", " + str(numFeat) + " (get " + mode + ") features")
        progressUpdate = 1
        i=0
        if numFeat > 100:
            progressUpdate = numFeat/100
        arcpy.SetProgressor("Step","Getting " + mode + " values...",0,numFeat,progressUpdate)
        attrs = [f.name for f in arcpy.ListFields(table)]

        if row is not None:
            while row:
                i += 1
                if i % progressUpdate == 0:
                    arcpy.SetProgressorPosition(i)
                try:
                    for field in fields:
                        if field in attrs:
                            currentValue = row.getValue(field)
                            if mode.upper() == "UNIQUE":
                                if currentValue != None:
                                    try:
                                        theValues.index(currentValue) # if the current value is present
                                        theDiff.append(currentValue) # add to the list of differences if it is found
                                    except:
                                        theValues.append(currentValue) # else add the value if the first check fails.
                            elif mode.upper() == "ALL":
                                theValues.append(currentValue)
                except:
                    err = "Exception caught: unable to get field values"
                    addError(err)
                    logProcessError(row.getValue(field),sourceIDField,row.getValue(sourceIDField),"Cannot read",err)
                    theValues = []

                row = cursor.next()

        del cursor
        #arcpy.RefreshCatalog(table)

    return [theValues,theDiff]

def addDlaField(table,targetName,field,attrs,ftype,flength):
    # add a field to a dla Geodatabase
    if targetName == _noneFieldName:
        return True

    retcode = False
    try:
        attrs.index(targetName) # check if field exists, compare uppercase
        retcode = True
    except:
        try:
            upfield = False
            tupper = targetName.upper()
            for nm in attrs:
                nupper = nm.upper()
                if tupper == nupper and nupper not in _ignoreFields and nm != _noneFieldName and nupper != 'GLOBALID': # if case insensitive match, note GlobalID and others cannot be renamed
                    nm2 = nm + "_1"
                    retcode = arcpy.AlterField_management(table,nm,nm2)
                    retcode = arcpy.AlterField_management(table,nm2,targetName)
                    addMessage("Field altered: " + nm + " to " + targetName)
                    upfield = True
            if upfield == False and targetName != _noneFieldName:
                retcode = addField(table,targetName,ftype,flength)
                addMessage("Field added: " + targetName)
        except :
            showTraceback()
            for attr in attrs: # drop any field prefix from the source layer (happens with map joins)
                thisFieldName = attr[attr.rfind(".")+1:]
                if thisFieldName.upper() == targetName.upper():
                    addMessageLocal("WARNING: Existing field name '" + thisFieldName + "' conflicts with new field name '" + targetName + "'. Identical names with different case are not supported by databases!\n")
    return retcode

def addField(table,fieldName,fieldType,fieldLength):
    # add a field to a Geodatabase
    retcode = False
    if fieldLength == None:
        fieldLength = ""
    arcpy.AddField_management(table, fieldName, fieldType,fieldLength)
    retcode = True

    return retcode

def createGeodatabase():
    # Create a workspace - file GDB
    folder = workspace[:workspace.rfind(os.sep)]
    fgdb = workspace[workspace.rfind(os.sep)+1:]
    retcode = False
    try:
        arcpy.CreateFileGDB_management(folder,fgdb)
        retcode = True
        addMessageLocal("New Geodatabase created: " + workspace)
    except:
        showTraceback()
        addMessageLocal("Unable to create Geodatabase: " + folder + "\\" + fgdb)
    return retcode


def isDlaDocument(xmlDoc):
    # Is the first node SourceTargetMatrix in the XML document?
    node = None
    try:
        node = xmlDoc.getElementsByTagName("SourceTargetMatrix")
    except:
        pass
    if node:
       retVal = True
    else:
       retVal = False
    return retVal

def isPlaylistDocument(xmlDoc):
    # Is the first node a SourceTargetPlaylist?
    PlaylistNode = None
    try:
        PlaylistNode = xmlDoc.getElementsByTagName("SourceTargetPlaylist")
    except:
        pass
    if PlaylistNode:
       retVal = True
    else:
       retVal = False
    return retVal

def getRootElement(xmlDoc):
    # get the root element
    retDoc = None
    if isDlaDocument(xmlDoc):
        retDoc = xmlDoc.getElementsByTagName("SourceTarget")[0]
    elif isPlaylistDocument(xmlDoc):
        retDoc = xmlDoc.getElementsByTagName("SourceTargetPlaylist")[0]
    return retDoc

def getXmlElements(xmlFile,elemName):
    # get Xml elements from a file or files in a playlist
    retDoc = None
    xmlDoc = getXmlDoc(xmlFile)
    if isDlaDocument(xmlDoc):
        retDoc = xmlDoc.getElementsByTagName(elemName)
    elif isPlaylistDocument(xmlDoc):
        docs = xmlDoc.getElementsByTagName("File")
        for doc in docs:
            fileName = collect_text(doc)
            folder = xmlFile[:xmlFile.rfind(os.sep)]
            theFile = os.path.join(folder,fileName)
            if os.path.exists(theFile):
                xmlDoc2 = getXmlDoc(theFile)
                xmlNodes = xmlDoc2.getElementsByTagName(elemName)
                if retDoc == None:
                    retDoc = xmlNodes
                else:
                    for node in xmlNodes:
                        retDoc.append(node)
            else:
                addMessageLocal(theFile + " does not exist, continuing...")
    else:
        retDoc = None
    return retDoc

def convertDataset(dataElementType,sourceTable,workspace,targetName,whereClause):
    # convert a dataset
    if dataElementType == "DEFeatureClass":
        arcpy.FeatureClassToFeatureClass_conversion(sourceTable,workspace,targetName,whereClause)
    elif dataElementType == "DETable":
        arcpy.TableToTable_conversion(sourceTable,workspace,targetName,whereClause)


def makeView(deType,workspace,sourceTable,viewName,whereClause, xmlFields):
    # make a view
    view = None
    if deType.lower().endswith('table'):
        view = makeTableView(workspace,sourceTable,viewName, whereClause,xmlFields)
    if deType.lower().endswith('featureclass'):
        view = makeFeatureView(workspace,sourceTable,viewName, whereClause, xmlFields)

    return view

def exportDataset(sourceWorkspace,sourceName,targetName,dataset,xmlFields):
    # export a dataset
    result = True
    sourceTable = os.path.join(sourceWorkspace,sourceName)
    targetTable = os.path.join(workspace,targetName)
    addMessageLocal("Exporting dataset " + sourceTable)
    try:
        desc = arcpy.Describe(sourceTable)
        deType = desc.dataElementType
        whereClause = getWhereClause(dataset)
        viewName = sourceName + "_View" + id_generator(size=3)
        view = makeView(deType,workspace,sourceTable,viewName, whereClause,xmlFields)
        count = arcpy.GetCount_management(view).getOutput(0)
        addMessageLocal(str(count) + " source rows")
        convertDataset(deType,view,workspace,targetName,whereClause)
    except:
        err = "Failed to create new dataset " + targetName
        addError(err)
        logProcessError(sourceTable,sourceIDField,sourceName,targetName,err)
        result = False
    return result


def importDataset(sourceWorkspace,sourceName,targetName,dataset,xmlFields):
    # import a dataset
    result = True
    sourceTable = os.path.join(sourceWorkspace,sourceName)
    targetTable = os.path.join(workspace,targetName)
    addMessageLocal("Importing dataset " + sourceTable)

    try:
        whereClause = getWhereClause(dataset)
        if not arcpy.Exists(sourceTable):
            err = sourceTable + " does not exist"
            addError(err)
            logProcessError(sourceTable,sourceIDField,sourceName,targetName,err)
            return False
        if not arcpy.Exists(targetTable):
            err = targetTable + " does not exist"
            addError(err)
            logProcessError(targetTable,sourceIDField,sourceName,targetName,err)
            return False
        desc = arcpy.Describe(sourceTable)
        deType = desc.dataElementType
        viewName = sourceName + "_View" + id_generator(size=3)
        view = makeView(deType,workspace,sourceTable,viewName, whereClause, xmlFields)
        count = arcpy.GetCount_management(view).getOutput(0)
        addMessageLocal(str(count) + " source rows")
        arcpy.Append_management([view],targetTable, "NO_TEST","","")

    except:
        err = "Failed to import layer " + targetName
        addError(err)
        logProcessError(sourceTable,sourceIDField,sourceName,targetName,err)
        result = False
    return result

def deleteExistingRows(datasets):
    # delete existing rows in a dataset
    for dataset in datasets:
        name = dataset.getAttributeNode("targetName").nodeValue
        table = os.path.join(workspace,name)
        if arcpy.Exists(table):
            arcpy.DeleteRows_management(table)
            addMessageLocal("Rows deleted from: " + name)
        else:
            addMessageLocal(table + " does not exist")

def getFileList(inputFolder,fileExt,minTime): # get a list of files - recursively
    inputFiles = []
    if inputFolder.lower().endswith(".dwg") == True: # if the arg is a file instead of a folder just get that as a list
        inputFiles.append([os.path.dirname(inputFolder), os.path.basename(inputFolder)])
        addMessageLocal(os.path.dirname(inputFolder))
        addMessageLocal(os.path.basename(inputFolder))
        return inputFiles
    docList = os.listdir(inputFolder) #Get directory list for inputDirectory
    for doc in docList:
        docLow = doc.lower()
        ffile = os.path.join(inputFolder,doc)
        if docLow.endswith(fileExt.lower()):
            t = os.path.getmtime(ffile)
            modTime = datetime.datetime.fromtimestamp(t)
            if modTime > minTime:
                inputFiles.append([inputFolder,doc])
        elif os.path.isdir(ffile):
            newFiles = getFileList(ffile,fileExt,minTime)
            inputFiles = newFiles + inputFiles
    inputFiles = sorted(inputFiles)
    return(inputFiles)

def repairName(name):
    # layer names can have spaces and other chars that can't be used in table names
    nname = name.replace(" ","_")
    nname = nname.replace("-","_")

    return nname


def getSourceName(xmlDoc):
    path = getNodeValue(xmlDoc,"Source")
    name = getDatasetName(path)
    return name

def getTargetName(xmlDoc):
    path = getNodeValue(xmlDoc,"Target")
    name = getDatasetName(path)
    return name

def getDatasetName(path):
    fullname = ''
    if path.find("/") > -1:
        parts = path.split("/")
        fullname = parts[len(parts)-3]
    elif path.lower().endswith(_lyrx):
        fullname = getLayerSourceString(path)
    else:
        fullname = path[path.rfind(os.sep)+1:]
    trimname = baseName(fullname)
    name = repairName(trimname)

    return name

def setProject(xmlfile,projectFilePath):
    # set the current project to enable relative file paths for processing
    global _project
    global _xmlFolder
    try:
        if _xmlFolder == None:
            prj = getProject()
        _xmlFolder = os.path.dirname(xmlfile)
        if projectFilePath != None:
            if not os.path.exists(projectFilePath):
                projectFilePath = os.path.join(_xmlFolder,projectFilePath)
            if os.path.exists(projectFilePath):
                _project = arcpy.mp.ArcGISProject(projectFilePath)
            else:
                pass
                #Removed by Mike Miller 6/20/17, this message as relative path is by xml file and not project
                #addMessage(str(projectFilePath) + ' does not exist, continuing')


    except:
        #addError("Unable to set the current project, continuing")
        _project = None
        #_xmlFolder = None

    return _project

def getProject():
    global _project, _xmlFolder
    if _project == None:
        try:
            _project = arcpy.mp.ArcGISProject("CURRENT")
        except:
            #addMessage("Unable to obtain a reference to the current project, continuing")
            _project = None
    return _project

def getDatasetPath(xmlDoc,name):
    # check if file exists, then try to add project folder if missing
    pth = getNodeValue(xmlDoc,name)
    if pth.lower().startswith(_http) == True or pth.lower().startswith(_https) == True:
        return pth
    elif pth.endswith(_lyrx):
        # need to check os.path
        if not os.path.exists(pth):
            pth = os.path.join(_xmlFolder,pth)
            if not os.path.exists(pth):
                addError("Unable to locate layer path: " + pth)
    else:
        # need to check arcpy
        if not arcpy.Exists(pth):
            pth = os.path.join(_xmlFolder,pth)
            if not arcpy.Exists(pth):
                addError("Unable to locate dataset path: " + pth)
    return pth

def dropProjectPath(pth):
    # drop the project path from datasets to support relative paths and moving files between machines.
    if _xmlFolder != None:
        pth = pth.replace(_xmlFolder,'')
        if pth.startswith('\\'):
            pth = pth[1:]
    return pth

def dropXmlFolder(xmlfile,pth):
    # drop the xml file path from datasets to support relative paths and moving files between machines.
    dir = os.path.dirname(xmlfile)
    pth = pth.replace(dir,'')
    if pth.startswith('\\'):
      pth = pth[1:]
    return pth

def getMapLayer(layerName):
    name = layerName[layerName.rfind('\\')+1:]
    layer = None
    try:
        prj = getProject()
        maps = prj.listMaps("*")
        found = False
        for map in maps:
            if not found:
                lyrs = map.listLayers(name)
                for lyr in lyrs:
                    if lyr.name == name and not found:
                        if lyr.supports("DataSource"):
                            layer = lyr
                            found = True # take the first layer with matching name
    except:
        addMessage("Warning: Unable to get layer from maps")
        return None

    return layer

def getLayerPath(layer):
    # get the source data path for a layer
    pth = ''

    if isinstance(layer,arcpy._mp.LayerFile): # map layerFile as parameter
        pth = layer.filePath
        addMessage("Used .lyrx filePath as source")

    elif isinstance(layer, arcpy._mp.Layer): # map layer as parameter
        if layer.supports('dataSource'):
            pth = layer.dataSource
            addMessage("Used data source property")
        else:
            addError("Layer does not support the datasource property.  Please ensure you selected a layer and not a group layer")

    elif isinstance(layer, str) and layer.lower().endswith(_lyrx):
        layer = arcpy.mp.LayerFile(layer)
        try:
            pth = layer.filePath
            addMessage("Used .lyrx filePath as source")
        except:
            addMessage("Failed to use .lyrx filePath as source")

    else: # should be a string, check if feature layer string, then try to describe
        pth = repairLayerSourceUrl(layer,layer)
        if isFeatureLayerUrl(pth):
            return pth
        # else - not needed but else logic below
        try:
            desc = arcpy.Describe(layer) # dataset path/source as parameter
            pth = desc.catalogPath
        except:
            lyr = getMapLayer(layer) # layer name in the project/map - if not described then could be layer name
            if lyr != None and lyr.supports("DataSource"):
                pth = lyr.dataSource
                layer = lyr
            else:
                addError("Unable to get the DataSource for the layer: " + str(layer))
                return ''
    # handle special cases for layer paths (urls, CIMWKSP, layer ids with characters)
    pth = repairLayerSourceUrl(pth,layer)
    # handle special case for joined layers
    pth = getJoinedLayer(layer,pth)

    addMessage(pth)
    return pth

def getJoinedLayer(layer,pth):
    # if there is a join then save a layer file and return that path
    path = pth
    if isinstance(layer, str): # map layer as parameter
        layer = getMapLayer(layer)

    try:
        conn = layer.connectionProperties.get("source", None) # check for a joined layer
    except:
        conn = None

    if conn != None and not arcpy.Exists(path):

        lname = layer.name + _lyrx
        result = arcpy.MakeFeatureLayer_management(layer,lname)
        layer = result.getOutput(0)

        arcpy.env.overwriteOutput = True
        projFolder = os.path.dirname(getProject().filePath)
        lyrFile = os.path.join(projFolder,lname)
        arcpy.SaveToLayerFile_management(layer,lyrFile)

        desc = arcpy.Describe(lyrFile)
        path = desc.catalogPath

    return path

def getSDELayer(layer,pth):
    # if there is an SDE layer with CIMWORKSPACE save a layer and return the path
    path = pth
    if isinstance(layer, str): # map layer as parameter
        layer = getMapLayer(layer)

    if pth.startswith(_CIMWKSP):

        lname = layer.name + _lyrx
        result = arcpy.MakeFeatureLayer_management(layer,lname)
        layer = result.getOutput(0)

        arcpy.env.overwriteOutput = True
        projFolder = os.path.dirname(getProject().filePath)
        lyrFile = os.path.join(projFolder,lname)
        arcpy.SaveToLayerFile_management(layer,lyrFile)

        desc = arcpy.Describe(lyrFile)
        path = desc.catalogPath

    return path


def repairLayerSourceUrl(layerPath,lyr):
    # take a layer path or layer name and return the data source or repaired source
    # lyr parameter is here but only used in CIMWKSP case.
    # note that multiple if statements are used - and there can be a progression of path changes - not elif statements.
    if layerPath == "" or layerPath == None:
        return layerPath
    path = None
    layerPath = str(layerPath) # seems to be url object in some cases

    if layerPath.startswith('GIS Servers\\'):
        # turn into url
        layerPath = layerPath.replace("GIS Servers\\",'')
        if layerPath.startswith(_http) == True or layerPath.startswith(_https) == True:
            layerPath = layerPath # do nothing
        else:
            layerPath = _http + layerPath
        if layerPath.find('\\') > -1:
            path = layerPath.replace("\\",'/')
            layerPath = path

    if layerPath.startswith(_http) == True or layerPath.startswith(_https) == True: # sometimes get http/https path to start with, need to handle non-integer layerid in both cases
        # fix for non-integer layer ids
        parts = layerPath.split("/")
        lastPart = parts[len(parts)-1]
        ints = [int(s) for s in re.findall(r'\d+',lastPart )] # scan for the integer value in the string
        if ints != []:
            lastPart = str(ints[0])
        parts[len(parts) - 1] = lastPart
        path = "/".join(parts)

    if layerPath.startswith(_CIMWKSP):
        # create database connection and use that path
        connfile = getConnectionFile(lyr.connectionProperties)
        path = os.path.join(connfile + os.sep + layerPath[layerPath.rfind(">")+1:]) # </CIMWorkspaceConnection>fcname
        path = path.replace("\\\\","\\")
        #path = getSDELayer(lyr,layerPath)

    if path == None:
        # nothing done here
        path = layerPath

    return path

def getTempTable(name):
    tname = workspace + os.sep + name
    return tname

def setWorkspace():
    global workspace
    wsName = 'dla.gdb'
    ws = os.path.join(_dirName,wsName)
    if not arcpy.Exists(ws):
        arcpy.CreateFileGDB_management(_dirName,wsName)
    workspace = ws
    arcpy.env.workspace = workspace

def deleteWorkspace():
    global workspace
    if workspace != None and arcpy.Exists(workspace):
        arcpy.Delete_management(workspace)

def getLayerVisibility(layer,xmlFileName):
    fieldInfo = None
    xmlDoc = getXmlDoc(xmlFileName)
    targets = xmlDoc.getElementsByTagName("TargetName")
    names = [collect_text(node).upper() for node in targets]
    esrinames = _ignoreFields # ['SHAPE','OBJECTID','SHAPE_AREA','SHAPE_LENGTH','GlobalID','GLOBALID']
    desc = arcpy.Describe(layer)
    if desc.dataType == "FeatureLayer":
        fieldInfo = desc.fieldInfo
        for index in range(0, fieldInfo.count):
            name = fieldInfo.getFieldName(index)
            if name.upper() not in names and name.upper() not in esrinames:
                addMessage("Hiding Field: " + name)
                fieldInfo.setVisible(index,"HIDDEN")
    return fieldInfo

def refreshLayerVisibility():
    prj = getProject()
    maps = prj.listMaps("*")
    for map in maps:
        lyrs = map.listLayers("*")
        for lyr in lyrs:
            try:
                isviz = lyr.visible # flip viz to redraw layer.
                lyr.visible = True if isviz == False else False
                lyr.visible = isviz
            except:
                addMessage("Could not set layer visibility")


def getXmlDoc(xmlFile):
    # open the xmldoc and return contents
    xmlDoc = None
    try:
        xmlFile = xmlFile.strip("'")
        xmlFile = xmlFile.replace("\\","/")
        xmlDoc = xml.dom.minidom.parse(xmlFile) # parse from string
        #xmlFile = os.path.normpath(xmlFile)
    except:
        addError("Unable to open the xmlFile: " + xmlFile)

    return xmlDoc


def getSpatialReference(desc): # needs gp Describe object
    try:
        spref = str(desc.spatialReference.factoryCode)
    except:
        try:
            spref = desc.spatialReference.exportToString()
        except:
            arcpy.AddError("Could not get Spatial Reference")

    return spref

def setupProxy():
    proxies = {}
    if _proxyhttp != None:
        proxies['http'] = _http + _proxyhttp
        os.environ['http'] = _proxyhttp
    if _proxyhttps != None:
        proxies['https'] = _proxyhttps
        os.environ['https'] = _http + _proxyhttps
    if proxies != {}:
        proxy = urllib.ProxyHandler(proxies)
        opener = urllib.build_opener(proxy)
        urllib.install_opener(opener)

def getConnectionFile(connectionProperties):

    global _xmlFolder
    if _xmlFolder == None:
        addError("_xmlFolder has not been set in code, exiting")
    cp = connectionProperties['connection_info']
    srvr = getcp(cp,'server')
    inst = getcp(cp,'db_connection_properties')
    db = getcp(cp,'database')
    fname = (srvr+inst+db+".sde").replace(":","").replace("\\","")
    connfile = os.path.join(_xmlFolder,fname)
    if os.path.exists(connfile):
        os.remove(connfile)
    args = []
    args.append(out_folder_path=_xmlFolder)
    args.append(out_name=fname)
    if getcp(cp,'dbclient') != None:
        args.append(database_platform=getcp(cp,'dbclient'))
    args.append(instance=inst)
    if getcp(cp,'authentication_mode') != None:
        args.append(account_authentication=getcp(cp,'authentication_mode'))
    if getcp(cp,'username') != None:
        args.append(username=getcp(cp,'username'))
    if getcp(cp,'password') != None:
        args.append(username=getcp(cp,'password'))
    args.append(database=db)
    if getcp(cp,'schema') != None:
        args.append(username=getcp(cp,'schema'))
    if getcp(cp,'version') != None:
        args.append(username=getcp(cp,'version'))
    if getcp(cp,'date') != None:
        args.append(username=getcp(cp,'date'))

    arcpy.CreateDatabaseConnection_management (','.join(args))

    return connfile

def getcp(cp,name):
    retval = None
    try:
        retval = cp[name]
        if name.lower() == 'authentication_mode':
            if retval == 'OSA':
                retval = 'OPERATING_SYSTEM_AUTH'
            else:
                retval = 'DATABASE_AUTH'
        elif name.lower() == 'dbclient':
            srcs = ['','altibase','db2 for z/os','informix','netezza','oracle','postgresql','sap hana','sqlserver','teradata']
            targs = ['','ALTIBASE','DB2 for z/OS','Informix','Netezza','Oracle','PostgreSQL','SAP HANA','Sql Server','Teradata']
            try:
                retval = targs[srcs.index(retval.lower())]
            except:
                retval = retval
    except:
        pass
    return retval

def isTable(ds):
    desc = arcpy.Describe(ds)
    if desc.datasetType.lower() == 'table':
        return True
    else:
        return False

def getSpatialReferenceString(xmlDoc,lyrtype):
    sprefstr = ''
    # try factoryCode first
    try:
        sprefstr = getNodeValue(xmlDoc,lyrtype + "FactoryCode")
        if sprefstr == '':
            sprefstr = getNodeValue(xmlDoc,lyrtype + "SpatialReference")
    except:
        try:
            sprefstr = getNodeValue(xmlDoc,lyrtype + "SpatialReference")
        except:
            pass
    return sprefstr

def checkGlobalIdIndex(desc,gidName):
    valid = False
    for index in desc.indexes:
        try:
            if index.isUnique and index.fields[0].name == gidName: # index must be on correct field and unique
                valid = True
        except:
            pass
    return valid

def checkDatabaseTypes(source,target):
    # check database types - SQL source db and SQL gdb as target
    supported = False
    try:
        wsType = "None"
        smsg = 'Workspace type does not support preserving GlobalIDs'
        try:
            wsType = arcpy.Describe(source).dataSource
        except:
            wsType = arcpy.Describe(source[:source.rfind(os.sep)]).workspaceType # might be in a feature dataset

        if wsType != 'RemoteDatabase':
            addMessage(wsType + ' Source ' + smsg)
            supported = False
        else:
            supported = True

        wsType = "None"
        try:
            wsType = arcpy.Describe(target).workspaceType
        except:
            wsType = arcpy.Describe(target[:target.rfind(os.sep)]).workspaceType # might be in a feature dataset

        if wsType != 'RemoteDatabase':
            addMessage(wsType + ' Target ' + smsg)
            supported = False
        elif supported == True:
            supported = True
    except:
        supported = False

    return supported
def get_geodatabase_path(input_table):
    '''Return the Geodatabase path from the input table or feature class.
    :param input_table: path to the input table or feature class
    '''
    workspace = os.path.dirname(input_table)
    if [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(workspace)]:
        return workspace
    else:
        return os.path.dirname(workspace)
def checkDatabaseType(path):
    # check database types - SQL source db and SQL gdb as target
    supported = False
    try:
        if path.lower().startswith(_http):
            supported = True
        elif path.lower().startswith(_https):
            supported = True
        elif path.lower().count(_sde) == 1:
            supported = True
        elif path.lower().endswith(_lyrx):
            source = getLayerFromString(path)
            if source.dataSource.startswith(_CIMWKSP):
                supported = True
            elif arcpy.Exists(source.dataSource):
                path = get_geodatabase_path(input_table=source.dataSource)
                d = arcpy.Describe(path)
                if d.workspaceType == "RemoteDatabase":
                    supported = True
        elif path.lower().count(_gdb) == 1:
            supported = False
    except:
        supported = False

    return supported

def compareSpatialRef(xmlDoc):
    # compare source and target spatial references
    spatRefMatch = False
    sref = getSpatialReferenceString(xmlDoc,'Source')
    tref = getSpatialReferenceString(xmlDoc,'Target')

    if tref is None or sref is None:
        return spatRefMatch
    if tref == sref:
        spatRefMatch = True
    else:
        sref_obj = arcpy.SpatialReference()
        tref_obj = arcpy.SpatialReference()
        sref_obj.loadFromString(sref)
        tref_obj.loadFromString(tref)
        if sref_obj.factoryCode == tref_obj.factoryCode:
            spatRefMatch = True
        elif ';' in sref and ';' in tref and tref.split(';')[0] == sref.split(';')[0]:
            spatRefMatch = True

    return spatRefMatch
def processGlobalIds(xmlDoc):
    # logic check to determine if preserving globalids is possible
    process = False

    source = getDatasetPath(xmlDoc,'Source')
    descs = arcpy.Describe(source)

    target = getDatasetPath(xmlDoc,'Target')
    desct = arcpy.Describe(target)

    sGlobalId = getFieldByName(descs,'globalIDFieldName')
    tGlobalId = getFieldByName(desct,'globalIDFieldName')

    if sGlobalId != None and tGlobalId != None:
        addMessage('Source and Target datasets both have GlobalID fields')

        supportedWSs = checkDatabaseType(source)
        if not supportedWSs:
            addMessage("Source Workspace type prevents preserving GlobalIDs")
        supportedWSt = checkDatabaseType(target)
        if not supportedWSt:
            addMessage("Target Workspace type prevents preserving GlobalIDs")
        ids = checkGlobalIdIndex(descs,sGlobalId)
        idt = checkGlobalIdIndex(desct,tGlobalId)

        errmsg = 'Dataset does not have a unique index on GlobalID field, unable to preserve GlobalIDs'
        if not ids:
            addMessage('Source ' + errmsg)
        if not idt:
            addMessage('Target ' + errmsg)

        if ids and idt and supportedWSs and supportedWSt:
            process = True

    return process

def getStagingName(source,target):
    stgName = getDatasetName(source) + "_" + getDatasetName(target)
    return stgName

def removeStagingElement(xmlDoc):
    # remove staging element from xmlDoc
    if len(xmlDoc.getElementsByTagName('Staged')) > 0:
        root = xmlDoc.getElementsByTagName('Datasets')[0]
        nodes = root.getElementsByTagName('Staged')
        for node in nodes:
            root.removeChild(node)

    return xmlDoc

def insertStagingElement(xmlDoc):
    # insert an element to indicate that the data has been staged
    if len(xmlDoc.getElementsByTagName('Staged')) == 0:
        root = xmlDoc.getElementsByTagName('Datasets')[0]
        staged = xmlDoc.createElement("Staged")
        # set source and target elements
        nodeText = xmlDoc.createTextNode('true')
        staged.appendChild(nodeText)
        root.appendChild(staged)

    return xmlDoc

def isStaged(xmlDoc):
    # insert an element to indicate that the data has been staged
    if len(xmlDoc.getElementsByTagName('Staged')) > 0:
        staged = True
    else:
        staged = False

    return staged

def hasJoin(source):
    # counts table names in fields to determine if joined
    desc = arcpy.Describe(source)
    fc = desc.featureClass
    hasJoin = False
    tables = []
    for field in fc.fields:
        if field.name.find('.') > 0:
            val = field.name.split('.')[0]
            if val not in tables:
                tables.append(val)
    if len(tables) > 1:
        hasJoin = True

    return hasJoin

def checkIsLayerFile(val,valStr):
    # for layer file parameters the value passed in is a layer but the string version of the layer is a path to the lyrx file...
    if valStr.lower().endswith(_lyrx):
        return valStr
    else:
        return val

def getFieldIndexList(values,value):
    # get the index number of a field in a list - case insensitive
    for idx, val in enumerate(values):
        if val.upper() == value.upper():
            return idx

def getLayerSourceString(lyrPath):
    if isinstance(lyrPath,str) and lyrPath.lower().endswith(_lyrx):
        if not os.path.exists(lyrPath):
            addMessage(str(_xmlFolder))
            lyrPath = os.path.join(_xmlFolder,lyrPath)
        layer = arcpy.mp.LayerFile(lyrPath)
        fc = layer.listLayers()[0]
        return fc.dataSource

def getLayerFromString(lyrPath):
    if isinstance(lyrPath,str) and lyrPath.lower().endswith(_lyrx):
        layer = arcpy.mp.LayerFile(lyrPath)
        fc = layer.listLayers()[0]
        return fc
    else:
        return lyrPath

def getXmlDocName(xmlFile):
    # normalize and fix paths
    try:
        xmlFile = xmlFile.strip("'")
        xmlFile = os.path.normpath(xmlFile)
    except:
        addError("Unable to process file name: " + xmlFile)
    return xmlFile

def getReplaceBy(xmlDoc):
    # get the where clause using the xml document or return ''
    repl = xmlDoc.getElementsByTagName("ReplaceBy")[0]
    fieldName = getNodeValue(repl,"FieldName")
    operator = getNodeValue(repl,"Operator")
    value = getNodeValue(repl,"Value")
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

def isFeatureLayerUrl(url):
    # assume layer string has already had \ and GIS Servers or other characters switched to be a url
    parts = url.split('/')
    lngth = len(parts)
    if lngth > 2:
        try:
            # check for feature server text
            if parts[lngth-2] == 'FeatureServer':
                return True
        except:
            return False
    return False
