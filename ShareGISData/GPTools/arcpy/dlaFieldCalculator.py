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
# dlaFieldCalculator.py
# ---------------------------------------------------------------------------

import os, sys, traceback, time, arcpy,  dla
import collections

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
try:
    dla.workspace = arcpy.GetParameterAsText(1) # scratch Geodatabase
except:
    dla.workspace = arcpy.env.scratchGDB
SUCCESS = 2 # parameter number for output success value

if dla.workspace == "" or dla.workspace == "#":
    dla.workspace = arcpy.env.scratchGDB

dla._errCount = 0

def main(argv = None):
    xmlDoc = dla.getXmlDoc(xmlFileName)
    targetName = dla.getTargetName(xmlDoc)
    success = calculate(xmlFileName,dla.workspace,targetName,False)
    if success == False:
        dla.addError("Errors occurred during field calculation")
    arcpy.SetParameter(SUCCESS, success)

def calculate(xmlFileName,workspace,name,ignore):

    dla.workspace = workspace
    success = True
    arcpy.ClearWorkspaceCache_management(dla.workspace)
    xmlDoc = dla.getXmlDoc(xmlFileName)
    dla.addMessage("Field Calculator: " + xmlFileName)
    arcpy.env.Workspace = dla.workspace
    table = dla.getTempTable(name)

    if not arcpy.Exists(table):
        dla.addError("Feature Class " + table + " does not exist, exiting")
        arcpy.SetParameter(SUCCESS, False)
        return
    if not arcpy.TestSchemaLock(table):
        dla.addError("Unable to obtain a schema lock for " + table + ", exiting")
        arcpy.SetParameter(SUCCESS, False)
        return -1

    desc = arcpy.Describe(table)
    fields = dla.getXmlElements(xmlFileName,"Field")
    sourceFields = dla.getXmlElements(xmlFileName,"SourceField")
    targetFields = dla.getXmlElements(xmlFileName,"TargetField")
    attrs = [f.name for f in arcpy.ListFields(table)]
    target_values = CaseInsensitiveDict()

    #Fix read into dict, using NM as key
    # at this point just getting the list of all target field names/types/lengths
    for target in targetFields:
        nm = target.getAttributeNode("Name").nodeValue
        target_values[nm] = dict(ftype = target.getAttributeNode("Type").nodeValue,
                                 flength = target.getAttributeNode("Length").nodeValue)


    for field in fields:
        arcpy.env.Workspace = dla.workspace
        targetName = dla.getNodeValue(field,"TargetName")
        sourceName = dla.getNodeValue(field,"SourceName")

        ftype = "String"
        flength = "50"
        if nm in target_values:
            ftype = target_values[nm]['ftype']
            flength = target_values[nm]['flength']
        # make sure the field exists in the field calculator dataset, this will include all source and target fields.
        dla.addDlaField(table,targetName,field,attrs,ftype,flength)
    
    allFields = sourceFields + targetFields # this should be the same as the dataset fields at this point
    desc = arcpy.Describe(table)
    layerNames = []
    names = []
    ftypes = []
    lengths = []
    ignore = dla.getIgnoreFieldNames(desc) # gdb system fields that will be handled automatically and cannot be calculated
    ignore = [nm.upper() for nm in ignore]

    for field in desc.fields: # get the uppercase names for everything that exists in the dataset
        if field.name.upper() not in ignore:
            layerNames.append(field.name.upper())

    for field in allFields: # loop through everything that might exist
        nm = field.getAttributeNode("Name").nodeValue.replace('.','_') #  handle joins and remaining . in field names
        if nm != dla._noneFieldName and nm.upper() not in ignore and nm.upper() in layerNames:  # ignore the None and ignore fields and names not in the dataset
            idx = dla.getFieldIndexList(names, nm) 
            if idx is None: # if the name is not already in the list
                names.append(nm)
                typ = field.getAttributeNode("Type").nodeValue
                leng = field.getAttributeNode("Length").nodeValue
                ftypes.append(typ)
                lengths.append(leng)

            #FIXME : Steve, was not sure why you were capturing an error here, and then doing something # from Steve - was looking for names that actually exist in the dataset and are not gdb system fields. No guarantee Xml matches dataset
            #try:
                #names.index(nm)
            #except:
                #names.append(nm)
                #typ = field.getAttributeNode("Type").nodeValue
                #leng = field.getAttributeNode("Length").nodeValue
                #ftypes.append(typ)
                #lengths.append(leng)
    retVal = setFieldValues(table,fields,names,ftypes,lengths)
    if retVal == False:
        success = False
    arcpy.ClearWorkspaceCache_management(dla.workspace)
    dla.cleanupGarbage()

    arcpy.ResetProgressor()
    if ignore == True:
        success = True
    return success

