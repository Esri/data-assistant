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
Contains classes to hold properties - not currently used, just working on an idea.
'''
import sys,os,xml.dom.minidom,time,datetime

import json
from xml.dom.minidom import Document

class dlaFile:
    # a simple class to hold project properties 
    def __init__(self,xmlFile):
        self.xmlFile
        self.dirName
        self.xmlDoc = xmlDoc
        self.dlaSourceTarget # dlaDatasets
        self.dlaFields
        self.dlaSourceFields
        self.dlaTargetFields
        self.data
        # not directly from xml file but useful items.
        self.rootFolder
        self.relativePath
        self.dlaworkspace
        self.dlaTable
        self.sourceViewName
        self.signinToken
        self.useReplaceSettings
        self.token

class dlaSourceTarget:
    # a simple class to hold Datasets section of the xml document
    def __init__(self,xmlDoc):
        self.rootFolder
        self.relativePath
        self.fullPath
        self.source # a dlaDataset
        self.target # a dlaDataset
        self.sourceSpatialReference
        self.targetSpatialReference
        self.replaceBy
        self.staged

class dlaDataset:
    # a simple class to hold dataset properties 
    def __init__(self,xmlDoc):
        self.rootFolder
        self.relativePath
        self.fullPath
        self.connectionProperties
        self.datasetName
        self.datasetType
        self.dlaType # dataset, layer file, service
        self.featureClass
        self.table
        self.dlaService
        self.shapeType
        self.spatialReference
        self.spatialReferenceString
        self.fields
        self.fieldNames
        self.dlaFields
        self.oidWhereClause

class dlaService:
    # a simple class to hold feature service properties 
    def __init__(self,xmlDoc):
        self.url
        self.serviceCapabilities # boolean or list?
