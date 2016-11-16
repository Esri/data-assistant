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

    for field in fields:
        arcpy.env.Workspace = dla.workspace
        targetName = dla.getNodeValue(field,"TargetName")
        sourceName = dla.getNodeValue(field,"SourceName")
            
        ftype = "String"
        length = "50"
        for target in targetFields:
            nm = target.getAttributeNode("Name").nodeValue
            if  nm == targetName:
                ftype = target.getAttributeNode("Type").nodeValue
                length = target.getAttributeNode("Length").nodeValue
        # uppercase compare, later need to check for orig/upper name for calc
        #ups = [nm.upper() for nm in attrs]
        dla.addDlaField(table,targetName,field,attrs,ftype,length)

    allFields = sourceFields + targetFields
    desc = arcpy.Describe(table)
    layerNames = []
    names = []
    ftypes = []
    lengths = []
    ignore = ['FID','OBJECTID','GLOBALID','SHAPE','SHAPE_AREA','SHAPE_LENGTH','SHAPE_LEN','STLENGTH()','STAREA()']
    for name in ['OIDFieldName','ShapeFieldName','LengthFieldName','AreaFieldName','GlobalID']:
        try:
            val = eval("desc." + name)
            val = val[val.rfind('.')+1:] 
            ignore.append(val).upper()
        except:
            pass

    for field in desc.fields:
        if field.name.upper() not in ignore:
            layerNames.append(field.name.upper())

    for field in allFields:
        nm = field.getAttributeNode("Name").nodeValue
        if nm != dla.noneName and nm.upper() not in ignore and nm.upper() in layerNames:
            try:
                names.index(nm)
            except:
                names.append(nm)
                typ = field.getAttributeNode("Type").nodeValue
                leng = field.getAttributeNode("Length").nodeValue      
                ftypes.append(typ)
                lengths.append(leng)

    retVal = setFieldValues(table,fields,names,ftypes,lengths)
    if retVal == False:
        success = False
    arcpy.ClearWorkspaceCache_management(dla.workspace)
    dla.cleanupGarbage()

    arcpy.ResetProgressor()
    if ignore == True:
        success = True
    return success

def getFieldExcept(desc,name):
    val = None
    return val


def calcValue(row,names,calcString):
    # calculate a value based on source fields and/or other expressions
    outVal = ""
    calcList = calcString.split("|")
    for strVal in calcList:
        if strVal in names:
            try:
                fidx = names.index(strVal)
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
                #dla.addMessage("Exceeded max number of errors in dla.maxErrorCount: " + str(dla.maxErrorCount))
                dla.addError("Exceeded max number of errors in dla.maxErrorCount: " + str(dla.maxErrorCount))
                return False
            if i > dla.maxrows:
                #dla.addMessage("Exceeded max number of rows supported in dla.maxrows: " + str(dla.maxrows))
                dla.addError("Exceeded max number of rows supported in dla.maxrows: " + str(dla.maxrows))
                return True
            i = i + 1
            setProgressor(i,numFeat)
            
            for field in fields:
                method = "None"
                sourceName = dla.getNodeValue(field,"SourceName")
                targetName = dla.getNodeValue(field,"TargetName")
                    
                targetValue = getTargetValue(row,field,names,sourceName,targetName)
                sourceValue = getSourceValue(row,names,sourceName,targetName)
                method = dla.getNodeValue(field,"Method").replace(" ","")
                fnum = names.index(targetName)

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
        nameidx = names.index(nm)
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
                if sourceTest == '':
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
        if str(otherwise) != "None":
            newValue = otherwise
        else:
            dla._errCount += 1
            success = False
            err = "Unable to find map value (otherwise) for " + str(targetName) + ", value = " + str(sourceValue)
            dla.addError(err)
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
    if i % 100 == 0:
        dla.addMessage("Feature " + str(i) + " processed")
    if i % getProgressUpdate(numFeat) == 0:
        arcpy.SetProgressorPosition(i)
        #dla.addMessage("Processing feature " + str(i))

def getProgressUpdate(numFeat):
    if numFeat > 500:
        progressUpdate = 1000 #int(numFeat/500)
    else:
        progressUpdate = 250
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
                targetValue = row[names.index(sourceName)]
            else:
                targetValue = row[names.index(targetName)]
        except:
            targetValue = None # handle the case where the source field does not exist or is blank

    return targetValue    

def getSourceValue(row,names,sourceName,targetName):
    try:
        sourceValue = row[names.index(sourceName)]    
    except:
        if sourceName != targetName and sourceName.upper() == targetName.upper():
            sourceValue = row[names.index(targetName)]    
        else:        
            sourceValue = None
    return sourceValue

def getValue(names,ftypes,lengths,targetName,targetValue,val):
    retVal = val # init to the value calculated so far. This function will alter as needed for field type 
    try:
        idx = names.index(targetName)
        if retVal == 'None':
            retVal = None
        if retVal != targetValue:
            if ftypes[idx] == 'Integer' or ftypes[idx] == 'Double':
                # if the type is numeric then try to cast to float
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

if __name__ == "__main__":
    main()