def calcValue(row,names,calcString):
    # calculate a value based on source fields and/or other expressions
    outVal = ""
    calcList = calcString.split("|")
    for strVal in calcList:
        if strVal in names:
            try:
                fidx = dla.getFieldIndexList(names,strVal)
                if str(row[fidx]) != row[fidx]:
                    outVal += str(row[fidx])
                else:
                    outVal += '"' + str(row[fidx]) + '"'

            except:
                outVal += strVal
        else:
            outVal += strVal
    if len(calcList) == 1 and outVal == '':
        outVal = calcList[0]
    try:
        if(outVal != "" and outVal != None):
            outVal = eval(outVal)
    except:
        dla.addMessage("Error evaluating:" + outVal)
        dla.showTraceback()
        dla.addError("Error calculating field values:" + outVal)
        outVal = None
    return outVal

def setFieldValues(table,fields,names,ftypes,lengths):
    # from source xml file match old values to new values to prepare for append to target geodatabase
    success = False
    row = None
    try:
        updateCursor = arcpy.da.UpdateCursor(table,names)

        result = arcpy.GetCount_management(table)
        numFeat = int(result.getOutput(0))
        dla.addMessage(table + ", " + str(numFeat) + " features")
        i = 0
        arcpy.SetProgressor("Step","Calculating " + table + "...",0,numFeat,getProgressUpdate(numFeat))

        for row in updateCursor:
            success = True
            if dla._errCount > dla.maxErrorCount:
                dla.addError("Exceeded max number of errors in dla.maxErrorCount: " + str(dla.maxErrorCount))
                return False
            if i > dla.maxrows:
                dla.addError("Exceeded max number of rows supported in dla.maxrows: " + str(dla.maxrows))
                return True
            i = i + 1
            setProgressor(i,numFeat)

            for field in fields:
                method = "None"
                sourceName = dla.getNodeValue(field,"SourceName").replace('.','_')
                targetName = dla.getNodeValue(field,"TargetName").replace('.','_')

                targetValue = getTargetValue(row,field,names,sourceName,targetName)
                sourceValue = getSourceValue(row,names,sourceName,targetName)
                method = dla.getNodeValue(field,"Method").replace(" ","")
                try:
                    fnum = dla.getFieldIndexList(names,targetName)
                except:
                    fnum = None # defensive check to skip fields that do not exist even though they are listed in Xml

                if fnum != None:
                    if method == "None" or (method == "Copy" and sourceName == '(None)'):
                        method = "None"
                        val = None
                    elif method == "Copy":
                        val = sourceValue
                    elif method == "DefaultValue":
                        val = dla.getNodeValue(field,"DefaultValue")
                    elif method == "SetValue":
                        val = dla.getNodeValue(field,"SetValue")
                    elif method == "ValueMap":
                        val = getValueMap(row,names,sourceValue,field)
                    elif method == "DomainMap":
                        val = getDomainMap(row,names,sourceValue,field)
                    elif method == "ChangeCase":
                        case = dla.getNodeValue(field,method)
                        expression = getChangeCase(sourceValue,case)
                        val = getExpression(row,names,expression)
                    elif method == "Concatenate":
                        val = getConcatenate(row,names,field)
                    elif method == "Left":
                        chars = dla.getNodeValue(field,"Left")
                        val = getSubstring(sourceValue,"0",chars)
                    elif method == "Right":
                        chars = dla.getNodeValue(field,"Right")
                        val = getSubstring(sourceValue,len(str(sourceValue))-int(chars),len(str(sourceValue)))
                    elif method == "Substring":
                        start = dla.getNodeValue(field,"Start")
                        length = dla.getNodeValue(field,"Length")
                        val = getSubstring(sourceValue,start,length)
                    elif method == "Split":
                        splitter = dla.getNodeValue(field,"SplitAt")
                        splitter = splitter.replace("(space)"," ")
                        part = dla.getNodeValue(field,"Part")
                        val = getSplit(sourceValue,splitter,part)
                    elif method == "ConditionalValue":
                        sname = dla.getNodeValue(field,"SourceName")
                        oper = dla.getNodeValue(field,"Oper")
                        iif = dla.getNodeValue(field,"If")
                        if iif != " " and type(iif) == 'str':
                            for name in names:
                                if name in iif:
                                    iif = iif.replace(name,"|"+name+"|")
                        tthen = dla.getNodeValue(field,"Then")
                        eelse = dla.getNodeValue(field,"Else")
                        for name in names:
                            if name in eelse:
                                eelse = eelse.replace(name,"|"+name+"|")
                        expression = "|" + tthen + "| " + " if |" + sname + "| " + oper + " |" + iif + "| else " + eelse
                        val = getExpression(row,names,expression)
                    elif method == "Expression":
                        expression = dla.getNodeValue(field,method)
                        for name in names:
                            expression = expression.replace(name,"|" + name + "|")
                        val = getExpression(row,names,expression)
                    # set field value
                    if method != "None":
                        newVal = getValue(names,ftypes,lengths,targetName,targetValue,val)
                        row[fnum] = newVal

                        #dla.addMessage(targetName + ':' + str(newVal)  + ':' + str(targetValue))
            try:
                updateCursor.updateRow(row)
                #printRow(row,names)
            except:
                dla._errCount += 1
                success = False
                err = "Exception caught: unable to update row"
                printRow(row,names)
                dla.showTraceback()
                dla.addError(err)
    except:
        dla._errCount += 1
        success = False
        err = "Exception caught: unable to update dataset"
        if row != None:
            printRow(row,names)
        dla.showTraceback()
        dla.addError(err)

    finally:
        del updateCursor
        dla.cleanupGarbage()
        arcpy.ResetProgressor()

    return success


