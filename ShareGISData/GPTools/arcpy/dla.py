
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

debug = False
startTime = time.localtime() # start time for a script
workspace = "dla.gdb" # default, override in script
successParameterNumber = 3 # parameter number to set at end of script to indicate success of the program
maxErrorCount = 20 # max errors before a script will stop
_errCount = 0 # count the errors and only report things > maxRowCount errors...
_proxyhttp = None # "127.0.0.1:80" # ip address and port for proxy, you can also add user/pswd like: username:password@proxy_url:port
_proxyhttps = None # same as above for any https sites - not needed for these tools but your proxy setup may require it.
_project = None


_dirName = os.path.dirname( os.path.realpath( __file__) )
maxrows = 10000000
noneName = '(None)'

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
            arcpy.AddMessage(str(val))
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

def getWorkspacePath(path):
    # get the path of the workspace
    workspace = arcpy.Describe(path) # preset
    dirName = os.path.dirname(path)
    if dirName and arcpy.Exists(dirName):
        dataset = arcpy.Describe(dirName)
    try:
        if dataset and dataset.datasetType == "FeatureDataset":
            # strip off last value to get workspace
            dirs = dirName.split(os.sep)
            dirs.pop()
            datasetStr = os.sep.join(dirs)
            workspace = arcpy.Describe(datasetStr) # use the next level up from feature dataset
    except:
        workspace = dataset # use the first dataset, datasetType fails on workspace values

    return workspace

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
            arcpy.MakeFeatureLayer_management(sourceFC, viewName , whereClause, workspace, fStr)
        except:
            showTraceback()
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

def xmakeFeatureViewForLayerx(workspace,sourceLayer,viewName,whereClause,xmlFields):
    # Process: Make Feature Layers - drop prefixes as needed
    #if arcpy.Exists(sourceLayer):
    #if arcpy.Exists(workspace + os.sep + viewName):
    #    arcpy.Delete_management(workspace + os.sep + viewName) # delete view if it exists

    desc = arcpy.Describe(sourceLayer)
    fields = arcpy.ListFields(sourceLayer)
    fLayerStr = getViewString(fields,xmlFields)
    arcpy.MakeFeatureLayer_management(sourceLayer, viewName, whereClause, workspace,fLayerStr)
    #else:
    #addError(sourceLayer + " does not exist, exiting")

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
    tname = table[table.rfind(os.sep) + 1:]
    #if arcpy.Exists(table):
    vname = tname + "_ViewDelete"
    if arcpy.Exists(vname):
        arcpy.Delete_management(vname) # delete view if it exists

    arcpy.MakeTableView_management(table, vname ,  expr)
    arcpy.DeleteRows_management(vname)
    addMessageLocal("Existing " + tname + " rows deleted ")
    try:
        arcpy.Delete_management(vname) # delete view if it exists
        retcode = True
    except:
        addMessageLocal("Could not delete view, continuing...")
    #else:
    #    addMessageLocal( "Dataset " + tname + " does not exist, skipping ")
    #    retcode = False
    return retcode

def appendRows(sourceTable,targetTable,expr):
    # append rows in feature class with a where clause
    workspace = sourceTable[:sourceTable.rfind("\\")]
    arcpy.env.Workspace = workspace
    if debug:
        addMessageLocal(tableName)
    retcode = False
    targTable = targetTable[targetTable.rfind("\\")+1:]
    sTable = sourceTable[sourceTable.rfind("\\")+1:]
    viewName = sTable + "_ViewAppend"
    desc = arcpy.Describe(targetTable)
    viewName = makeView(desc.dataElementType,workspace,sourceTable,viewName,expr,[])

    numSourceFeat = arcpy.GetCount_management(viewName).getOutput(0)
    addMessage("Appending " + sTable + " TO " + targTable)
    result = arcpy.Append_management(viewName,targetTable,"NO_TEST")
    addMessageLocal(targTable + " rows Appended ")

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
                        dsNames.append(nameTrimmer(fc))
                        dsFullNames.append(desc.CatalogPath + os.sep + fc)
                        if debug:
                            arcpy.AddMessage(desc.CatalogPath + os.sep + fc)
            arcpy.env.workspace = gdb

    arcpy.env.workspace = gdb
    fcs = arcpy.ListFeatureClasses()
    for fClass in fcs:
        descfc = arcpy.Describe(fClass)
        if descfc.DatasetType == "FeatureClass":
            dsNames.append(nameTrimmer(fClass))
            dsFullNames.append(gdb + os.sep + fClass)
            if debug:
                arcpy.AddMessage(gdb + os.sep + fClass)

    arcpy.env.workspace = gdb
    for table in wsTables:
        descfc = arcpy.Describe(table)
        if descfc.DatasetType == "Table":
            dsNames.append(nameTrimmer(table))
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

