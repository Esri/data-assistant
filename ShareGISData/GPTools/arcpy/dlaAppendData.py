# dlaAppendData.py - Append Data to a database or service.
# --------------------------------------------------------------------------------------------------------------

import dlaPublish, arcpy

dlaPublish.useReplaceSettings = False # setting this to False will Append data

arcpy.AddMessage("Appending Data")

xmlFileNames = arcpy.GetParameterAsText(0) # xml file name as a parameter, multiple values separated by ;

dlaPublish.publish(xmlFileNames)