def getSplit(sourceValue,splitter,part):

    strVal = None
    try:
        strVal = sourceValue.split(str(splitter))[int(part)]
    except:
        pass

    return strVal

def getSubstring(sourceValue,start,chars):
    strVal = None
    try:
        start = int(start)
        chars = int(chars)
        strVal = str(sourceValue)[start:chars]
    except:
        pass
    return strVal

def getChangeCase(sourceValue,case):
    expression = None
    lcase = case.lower()
    if lcase.startswith("upper"):
        case = ".upper()"
    elif lcase.startswith("lower"):
        case = ".lower()"
    elif lcase.startswith("title"):
        case = ".title()"
    elif lcase.startswith("capitalize"):
        case = ".capitalize()"
    expression = '"' + sourceValue + '"' + case
    return expression


def getConcatenate(row,names,field):
    concatFields = field.getElementsByTagName("cField")
    sep = field.getElementsByTagName("Separator")[0]
    sep = dla.getTextValue(sep)
    sep = sep.replace("(space)"," ")
    concat = []
    for cfield in concatFields:
        node = cfield.getElementsByTagName("Name")
        nm = dla.getTextValue(node[0])
        nameidx = dla.getFieldIndexList(names,nm)
        if row[nameidx] != None:
            concat.append(str(row[nameidx]))
    concatStr = concatRepair(concat,sep)
    if concatStr == "":
        concatStr = None
    return concatStr

def concatRepair(concat,sep):
    stripvals = [None,""," "]
    nothing = False
    items = []
    for item in concat:
        if item not in stripvals:
            items.append(item)

    concatStr = sep.join(items)
    return concatStr

def getValueMap(row,names,sourceValue,field):

    # run value map function for a row
    valueMaps = field.getElementsByTagName("ValueMap")
    newValue = None
    found = False
    otherwise = None
    for valueMap in valueMaps:
        try:
            otherwise = valueMap.getElementsByTagName("Otherwise")[0]
            otherwise = dla.getTextValue(otherwise)
        except:
            otherwise = None
        sourceValues = []
        sourceValues = valueMap.getElementsByTagName("sValue")
        targetValues = []
        targetValues = valueMap.getElementsByTagName("tValue")
        i = 0
        for val in sourceValues:
            sValue = dla.getTextValue(val)
            try:
                sourceTest = float(sValue)
            except ValueError:
                sourceTest = str(sValue)
                if sourceTest == '' or sourceTest == 'None':
                    sourceTest = None
            #if mapExpr and mapExpr != "":
            #    sourceValue = calcValue(row,names,mapExpr)
            if sourceValue == sourceTest or sourceValue == sValue: # this will check numeric and non-numeric equivalency for current values in value maps
                found = True
                try:
                    newValue = dla.getTextValue(targetValues[i])
                except:
                    dla._errCount += 1
                    success = False
                    err = "Unable to map values for " + sourceValue + ", value = " + str(newValue)
                    dla.showTraceback()
                    dla.addError(err)
                    print(err)
            i = i + 1
    if not found:
        if str(otherwise) != "None" or otherwise == None:
            if otherwise.startswith("\n ") or otherwise == "":
                otherwise = None
            newValue = otherwise
        else:
            dla._errCount += 1
            success = False
            err = "Unable to find map value (otherwise) for " + str(targetName) + ", value = " + str(sourceValue)
            dla.addError(err)
    return newValue