def nameTrimmer(name):
    # trim any database prefixes from table names
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
                if tupper == nupper and nupper != 'GLOBALID': # if case insensitive match, note GlobalID cannot be renamed
                    nm2 = nm + "_1"
                    retcode = arcpy.AlterField_management(table,nm,nm2)
                    retcode = arcpy.AlterField_management(table,nm2,targetName)
                    addMessage("Field altered: " + nm + " to " + targetName)
                    upfield = True
            if upfield == False:
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
    if deType == "DETable":
        view = makeTableView(workspace,sourceTable,viewName, whereClause,xmlFields)
    if deType == "DEFeatureClass":
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
        viewName = sourceName + "_View"
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
        viewName = sourceName + "_View"
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
    name = getDatasetName(xmlDoc,"Source")
    return name

def getTargetName(xmlDoc):
    name = getDatasetName(xmlDoc,"Target")
    return name

def getDatasetName(xmlDoc,doctype):
    layer = getNodeValue(xmlDoc,doctype)
    fullname = ''
    if layer.find("/") > -1:
        parts = layer.split("/")
        fullname = parts[len(parts)-3]
    else:
        fullname = layer[layer.rfind(os.sep)+1:]
    trimname = nameTrimmer(fullname)    
    name = repairName(trimname)

    return name

def getProject():
    global _project
    if _project == None:
        try:
            _project = arcpy.mp.ArcGISProject("CURRENT")
        except:
            addError("Unable to obtain a reference to the current project, exiting")
            _project = None
    return _project

def getLayer(layerName):
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
        addMessage("Unable to get layer from maps")
        return None
       
    return layer


def getLayerPath(pth): # requires string for layer argument

    if pth != None:
        if os.path.exists(pth[:pth.rfind(os.sep)]):
            # this is a link to a path so Ok
            pth = pth
        else:
            # this is feature service, layer name (layer in map), other non-filed-based
            try:
                desc = arcpy.Describe(pth)
                pth = desc.catalogPath
            except:
                pass
            pth = getLayerSourceUrl(pth)

        #dla.addMessage("Output path:" + pth)
    return pth

def getLayerSourceUrl(targetLayer):

    compLayer = targetLayer[targetLayer.rfind('\\')+1:]
    targetLayer = None

    lyr = getLayer(compLayer)
    if lyr != None and lyr.supports("DataSource"):
        targetLayer = lyr.dataSource
        found = True # take the first layer with matching name

    if targetLayer.startswith('GIS Servers\\'):
        targetLayer = targetLayer.replace("GIS Servers\\","http://")
        if targetLayer.find('\\') > -1:
            targetLayer = targetLayer.replace("\\",'/')
    elif targetLayer.startswith('CIMWKSP') and found == True:
        connfile = getConnectionFile(lyr.connectionProperties)
        targetLayer = os.path.join(connfile + os.sep + targetLayer[targetLayer.rfind(">")+1:]) # </CIMWorkspaceConnection>fcname

    if targetLayer.startswith('http'):
        parts = targetLayer.split("/")
        lastPart = parts[len(parts)-1]
        #if lastPart.startswith('L'): # Thought the Pro 1.3 bug involved 'L' prefix, seems like not always...
        #    suffix = parts[len(parts)-3]
        #    lastPart = lastPart[1:].replace(suffix,'')
        ints = [int(s) for s in re.findall(r'\d+',lastPart )]
        if ints != []:
            lastPart = str(ints[0])

        parts[len(parts) - 1] = lastPart
        targetLayer = "/".join(parts)
    #addMessage('layer='+targetLayer)
    return targetLayer


def getTempTable(name):
    tname = workspace + os.sep + name
    return tname

def doInlineAppend(source,target):
    # perform the append from a source table to a target table
    success = False
    if arcpy.Exists(target):
        numSourceFeat = arcpy.GetCount_management(source).getOutput(0)
        #addMessage("Truncating  "  + target)
        #arcpy.TruncateTable_management(target)
        addMessage("Appending " + source + " TO " + target)
        result = arcpy.Append_management(source,target, "NO_TEST")
        numTargetFeat = arcpy.GetCount_management(target).getOutput(0)
        addMessage(numSourceFeat + " features in source dataset")
        addMessage(numTargetFeat + " features in target dataset")
        msgs = arcpy.GetMessages()
        arcpy.AddMessage(msgs)
        success = True

        if int(numTargetFeat) != int(numSourceFeat):
            arcpy.AddMessage("WARNING: Different number of rows in Target table, " + numTargetFeat )
        if int(numTargetFeat) == 0:
            addError("ERROR: 0 Features in target dataset")
            success = False
                       
        if debug:
            addMessage("completed")
    else:
        addMessage("Target: " + target + " does not exist")
        success = False

    cleanupGarbage()
    return success

