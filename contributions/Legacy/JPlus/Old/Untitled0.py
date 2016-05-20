# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import arcpy
import sys
import pandas as pd
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
import os
import datetime
import jdcal
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <codecell>

locationtemp1 = r'c:\ArcGIS\temp'
locationtemp2 = r'c:\ArcGIS\EDM.gdb\temp'

# <codecell>

Simple_CQ = locationtemp2+'\\'+'Simple_CQ'

# <codecell>

DataFactorsBoundaries= locationtemp1+'\\'+'BoundariesTable.csv'
DataFactorsCentroids = locationtemp1+'\\'+'CentroidsTable.csv'

# <codecell>

#local variables
NearTable = locationtemp1+'\\'+'NearTable.dbf'
CQLines = locationtemp2+'\\'+'\CQLines'
CQVertices = locationtemp2+'\\'+'CQVertices'
CQSegments = locationtemp2+'\\'+'CQSegment'
CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
centroidsTable_name = 'CentroidCQdata.dbf'
centroidsTable = locationtemp1+'\\'+centroidsTable_name
Overlaptable = locationtemp1+'\\'+'overlapingTable.csv'

# <codecell>

#Create points in the centroid of segment line and table with near features: 
# indentifying for each segment of line of building A the segment of line of building B in common.  
arcpy.FeatureToLine_management(Simple_CQ,CQLines)
arcpy.FeatureVerticesToPoints_management(Simple_CQ,CQVertices,'ALL')
arcpy.SplitLineAtPoint_management(CQLines,CQVertices,CQSegments,'2 METERS')
arcpy.FeatureVerticesToPoints_management(CQSegments,CQSegments_centroid,'MID')
arcpy.GenerateNearTable_analysis(CQSegments_centroid,CQSegments_centroid,NearTable,"1 Meters","NO_LOCATION","NO_ANGLE","CLOSEST","0")

# <codecell>

#Import the table with NearMatches
NearMatches = dbf2df(NearTable)

# <codecell>

# Import the table with attributes of the centroids of the Segments
arcpy.TableToTable_conversion(CQSegments_centroid, locationtemp1, centroidsTable_name)
DataCentroids = dbf2df(centroidsTable, cols={'Name','height','ORIG_FID'})

# <codecell>

# CreateJoin to Assign a Factor to every Centroid of the lines, FactorShade =0 if the line
# exist in a building totally covered by another one, and Freeheight = 1 to the height of the line 
# that is not obstructed by the other building
FirstJoin = pd.merge(NearMatches,DataCentroids,left_on='IN_FID', right_on='ORIG_FID')
SecondaryJoin = pd.merge(FirstJoin,DataCentroids,left_on='NEAR_FID', right_on='ORIG_FID')

# <codecell>

# delete matches within the same polygon Name (it can happen that lines are too close one to the other)
# also delete matches with a distance of more than 20 cm making room for mistakes during the simplicfication of buildings but avoiding deleten boundaries 
rows = SecondaryJoin.IN_FID.count()
for row in range(rows):
    if SecondaryJoin.loc[row,'Name_x'] == SecondaryJoin.loc[row,'Name_y'] or SecondaryJoin.loc[row,'NEAR_DIST'] > 0.2:
       SecondaryJoin = SecondaryJoin.drop(row)
SecondaryJoin.reset_index(inplace=True)

# <codecell>

rows = SecondaryJoin.IN_FID.count()
SecondaryJoin['FactorShade']=0
SecondaryJoin['Freeheight']=0
for row in range(rows):
    if SecondaryJoin.loc[row,'height_x'] <= SecondaryJoin.loc[row,'height_y']:
        SecondaryJoin.loc[row,'FactorShade'] = 0
        SecondaryJoin.loc[row,'Freeheight'] = 0
    elif SecondaryJoin.loc[row,'height_x'] > SecondaryJoin.loc[row,'height_y'] and SecondaryJoin.loc[row,'height_x']-1 <= SecondaryJoin.loc[row,'height_y']:
        SecondaryJoin.loc[row,'FactorShade'] = 0
    else:
        SecondaryJoin.loc[row,'FactorShade'] = 1
        SecondaryJoin.loc[row,'Freeheight'] = abs(SecondaryJoin.loc[row,'height_y']- SecondaryJoin.loc[row,'height_x'])