def getDomainMap(row,names,sourceValue,field):

    # run domain map function for a row
    valueMaps = field.getElementsByTagName("DomainMap")
    newValue = None
    found = False
    otherwise = None
    for valueMap in valueMaps:
        sourceValues = []
        sourceValues = valueMap.getElementsByTagName("sValue")
        targetValues = []
        targetValues = valueMap.getElementsByTagName("tValue")
        i = 0
        for val in sourceValues:
            sValue = dla.getTextValue(val)
            try:
                sourceTest = float(sValue)
            except ValueError:
                sourceTest = str(sValue)
                if sourceTest == '' or sourceTest == 'None':
                    sourceTest = None
            if sourceValue == sourceTest or sourceValue == sValue: # this will check numeric and non-numeric equivalency for current values in maps
                found = True
                try:
                    newValue = dla.getTextValue(targetValues[i])
                except:
                    dla._errCount += 1
                    success = False
                    err = "Unable to map values for " + sourceValue + ", value = " + str(newValue)
                    dla.showTraceback()
                    dla.addError(err)
                    print(err)
            i = i + 1

    return newValue

def getExpression(row,names,expression):

    calcNew = None
    try:
        calcNew = calcValue(row,names,expression)
        #setValue(row,targetName,sourceValue,calcNew,idx)
    except:
        err = "Exception caught: unable to set value for expression=" + expression
        dla.showTraceback()
        dla.addError(err)
        print(err)
        dla._errCount += 1
    return calcNew

def setProgressor(i,numFeat):
    if i % getProgressUpdate(numFeat) == 0:
        dla.addMessage(str(i) + " processed")
    if i % getProgressUpdate(numFeat) == 0:
        arcpy.SetProgressorPosition(i)

def getProgressUpdate(numFeat):
    if numFeat > 1000:
        progressUpdate = 1000 #int(numFeat/500)
    else:
        progressUpdate = 100
    return progressUpdate

def printRow(row,names):
    r = 0
    for item in row:
        msg = str(names[r]) + ":" + str(item) + ' #' + str(r)
        print(msg)
        arcpy.AddMessage(msg)
        r += 1

def getTargetValue(row,field,names,sourceName,targetName):
    # get the current value for the row/field
    targetValue = None
    if sourceName != "" and not sourceName.startswith("*") and sourceName != "(None)":
        try:
            if sourceName != targetName and sourceName.upper() == targetName.upper():
                # special case for same name but different case - should already have the target name from extract functions
                targetValue = row[dla.getFieldIndexList(names,sourceName)]
            else:
                targetValue = row[dla.getFieldIndexList(names,targetName)]
        except:
            targetValue = None # handle the case where the source field does not exist or is blank

    return targetValue

def getSourceValue(row,names,sourceName,targetName):
    try:
        sourceValue = row[dla.getFieldIndexList(names,sourceName)]
    except:
        if sourceName != targetName and sourceName.upper() == targetName.upper():
            sourceValue = row[dla.getFieldIndexList(names,targetName)]
        else:
            sourceValue = None
    return sourceValue

def getValue(names,ftypes,lengths,targetName,targetValue,val):
    retVal = val # init to the value calculated so far. This function will alter as needed for field type
    try:
        idx = dla.getFieldIndexList(names,targetName)
        if retVal == 'None':
            retVal = None
        if retVal != targetValue:
            if ftypes[idx] == 'Integer' or ftypes[idx] == 'Double':
                # if the type is numeric then try to cast to float
                if str(val) == 'None':
                    retVal = None
                else:
                    try:
                        valTest = float(val)
                        retVal = val
                    except:
                        err = "Exception caught: unable to cast " + targetName + " to " + ftypes[idx] + "  : '" + str(val) + "'"
                        dla.addError(err)
                        dla._errCount += 1
            elif ftypes[idx] == 'String':
                # if a string then cast to string or encode utf-8
                if type(val) == 'str':
                    retVal = val.encode('utf-8', errors='replace').decode('utf-8',errors='backslashreplace') # handle unicode
                else:
                    retVal = str(val)
                # check length to make sure it is not too long.
                if len(retVal) > int(lengths[idx]):
                    err = "Exception caught: value length > field length for " + targetName + "(Length " + str(lengths[idx]) + ") : '" + str(retVal) + "'"
                    dla.addError(err)
                    dla._errCount += 1

            else:
                retVal = val
    except:
        err = "Exception caught: unable to get value for value=" + str(val) + " fieldname=" + targetName
        dla.showTraceback()
        dla.addError(err)
        dla._errCount += 1

    return retVal

class CaseInsensitiveDict(collections.MutableMapping):
    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[self.__keystring(key).lower()] = (key, value)
    def __keystring(self, key):
        return str(key)
    def __getitem__(self, key):

        return self._store[self.__keystring(key).lower()][1]

    def __delitem__(self, key):
        del self._store[self.__keystring(key).lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, collections.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


if __name__ == "__main__":
    main()