def setWorkspace():
    global workspace
    wsName = 'dla.gdb'
    ws = os.path.join(_dirName,wsName)
    if not arcpy.Exists(ws):
        arcpy.CreateFileGDB_management(_dirName,wsName)
    workspace = ws
    arcpy.env.workspace = workspace
    #if arcpy.env.scratchWorkspace == None: -- too many issues with locking using project/scratch gdb for intermediate data
     #workspace = arcpy.env.scratchGDB # just put it in temp for now - not project gdb
    #else:
    #    workspace = arcpy.env.scratchWorkspace

def deleteWorkspace():
    global workspace
    if workspace != None and arcpy.Exists(workspace):
        arcpy.Delete_management(workspace)

def getLayerVisibility(layer,xmlFileName):
    fieldInfo = None
    xmlDoc = getXmlDoc(xmlFileName)
    targets = xmlDoc.getElementsByTagName("TargetName")
    names = [collect_text(node).upper() for node in targets]
    esrinames = ['SHAPE','OBJECTID','SHAPE_AREA','SHAPE_LENGTH','GlobalID','GLOBALID']
    desc = arcpy.Describe(layer)
    if desc.dataType == "FeatureLayer":
        fieldInfo = desc.fieldInfo
        for index in range(0, fieldInfo.count):
            name = fieldInfo.getFieldName(index)
            if name.upper() not in names and name.upper() not in esrinames:
                addMessage("Hiding Field: " + name)
                fieldInfo.setVisible(index,"HIDDEN")
    return fieldInfo

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
                addMessage('Service REST capabilities: ' + capabilities)
                for item in checkList:
                    if capabilities.find(item) == -1:
                        addMessage('Service does not support: ' + item)
                        hasit = False
                    else:
                        addMessage('Service supports: ' + item)
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
        addMessage("Service Name: " + parts[7])
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
        addMessage('Error: No path available for layer')            
        return False
    #addMessage('Checking: ' + sourcePath)    
    if checkLayerIsService(sourcePath):
        #url = getLayerSourceUrl(sourcePath)
        url = sourcePath
        if isFeatureLayerUrl(url):
            data = arcpy.GetSigninToken()
            token = data['token']
            name = getServiceName(url)
            #print('Service',name)
            res = hasCapabilities(url,token,['Create','Delete'])
            if res != True and required == False:
                addMessage('WARNING: ' + name + ' does not have Create and Delete privileges')
                addMessage('Verify the service properties for: ' + url)
                addMessage('This tool might continue but other tools will not run until this is addressed')
            elif res != True and required == True:
                addError('WARNING: ' + name + ' does not have Create and Delete privileges')
                addMessage('Verify the service properties for: ' + url)
                addMessage('This tool will not run until this is addressed')
            return res
        else:
            addMessage(sourcePath + ' Does not appear to be a feature service layer, exiting. Check that you selected a layer not a service')
            return False
    else:
        return True

## end May 2016 section
    
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
        proxies['http'] = 'http://' + _proxyhttp
        os.environ['http'] = _proxyhttp
    if _proxyhttps != None:
        proxies['https'] = _proxyhttps
        os.environ['https'] = 'http://' + _proxyhttps
    if proxies != {}:
        proxy = urllib.ProxyHandler(proxies)
        opener = urllib.build_opener(proxy)
        urllib.install_opener(opener)

def getConnectionFile(connectionProperties):

    dir = os.path.dirname(os.path.realpath(__file__))
    cp = connectionProperties['connection_info']
    srvr = getcp(cp,'server')
    inst = getcp(cp,'db_connection_properties')
    db = getcp(cp,'database')
    fname = (srvr+inst+db+".sde").replace(":","").replace("\\","")
    connfile = os.path.join(dir,fname)
    if os.path.exists(connfile):
        os.remove(connfile)

    arcpy.CreateDatabaseConnection_management (out_folder_path=dir,
                                            out_name=fname,
                                            database_platform=getcp(cp,'dbclient'),
                                            instance=inst,
                                            account_authentication=getcp(cp,'authentication_mode'),
                                            username=getcp(cp,'username'),
                                            password=getcp(cp,'password'),
                                            database=db,
                                            schema=getcp(cp,'schema'),
                                            version=getcp(cp,'version'),
                                            date=getcp(cp,'date'))
    return connfile

def getcp(cp,name):
    retval = ""
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