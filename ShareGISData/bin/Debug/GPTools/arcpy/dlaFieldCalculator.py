# ---------------------------------------------------------------------------
# dlaFieldCalculator.py

import os, sys, traceback, time, arcpy,  xml.dom.minidom, dla

xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
try:
    dla.workspace = arcpy.GetParameterAsText(1) # scratch Geodatabase
except:
    dla.workspace = arcpy.env.scratchGDB
SUCCESS = 2 # parameter number for output success value

if dla.workspace == "" or dla.workspace == "#":
    dla.workspace = arcpy.env.scratchGDB

errCount = 0

def main(argv = None):
    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    targetName = dla.getTargetName(xmlDoc)
    success = calculate(xmlFileName,dla.workspace,targetName,False)
    if success == False:
        dla.addError("Errors occurred during field calculation")
    arcpy.SetParameter(SUCCESS, success)

def calculate(xmlFileName,workspace,name,ignore):

    dla.workspace = workspace    
    success = True
    arcpy.ClearWorkspaceCache_management(dla.workspace)
    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    
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
    #sourceFields = dla.getXmlElements(xmlFileName,"SourceField")
    targetFields = dla.getXmlElements(xmlFileName,"TargetField")
    attrs = [f.name for f in arcpy.ListFields(table)]

    for field in fields:
        arcpy.env.Workspace = dla.workspace
        targetName = dla.getNodeValue(field,"TargetName")
        sourceName = dla.getNodeValue(field,"SourceName")
            
        type = "String"
        length = "50"
        for target in targetFields:
            nm = target.getAttributeNode("Name").nodeValue
            if  nm == targetName:
                type = target.getAttributeNode("Type").nodeValue
                length = target.getAttributeNode("Length").nodeValue
        dla.addDlaField(table,targetName,field,attrs,type,length)

    names = [f.name for f in arcpy.ListFields(table)]

    retVal = setFieldValues(table,fields,names)
    if retVal == False:
        success = False
    arcpy.ClearWorkspaceCache_management(dla.workspace)
    dla.cleanupGarbage()

    arcpy.ResetProgressor()
    if ignore == True:
        success = True
    return success

def calcValue(row,names,calcString):
    # calculate a value based on fields and or other expressions
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

def setFieldValues(table,fields,names):
    # from source xml file match old values to new values to prepare for append to target geodatabase
    success = False
    
    try:
        updateCursor = arcpy.da.UpdateCursor(table,names)
    except:
        dla.addMessage( "Unable to update the Dataset, Python error is: ")
        dla.showTraceback()
        row = None

    result = arcpy.GetCount_management(table)
    numFeat = int(result.getOutput(0))
    dla.addMessage(table + ", " + str(numFeat) + " features")
    i = 0
    arcpy.SetProgressor("Step","Calculating " + table + "...",0,numFeat,getProgressUpdate(numFeat))
    
    for row in updateCursor:
        global errCount
        success = True
        if errCount > dla.maxErrorCount:
            dla.addMessage("Exceeded max number of errors in dla.maxErrorCount: " + str(dla.maxErrorCount))
            return False
        if i > dla.maxrows:
            dla.addMessage("Exceeded max number of rows supported in dla.maxrows: " + str(dla.maxrows))
            return True
        i = i + 1
        setProgressor(i,numFeat)
        for field in fields:
            method = "None"
            sourceName = dla.getNodeValue(field,"SourceName")
            targetName = dla.getNodeValue(field,"TargetName")
                
            targetValue = getTargetValue(row,field,names,sourceName,targetName)
            sourceValue = getSourceValue(row,names,sourceName)
            method = dla.getNodeValue(field,"Method").replace(" ","")
            if method == "None" or (method == "Copy" and sourceName == '(None)'):
                method = "None"
                val = None
            elif method == "Copy":
                val = sourceValue
            elif method == "DefaultValue":
                val = dla.getNodeValue(field,"DefaultValue")
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
                part = dla.getNodeValue(field,"Part")
                val = getSplit(sourceValue,splitter,part)
            elif method == "ConditionalValue":
                sname = dla.getNodeValue(field,"SourceName")
                oper = dla.getNodeValue(field,"Oper")
                iif = dla.getNodeValue(field,"If")
                tthen = dla.getNodeValue(field,"Then")
                eelse = dla.getNodeValue(field,"Else")
                expression = tthen + " if |" + sname + "| " + oper + " " + iif + " else " + eelse
                val = getExpression(row,names,expression)
            elif method == "Expression":
                expression = dla.getNodeValue(field,method)
                for name in names:
                    expression = expression.replace(name,"|" + name + "|")
                val = getExpression(row,names,expression)
            # set field value
            setValue(row,names,targetName,targetValue,val)
        try:
            updateCursor.updateRow(row)
        except:
            errCount += 1
            success = False
            err = "Exception caught: unable to update row"
            printRow(row,names)
            dla.showTraceback()
            dla.addError(err)
        
    del updateCursor
    dla.cleanupGarbage()
    arcpy.ResetProgressor()

    return success


