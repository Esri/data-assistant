import os,arcpy, dla, dlaCreateSourceTarget,dlaPreview,dlaPublish

def main():
    test5()

def test1():
    dla._project = arcpy.mp.ArcGISProject(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject15\MyProject15.aprx")

    result = arcpy.MakeFeatureLayer_management(r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject15\MyProject15.gdb\test",
            "testTHIS")
    layer = result.getOutput(0)
    layer = dla.getLayer("Test")
    if isinstance(layer, arcpy._mp.Layer):
        print(layer.dataSource)
    else:
        desc = arcpy.Describe(layer)
        print(desc.catalogPath)

#    dlaCreateSourceTarget.createDlaFile("testTHIS",
#                                        r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject15\MyProject15.gdb\testout",
#                                        r"C:\Users\Steve\Documents\ArcGIS\Projects\MyProject15\testout.xml")

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
        #if group == 0:
        #    dlaPublish.useReplaceSettings = True # setting this to True will use ReplaceByField logic
        #    dlaPublish.publish(r'C:\Users\Steve\Documents\ArcGIS\Projects\pbmpolygons\pbm0Replace.xml')
        #else:
        #    dlaPublish.useReplaceSettings = False 
        #    dlaPublish.publish(outdoc)

#def repairDataset(ws,base,ds):
        #arcpy.RepairGeometry_management(ds,delete_null=True)
        #desc = arcpy.Describe(ds)
        #if desc.shapeType == 'Polygon':
        #    try:
        #        tempds = os.path.join(ws,base+'_tmp')
        #        if arcpy.Exists(tempds):
        #            arcpy.Delete_management(tempds)
        #        arcpy.Rename_management(ds,tempds)
        #        arcpy.SimplifyPolygon_cartography(in_features=tempds,out_feature_class=ds,
        #            tolerance='1 Meters',minimum_area='1 Meters',algorithm="POINT_REMOVE",error_option="RESOLVE_ERRORS")
                    #collapsed_point_option="NO_KEEP")
        #    except:
        #        try:
        #            arcpy.Rename_management(tempds,ds)
        #        except:
        #            pass
        #        dla.showTraceback()

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