# <codecell>

#Create and export Secondary Join with results, it will be Useful for the function CalcObservers
SecondaryJoin.to_csv(DataFactorsBoundaries,index=False)

# <codecell>

#Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without
#shading boundaries these factors are equal to 1 and the field 'height' respectively.
DataCentroids['FactorShade'] = 1
DataCentroids['Freeheight'] = DataCentroids['height']

# <codecell>

Results = DataCentroids.merge(SecondaryJoin, left_on='ORIG_FID', right_on='ORIG_FID_x', how='outer')

# <codecell>

Results.FactorShade_y.fillna(Results['FactorShade_x'],inplace=True)
Results.Freeheight_y.fillna(Results['Freeheight_x'],inplace=True)
Results.rename(columns={'FactorShade_y':'FactorShade','Freeheight_y':'Freeheight'},inplace=True)
FinalDataCentroids = pd.DataFrame(Results,columns={'ORIG_FID','height','FactorShade','Freeheight'})
FinalDataCentroids.to_csv(DataFactorsCentroids,index=False)

# <markdowncell>

# ##New observation

# <codecell>

# import the table with factors of boundaries and get sinlge values of those with value = 0 in factor shade
#local variables
Out_name = locationtemp1+'\\'+'Datacentroids.dbf'
Observers = locationtemp2+'\\'+'Observers2'
ObserversLines = locationtemp2+'\\'+'ObserversLines'
Overlapping = locationtemp2+'\\'+'Overlapping'
non_Overlapping = locationtemp2+'\\'+'non_Overlapping'
#calculation
df2dbf(FinalDataCentroids,Out_name)

# <codecell>

# do the same with the lines
arcpy.JoinField_management(CQSegments,'OBJECTID', Out_name,'ORIG_FID')
arcpy.CopyFeatures_management(CQSegments,ObserversLines)
with arcpy.da.UpdateCursor(ObserversLines, 'FactorShadeN') as cursor:
    for row in cursor:
        if row[0] == 0:
            cursor.deleteRow()

# <codecell>

# Merge data with centroids
arcpy.JoinField_management(CQSegments_centroid,'ORIG_FID', Out_name,'ORIG_FID')
arcpy.CopyFeatures_management(CQSegments_centroid,Observers)
#Delete those points with Factorshade = 0 (sharing completely boundaries)
with arcpy.da.UpdateCursor(Observers, 'FactorShadeN') as cursor:
    for row in cursor:
        if row[0] == 0:
            cursor.deleteRow()

# <codecell>

# delete those points of deposits
with arcpy.da.UpdateCursor(Observers, 'DEPO') as cursor:
    for row in cursor:
        if row[0] == 1:
            cursor.deleteRow()

# <markdowncell>

# eliminate points over polygons overlapping

# <codecell>

#Identify the polygons that share boundaries, create a new layer with it and aggregate
DataNear = pd.read_csv(DataFactorsBoundaries)
CleanDataNear = DataNear[DataNear['FactorShade'] == 0]
CleanDataNear.drop_duplicates(cols='Name_x',inplace=True)
CleanDataNear.reset_index(inplace=True)
rows = CleanDataNear.Name_x.count()

# <codecell>

# local variables
OverlappingAgg = locationtemp2+'\\'+'Overlappingagg'
for row in range(rows):
    Field = "Name" # select field where the name exists to iterate
    Value = CleanDataNear.loc[row,'Name_x'] # set the value or name of the City quarter
    Where_clausule =  ''''''+'"'+Field+'"'+"="+"\'"+str(Value)+"\'"+'''''' # strange writing to introduce in ArcGIS
    if row == 0:
        arcpy.MakeFeatureLayer_management(Simple_CQ, 'Simple_lyr')
        arcpy.SelectLayerByAttribute_management('Simple_lyr',"NEW_SELECTION",Where_clausule)
    else:
        arcpy.SelectLayerByAttribute_management('Simple_lyr',"ADD_TO_SELECTION",Where_clausule)
        
