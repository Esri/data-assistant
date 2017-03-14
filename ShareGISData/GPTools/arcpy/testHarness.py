import os,arcpy, dla, dlaCreateSourceTarget,dlaPreview,dlaPublish,dlaStage

projFolder = r"C:\Users\Steve\Documents\ArcGIS\Projects\DomainTest"

def main():
    test01()

def test0():
    dlaStage.stage(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\ForSteve\CurbStopValves.xml")


def test01():
    #dla.setProject(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\SourceTarget.xml","DomainTest.aprx")
    dlaStage.stage(r"C:\Users\Steve\Documents\ArcGIS\Projects\DomainTest\SourceTarget.xml")
    #dlaPublish.publish(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\ForSteve\CurbStopValves.xml")
    #dlaPublish.publish(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\testjoin.xml")

def testCreate():
    dla._project = arcpy.mp.ArcGISProject(os.path.join(projFolder,"DomainTest.aprx"))
    dla._projectFolder = projFolder
    dlaCreateSourceTarget.createDlaFile(os.path.join(projFolder,r'DomainTest.gdb\WaterValve'),
                                        os.path.join(projFolder,r'DomainTest.gdb\WaterDevice'),
                                        os.path.join(projFolder,'SourceTarget.xml'))


def test1():
    dla._project = arcpy.mp.ArcGISProject(os.path.join(projFolder,"MyProject.aprx"))

    #fcfields = arcpy.ListFields(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\SampleData.gdb\SampleData")
    #tfields = arcpy.ListFields(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\SampleData.gdb\SampleTable")     

    #vfields = getViewString(tfields,fcfields)
    #result = arcpy.MakeFeatureLayer_management(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\SampleData.gdb\SampleData","Join1")


    #layer = dla.getMapLayer("JoinTest")
    #lname = layer.name
    #result = arcpy.MakeFeatureLayer_management(layer,lname)
    #layer = result.getOutput(0)
    #lyrFile = dla.getLayerPath(layer)

    #layer = dla.getMapLayer("JoinTest")
    #arcpy.env.overwriteOutput = True
    #lyrFile = os.path.join(projFolder,lname)
    #arcpy.SaveToLayerFile_management(layer,lyrFile)
    #desc = arcpy.Describe(lyrFile)
    #pth = dla.getLayerPath(lyrFile)
    #tmp = desc.catalogPath
    #fields = arcpy.ListFields(lyrFile)

    #result = arcpy.MakeFeatureLayer_management(lyrFile,lname)
    #layer = result.getOutput(0)
    #try:
    #    tmp = layer.connectionProperties
    #    for item in tmp:
    #        print(str(item),tmp[item])
    #    src = tmp['source']
    #    dest = tmp['destination']
    #    print(src['dataset'])
    #    print(src['connection_info']['database'])
    #    print(dest['dataset'])
    #    print(dest['connection_info']['database'])
    #except:
    #    pass
    
    dlaCreateSourceTarget.createDlaFile(r"JoinTest",
                                        r"http://services2.arcgis.com/EmOtS7q6cfSmspIo/arcgis/rest/services/MapTesting/FeatureServer/4",
                                        r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject\testjoin.xml")

    #result = arcpy.MakeFeatureLayer_management(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject15\MyProject15.gdb\test",
    #        "testTHIS")
    #layer = result.getOutput(0)
    #layer = dla.getLayer("Test")
    #if isinstance(layer, arcpy._mp.Layer):
    #    print(layer.dataSource)
    #else:
    #    desc = arcpy.Describe(layer)
    #    print(desc.catalogPath)

def getViewString(fields,fields2):
    # get the string for creating a view
    viewStr = ""
    for field in fields: # drop any field prefix from the source layer (happens with map joins)
        thisFieldName = field.name[field.name.rfind(".")+1:]
        for field2 in fields2:
            matchname = field2.name[field2.name.rfind(".")+1:]
            if matchname != thisFieldName and matchname.upper() == thisFieldName.upper():
                # this is a special case where the source name is different case but the same string as the target
                # need to create table so that the name matches the target name so there is no conflict later
                thisFieldName = targetname

        thisFieldStr = field.name + " " + thisFieldName + " VISIBLE NONE;"
        viewStr += thisFieldStr

    return viewStr



def test2():

    dla._project = arcpy.mp.ArcGISProject(r"C:\Users\Steve\Documents\ArcGIS\Projects\pbmpolygons\pbmpolygons.aprx")
    ws = r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject11\shp\Data Assistant 10.4 Testing\pbmnorepair.gdb"
    base = "pbmpoly"
    res = arcpy.GetCount_management(os.path.join(ws,base))
    cnt = int(res.getOutput(0))
    chunk = 100000
    lngth = int(cnt/chunk)

    for group in range (0,lngth):

        minoid = group * chunk
        where = 'OBJECTID > '+ str(minoid) + ' AND OBJECTID <= ' + str(minoid+chunk)
        dla.addMessage(where)

        layername = "pbmpolys"
        if arcpy.Exists(layername):
            arcpy.Delete_management(layername)
        result = arcpy.MakeFeatureLayer_management(in_features=os.path.join(ws,base),where_clause=where,workspace=ws,out_layer=layername)

        cnt = result.getOutput(0)
        outpath = r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject11\shp\Data Assistant 10.4 Testing\pbm.gdb"
        outname = "pbmpoly"+str(group) 
        ds = os.path.join(outpath,outname)
        if arcpy.Exists(ds):
            arcpy.Delete_management(ds)
        arcpy.FeatureClassToFeatureClass_conversion(in_features=layername,out_path=outpath,out_name=outname)

        outdoc = r"C:\Users\Steve\Documents\ArcGIS\Projects\pbmpolygons\pbm" + str(group) + ".xml"
        svce = r"http://services.arcgis.com/b6gLrKHqgkQb393u/arcgis/rest/services/TaxDistribution/FeatureServer/0"
        
        dlaCreateSourceTarget.createDlaFile(ds,svce,outdoc)


def test3():

    dla._project = arcpy.mp.ArcGISProject(r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\Trails.aprx")

    dlaCreateSourceTarget.createDlaFile(r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\prawn.sde\GDB_D.DBO.GWS_FACILITY",
                                        r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\prawn.sde\GDB_D.DBO.GWS_TANK",
                                        r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\tables.xml")

def test4():
    dlaPreview.preview(r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\tables.xml")

def test5():
    dlaPublish.useReplaceSettings = True
    dlaPublish.publish(r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\tables.xml")

def test6():

    dla._project = arcpy.mp.ArcGISProject(r"C:\Users\Steve\Documents\ArcGIS\Projects\Trails\Trails.aprx")
    layer = "Trails"
    try:
        desc = arcpy.Describe(layer) # never works in scripts
    except:
        arcpy.AddMessage("Describe error")    
        dla.showTraceback()

    layer = dla.getLayer("Trails") # loop through maps/layers to find matching name
    if layer != None and layer.supports("DataSource"):
        try:
            arcpy.AddMessage(layer.dataSource)
        except:
            arcpy.AddMessage("Print error")    

if __name__ == "__main__":
    main()