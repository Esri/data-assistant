# dlaReplaceByField.py - use Replace field settings to replace content in a database or service.
# --------------------------------------------------------------------------------------------------------------

import dlaPublish, arcpy, dla

dlaPublish.useReplaceSettings = True # setting this to True will use ReplaceByField logic

arcpy.AddMessage("Replacing by Field Value")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;
dla._errorCount = 0

dlaPublish.publish(xmlFileNames)

dla.writeFinalMessage("Data Assistant - Replace Data")

