# dlaAppendData.py - Append Data to a database or service.
# --------------------------------------------------------------------------------------------------------------
'''
Tool to append data to a target dataset. The script calls dlaPublish.publish with one or more
xml file names separated by semi colons - the way that a multiple file parameter is passed from Geoprocessing tools.

No data will be deleted in the target dataset, and all data from the source will be appended.
'''

import dlaPublish, arcpy, dla

dlaPublish.useReplaceSettings = False # setting this to False will Append data

arcpy.AddMessage("Appending Data")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;
dla._errorCount = 0

dlaPublish.publish(xmlFileNames) # perform the processing

dla.writeFinalMessage("Data Assistant - Append Data")