arcpy.CopyFeatures_management('Simple_lyr', Overlapping)
arcpy.AggregatePolygons_cartography(Overlapping,OverlappingAgg,"1 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL","#","C:/ArcGIS/Default.gdb/Overlapping_AggregatePolygon_Tbl")

# <codecell>

# do the same but create a layer with the rest of buildings and then join both files
arcpy.MakeFeatureLayer_management(Simple_CQ, 'CTR_lyr')
selection = arcpy.SelectLayerByLocation_management('CTR_lyr', 'intersect', Overlapping)
arcpy.SelectLayerByLocation_management('CTR_lyr', 'intersect', Overlapping, selection_type='switch_selection')
arcpy.CopyFeatures_management('CTR_lyr', non_Overlapping)
arcpy.Merge_management([Overlapping,non_Overlapping],Observers)

# <codecell>


# <codecell>

#make a new copy where the observers will be stored

# <codecell>


# <codecell>


# <codecell>


# <codecell>


# <codecell>


# <codecell>


# <codecell>


# <codecell>

FinalDataCentroids

# <markdowncell>

# now with the observers

# <codecell>

# Local variables
Observers = locationtemp2+'\\'+'observers'
locationtemporal2 = locationtemp2

# <codecell>

Buffer_CQ = locationtemporal2+'\\'+'BufferCQ'
temporal_lines = locationtemporal2+'\\'+'lines'
Points = locationtemporal2+'\\'+'Points'
AggregatedBuffer = locationtemporal2+'\\'+'BufferAggregated'
temporal_lines3 = locationtemporal2+'\\'+'lines3'
Points3 = locationtemporal2+'\\'+'Points3'
Points3Updated = locationtemporal2+'\\'+'Points3Updated'
EraseObservers = locationtemporal2+'\\'+'eraseobservers'
Observers = locationtemporal2+'\\'+'observers'  
NonoverlappingBuildings = locationtemporal2+'\\'+'Non_overlap'

# <codecell>

#Transform all polygons of the simplified areas to observation points
arcpy.SplitLine_management(Buffer_CQ,temporal_lines)
arcpy.FeatureVerticesToPoints_management(temporal_lines,Points,'MID') # Second the transformation of Lines to a mid point

# <codecell>

#Join all the polygons to get extra vertices, make lines and then get points. 
#these points should be added to the original observation points
arcpy.AggregatePolygons_cartography(Buffer_CQ,AggregatedBuffer,"0.5 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL") # agregate polygons
arcpy.SplitLine_management(AggregatedBuffer,temporal_lines3) #make lines
arcpy.FeatureVerticesToPoints_management(temporal_lines3,Points3,'MID')# create extra points

# <codecell>

# add information to Points3 about their buildings and erase oveerlapping points
arcpy.SpatialJoin_analysis(Points3,Buffer_CQ,Points3Updated,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST")
arcpy.Erase_analysis(Points3Updated,Points,EraseObservers,"2 Meters")# erase overlaping points
arcpy.Merge_management([Points,EraseObservers],Observers)# erase overlaping points

# <codecell>

DataNear = pd.read_csv(DataFactorsBoundaries)
Dataobservers= pd.read_csv(DataFactorsObservers)

# <codecell>

print Dataobservers.head()

# <codecell>

print DataNear.head()

# <codecell>

CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
print CleanDataNear.head()

# <codecell>

#  Eliminate Observation points above roofs of the highest surfaces(a trick to make the 
#Import Overlaptable from function CalcBoundaries containing the data about buildings overlaping, eliminate duplicades, chose only those ones no overlaped and reindex
DataNear = pd.read_csv(DataFactorsBoundaries)

# <codecell>

# Eliminate observation points that ar inside buildings with also sharing boundaries with other buildings of the same height

# <codecell>


