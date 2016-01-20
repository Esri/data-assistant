__author__ = 'chri4819'


#Densify FC to support JSON conversion
arcpy.AddMessage("Simplifying (densifying) Parcel Geometry")
arcpy.Densify_edit(CommunityParcelsLocalCopy)
simplify = "{}temp".format(CommunityParcelsLocalCopy)
arcpy.SimplifyPolygon_cartography(CommunityParcelsLocalCopy, simplify, "POINT_REMOVE", "1 Meters")
print "Truncating Parcels from Feature Service"
arcpy.AddMessage("Truncating Parcels from Feature Service")


try:
	value1 = fs.query(where=deleteSQL, returnIDsOnly=True)
	myids = value1['objectIds']

	#Chunk deletes using 500 at a time

	minId = min(myids)
	i = 0
	maxId = max(myids)

	print minId
	print maxId
	chunkSize = 500

	while (i <= len(myids)):
		oids = ",".join(str(e) for e in myids[i:i + chunkSize])
		print oids
		if oids == '':
			continue
		else:
			fs.deleteFeatures(objectIds=oids)
		i += chunkSize
		print i
		print "Completed: {0:.0f}%".format(i / float(len(myids)) * 100)
		arcpy.AddMessage("Deleted: {0:.0f}%".format(i / float(len(myids)) * 100))


except:
	pass

	print "Community Parcels upload Started"
	arcpy.AddMessage("Community Parcels upload started, please be patient.  For future consideration, please run tool during non-peak internet usage")


	#Chunk uploads and use simplified geometry

	arcpy.env.overwriteOutput = True
	inDesc = arcpy.Describe(simplify)
	oidName = arcpy.AddFieldDelimiters(simplify,inDesc.oidFieldName)
	sql = '%s = (select min(%s) from %s)' % (oidName,oidName,os.path.basename(simplify))
	cur = arcpy.da.SearchCursor(simplify,[inDesc.oidFieldName],sql)
	minOID = cur.next()[0]
	del cur, sql
	sql = '%s = (select max(%s) from %s)' % (oidName,oidName,os.path.basename(simplify))
	cur = arcpy.da.SearchCursor(simplify,[inDesc.oidFieldName],sql)
	maxOID = cur.next()[0]
	del cur, sql
	breaks = range(minOID,maxOID)[0:-1:100]
	breaks.append(maxOID+1)
	exprList = [oidName + ' >= ' + str(breaks[b]) + ' and ' + \
				oidName + ' < ' + str(breaks[b+1]) for b in range(len(breaks)-1)]
	for expr in exprList:
		UploadLayer = arcpy.MakeFeatureLayer_management(simplify, 'TEMPCOPY', expr).getOutput(0)
		fs.addFeatures(UploadLayer)

	arcpy.Delete_management(simplify)