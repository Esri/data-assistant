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
dla._errCount = 0

dlaPublish.publish(xmlFileNames) # perform the processing

dla.writeFinalMessage("Data Assistant - Replace Data")

