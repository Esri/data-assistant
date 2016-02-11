# dlaReplaceByField.py - use Replace field settings to replace content in a database or service.
# --------------------------------------------------------------------------------------------------------------
'''
Tool to replace data by field value or where clause. The script calls dlaPublish.publish with one or more
xml file names separated by semi colons - the way that a multiple file parameter is passed from Geoprocessing tools.

Data will be deleted in the target dataset using the Replace By Settings, and all data from the source will be appended.
'''
import dlaPublish, arcpy, dla

dlaPublish.useReplaceSettings = True # setting this to True will use ReplaceByField logic

arcpy.AddMessage("Replacing by Field Value")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;
dla._errorCount = 0

dlaPublish.publish(xmlFileNames) # perform the processing

dla.writeFinalMessage("Data Assistant - Replace Data")