def getSplit(sourceValue,splitter,part):
    global errCount
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
        
##    for val in stripvals:
##        nothing = False
##        while nothing == False:
##            try:
##                if(concat[i] 
##                concat.remove(val)
##                nothing = False
##            except:
##                nothing = True
                
    concatStr = sep.join(items)
    return concatStr

def getValueMap(row,names,sourceValue,field):
    global errCount
    # run value map function for a row
    valueMaps = field.getElementsByTagName("ValueMap")
    newValue = None
    found = False
    for valueMap in valueMaps:
        try:
            otherwise = valueMap.getElementsByTagName("Otherwise")
        except:
            otherwise = None
        sourceValues = []
        sourceValues = valueMap.getElementsByTagName("sValue")
        targetValues = []
        targetValues = valueMap.getElementsByTagName("tValue")
        i = 0
        for sourceValue in sourceValues:
            sValue = dla.getTextValue(sourceValue)
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
                    errCount += 1
                    success = False
                    err = "Unable to map values for " + sourceValue + ", value = " + str(newValue)
                    dla.showTraceback()
                    dla.addError(err)
                    print(err)
            i = i + 1
    if not found:
        if otherwise and str(otherwise) != "None" and otherwise != []:
            otherwise = str(otherwise)
            #if otherwise.count(" ") > 2 or otherwise.count("!") > 1:
            newValue = calcValue(row,names,otherwise)
            # setValue(row,targetName,sourceValue,otherval,idx)
        else:
            errCount += 1
            success = False
            err = "Unable to find map value (otherwise) for " + str(targetName) + ", value = " + str(sourceValue)
            dla.addError(err)
    return newValue

def getExpression(row,names,expression):
    global errCount
    calcNew = None
    try:
        calcNew = calcValue(row,names,expression)
        #setValue(row,targetName,sourceValue,calcNew,idx)
    except:
        err = "Exception caught: unable to set value for expression=" + expression
        dla.showTraceback()
        dla.addError(err)
        print(err)
        errCount += 1
    return calcNew

def setProgressor(i,numFeat):
    if i % 1000 == 0:
        dla.addMessage("Feature " + str(i) + " processed")
    if i % getProgressUpdate(numFeat) == 0:
        arcpy.SetProgressorPosition(i)
        dla.addMessage("Processing feature " + str(i))

def getProgressUpdate(numFeat):
    if numFeat > 500:
        progressUpdate = int(numFeat/500)
    else:
        progressUpdate = 10
    return progressUpdate

def printRow(row,names):
    r = 0
    for item in row:
        print(str(names[r]) + ": " + str(item))
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

def getSourceValue(row,names,sourceName):
    try:
        sourceValue = row[names.index(sourceName)]    
    except:
        sourceValue = None
    return sourceValue

def setValue(row,names,targetName,targetValue,val):

    global errCount
   
    try:
        if val == 'None':
            val = None
        if val != targetValue:
            row[names.index(targetName)] = val
    except:
        success = False
        err = "Exception caught: unable to set value for value=" + str(val)
        dla.showTraceback()
        dla.addError(err)
        print(err)
        errCount += 1

if __name__ == "__main__":
    main()
