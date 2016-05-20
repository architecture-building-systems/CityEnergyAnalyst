# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #1. RADIATION MODEL
# ##Introduction
# 
# This routine calculates the solar radiation incident in the surfaces of Buildings in Wh/m2 per every hour of the year.
# THe algorithm considers shading form adjacent buildings, vegetation and terrain.
# 
# ###The input:
# 
# 1. From 0. City Quarters
# 
# - CQ_Name: The name of the City quarter/Zone/Cluster to Create the radiation model obtained from the Routine Number 0. CQ
# - CQ = a .shp (multi-polygon) file containing the simplified buildings of the selected City quarter/Zone/Cluster to run the analysis and obtained from the Routine Numer 0. CQ.
# - Simple_Context = a .shp file containing the simplified buildings of all the context and obtained from the Routine Number 0. CQ
# 
# 2. Other
# 
# - DEModel: a .asci or tif (raster) file containing a high definition Digital Elevation Model of the Context including mountains if possible.
# - Latitude: Latitude of the City of the case study (+) if North, (-) if South.
# - Longitude: Longitude of the City of the case study (+) if West of Grenwhich meridian, (-) if East.
# - Timezone: GMT + (?)
# - Daylightsaving dates: Number of day of the year where daylightsaving measures take place. for Zug in 2013 = 90 and 300
# 
# ###The Output:
# 
# - DEModelFinal = a .asci or tif (raster) file containing a high definition Digital Elevation Model with Buildings.
# - DataRadiation = a .csv file containing the hourly radiation values Wh/m2 incident in a point representing every vertical surface of the Buildings analyzed,
#                   This file contents the Length of everysurface, the name of the building at which this surface belons too, the height of the building related, the Factor " Freeheight" and the Factpr "FactorShade"
#                   Freeheight stands for the height of the surface that is exposed to the exterior, factor Shade represents the amount of area of the surface facing the exterior.

# <markdowncell>

# ## MODULES

# <codecell>

import arcpy
from arcpy.sa import *
import pandas as pd
import numpy as np
arcpy.env.workspace = 'c:\ArcGIS\EDM.gdb'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <codecell>

import sys, os
sys.path.append("C:\Users\Jimeno Fonseca\Documents\Console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 

# <codecell>

import datetime
import jdcal

# <markdowncell>

# ##VARIABLES

# <codecell>

CQ_name = 'CityQuarter_3'
CQ = r'c:\ArcGIS\EDM.gdb\Communities\CityQuarter_3' 
Context = r'c:\ArcGIS\EDM.gdb\RawData\Context'

# <codecell>

DEModel = r'c:\ArcGIS\EDM.gdb\DEM' # DEM of analysis
Latitude = 47.1628017306431# of the site Zug
Longitude = 8.31 # of the site Zug
TimeZone = 1 # of the site Zug

# <codecell>

Simple_CQ = r'c:\ArcGIS\EDM.gdb\temp'+'\\'+'Sim'+CQ_name
Simple_Context = r'c:\ArcGIS\EDM.gdb\temp\Simple_Context'

# <codecell>

Buffer_CQ = r'c:\ArcGIS\EDM.gdb\temp\BufferCQ'
AggregatedBuffer = r'c:\ArcGIS\EDM.gdb\temp\BufferAggregated'
temporal_lines = r'c:\ArcGIS\EDM.gdb\temp\lines' 
temporal_lines2 = r'c:\ArcGIS\EDM.gdb\temp\lines2' 
temporal_lines3 = r'c:\ArcGIS\EDM.gdb\temp\lines3'
Points2 = r'c:\ArcGIS\EDM.gdb\temp\Points2'
Points3 = r'c:\ArcGIS\EDM.gdb\temp\Points3'
Points = r'c:\ArcGIS\EDM.gdb\temp\Points' 
SimpleBuffer_CQ = r'c:\ArcGIS\EDM.gdb\temp\SimpleBufferfCQ'
temporal1 = r'c:\ArcGIS\temp'
temporal2 = r'c:\ArcGIS\EDM.gdb'
Outradiation = r'c:\ArcGIS\temp\Surfaceradiationyear.csv'
EraseObservers = r'c:\ArcGIS\EDM.gdb\temp\eraseobservers'
Observers = r'c:\ArcGIS\EDM.gdb\temp\observers'
CentroidCQ = r'c:\ArcGIS\EDM.gdb\temp\CQcentroid'
Overlaptable = temporal1+'\\'+'overlapingTable.csv'

# <codecell>

DEModelFinal = r'c:\ArcGIS\EDM.gdb\DEM_All'

# <codecell>

# Set local variables
latitude = '47.1628017306431' # obtained from the model itself but String
skySize = '3500'
dayInterval = '1'
hourInterval = '1'
calcDirections = '32'
zenithDivisions = '8'
azimuthDivisions = '8'
diffuseProp = '0.3'
transmittivity = '0.5'
heightoffset = '5'

# <codecell>

CQLines = r'c:\ArcGIS\EDM.gdb\temp\CQLines'
CQVertices = r'c:\ArcGIS\EDM.gdb\temp\CQVertices'
CQSegments = r'c:\ArcGIS\EDM.gdb\temp\CQSegment'
CQSegments_centroid = r'c:\ArcGIS\EDM.gdb\temp\CQSegmentCentro'
NearTable = r'c:\ArcGIS\temp\NearTable.dbf'

# <codecell>

NonoverlappingBuildings = r'c:\ArcGIS\EDM.gdb\temp\Non_Overlap'
DataCentroidsCSV=r'c:\ArcGIS\temp\Datacentroids.csv'

# <codecell>

DataradiationLocation = r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'DataRadiation.csv'

# <markdowncell>

# ##FUNCTIONS

# <markdowncell>

# ###Calculation of Sunrise hour

# <codecell>

def Calc_sunrise(day,Longitude,Latitude,TimeZone): # Calculated according to NOAA website
    # Calculate Date and Julian day
    Date = datetime.datetime(2013, 1, 1) + datetime.timedelta(day - 1)
    JuliandDay = sum(jdcal.gcal2jd(Date.year, Date.month, Date.day))
    JulianCentury = (JuliandDay-2451545)/36525
    # variables
    Gmean = np.mod(280.46646+JulianCentury*(36000.76983 + JulianCentury*0.0003032),360)
    Gmeansun = 357.52911+JulianCentury*(35999.05029 - 0.0001537*JulianCentury)
    Orbit = 0.016708634-JulianCentury*(0.000042037+0.0000001267*JulianCentury)
    Suneq_control = np.sin(np.radians(Gmeansun))*(1.914602-JulianCentury*(0.004817+0.000014*JulianCentury))+np.sin(np.radians(2*Gmeansun))*(0.019993-0.000101*JulianCentury)+np.sin(np.radians(3*Gmeansun))*0.000289
    Suntrue_long = Gmean+Suneq_control
    Sunapp_long = Suntrue_long-0.00569-0.00478*np.sin(np.radians(125.04-1934.136*JulianCentury))
    MeanObl = 23+(26+((21.448-JulianCentury*(46.815+JulianCentury*(0.00059-JulianCentury*0.001813))))/60)/60
    OblCorr = MeanObl+0.00256*np.cos(np.radians(125.04-1934.136*JulianCentury))
    SunDeclinationAngle = np.degrees(np.arcsin(np.sin(np.radians(OblCorr))*np.sin(np.radians(Sunapp_long))))
    vary = np.tan(np.radians(OblCorr/2))*np.tan(np.radians(OblCorr/2))
    #Equation of time:
    EOT =4*np.degrees(vary*np.sin(2*np.radians(Gmean))-2*Orbit*np.sin(np.radians(Gmeansun))+4*Orbit*vary*np.sin(np.radians(Gmeansun))*np.cos(2*np.radians(Gmean))-0.5*vary*vary*np.sin(4*np.radians(Gmean))-1.25*Orbit*Orbit*np.sin(2*np.radians(Gmeansun)))
    # aparent sunrise hour
    HA_sunrise = np.degrees(np.arccos(np.cos(np.radians(90.833))/(np.cos(np.radians(Latitude))*np.cos(np.radians(SunDeclinationAngle)))-np.tan(np.radians(Latitude))*np.tan(np.radians(SunDeclinationAngle))))
    Solar_noon =(720-4*Longitude-EOT+TimeZone*60)/1440
    Sun_rise = (Solar_noon-HA_sunrise*4/1440)*24
    return Sun_rise

# <markdowncell>

# ###Parsing of Radiation data

# <codecell>

def Calctable(day,Radiation):
    import datetime
    # Table with empty values with the same range as the points.
    TableFShade_LCT = pd.DataFrame.copy(Radiation)
    Names = ['T0','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16','T17','T18','T19','T20','T21','T22','T23']
    for Name in Names:
        TableFShade_LCT[Name]= 0
    #Counter of Columns in the Initial Tabshade
    Counter = Radiation.count(1)
    Value = Counter[0]-1
    #Condition to take into account daysavingtime in Switzerland as the radiation data in ArcGIS is calculated for 2013.    
    if 90 <= day <300: 
        D = 1
    else:
        D = 0 
    # Calculation of Sunrise time
    Sunrise_time = Calc_sunrise(day,Longitude,Latitude,TimeZone) + D
    # Calculation of table
    for time in range(Value):
        Hour = int(Sunrise_time)+ int(time)
        TableFShade_LCT['T'+str(Hour)] = Radiation['T'+str(time)]
    #rename the table for every T to get in 1 to 8760 hours.
    if day == 1:
        name = 1
    else:
        name = int(day-1)*24+1
    
    TableFShade_LCT.rename(columns={'T0':'T'+str(name),'T1':'T'+str(name+1),'T2':'T'+str(name+2),'T3':'T'+str(name+3),'T4':'T'+str(name+4),
                                    'T5':'T'+str(name+5),'T6':'T'+str(name+6),'T7':'T'+str(name+7),'T8':'T'+str(name+8),'T9':'T'+str(name+9),
                                    'T10':'T'+str(name+10),'T11':'T'+str(name+11),'T12':'T'+str(name+12),'T13':'T'+str(name+13),'T14':'T'+str(name+14),
                                    'T15':'T'+str(name+15),'T16':'T'+str(name+16),'T17':'T'+str(name+17),'T18':'T'+str(name+18),'T19':'T'+str(name+19),
                                    'T20':'T'+str(name+20),'T21':'T'+str(name+21),'T22':'T'+str(name+22),'T23':'T'+str(name+23)},inplace=True)
    return TableFShade_LCT

# <markdowncell>

# ##PROCESSES

# <markdowncell>

# ###Simplification of Buildings

# <codecell>

arcpy.SimplifyBuilding_cartography(Context,Simple_Context,simplification_tolerance=8, minimum_area=None, conflict_option=True)

# <codecell>

arcpy.SimplifyBuilding_cartography(CQ,Simple_CQ,simplification_tolerance=8, minimum_area=None, conflict_option=True)

# <markdowncell>

# ###Definition of areas of factors of Areas exposed to sun

# <markdowncell>

# 1.1.Create points in the centroid of segment line and table with near features: indentifying for each segment of line of building A the segment of line of building B in common. 

# <codecell>

arcpy.FeatureToLine_management(Simple_CQ,CQLines)
arcpy.FeatureVerticesToPoints_management(Simple_CQ,CQVertices,'ALL')
arcpy.SplitLineAtPoint_management(CQLines,CQVertices,CQSegments,'2 METERS')
arcpy.FeatureVerticesToPoints_management(CQSegments,CQSegments_centroid,'MID')

# <codecell>

arcpy.GenerateNearTable_analysis(CQSegments_centroid,CQSegments_centroid,NearTable,"1 Meters","NO_LOCATION","NO_ANGLE","CLOSEST","0")

# <markdowncell>

# 1.2. Import the table with NearMatches

# <codecell>

NearMatches = dbf2df(NearTable)
NearMatches

# <markdowncell>

# 1.3. Import the table with attributes of the centroids of the Segments

# <codecell>

OutTable = 'CentroidCQdata.dbf'
arcpy.TableToTable_conversion(CQSegments_centroid, temporal1, OutTable)
DataCentroids = dbf2df(temporal1+'\\'+OutTable, cols={'Name','height','ORIG_FID'})
print DataCentroids.ORIG_FID

# <markdowncell>

# 1.3. CreateJoin to Assign a Factor to every Centroid of the lines, FactorShade =0 if the line exist in a building totally covered by another one, and Freeheight = to the height of the line that is not obstructed by the other building

# <codecell>

FirstJoin = pd.merge(NearMatches,DataCentroids,left_on='IN_FID', right_on='ORIG_FID')
SecondaryJoin = pd.merge(FirstJoin,DataCentroids,left_on='NEAR_FID', right_on='ORIG_FID')

# <codecell>

print SecondaryJoin.head()

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


# <markdowncell>

# 1.4 Create and export Secondary Join with results, it will be Useful for the Chapter "Observation Points'

# <codecell>

SecondaryJoin.to_csv(Overlaptable,index=False)

# <markdowncell>

# 1.4. Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without shading boundaries these factors are equal to 1 and the field height respectively

# <codecell>

DataCentroids['FactorShade'] = 1
DataCentroids['Freeheight'] = DataCentroids['height']
rows = SecondaryJoin.IN_FID.count()
rows2 = DataCentroids.ORIG_FID.count()

# <codecell>

for row in range(rows):
    for row2 in range(rows2):
        if SecondaryJoin.loc[row,'ORIG_FID_x'] == DataCentroids.loc[row2,'ORIG_FID']:
            DataCentroids.loc[row2,'FactorShade'] = SecondaryJoin.loc[row,'FactorShade']
            DataCentroids.loc[row2,'Freeheight'] = SecondaryJoin.loc[row,'Freeheight']

# <codecell>

print DataCentroids.FactorShade

# <codecell>

DataCentroids.to_csv(DataCentroidsCSV,index=False)

# <markdowncell>

# ###Buildings into DEM

# <markdowncell>

# 1.1. Create a raster with all the buildings

# <codecell>

Outraster = r'c:\ArcGIS\EDM.gdb\AllRaster'
arcpy.env.extent = '676682, 218586, 684612, 229286' #These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
arcpy.FeatureToRaster_conversion(Simple_Context,'height',Outraster,'0.5') #creating raster of the footprints of the buildings

# <markdowncell>

# 1.2. clear non values and add all the Buildings to the DEM 

# <codecell>

OutNullRas =IsNull(Outraster) # identify noData Locations
Output = Con(OutNullRas == 1,0,Outraster)
RadiationDEM = Raster(DEModel) + Output
RadiationDEM.save(r'c:\ArcGIS\EDM.gdb\DEM_All')

# <markdowncell>

# ###Observation Points 

# <markdowncell>

# 2.1. First increase the boundaries in 2m of each surface in the community to analyze- this will avoid that the observers overlap the buildings and Simplify the community vertices to only create 1 point per surface

# <codecell>

arcpy.Buffer_analysis(Simple_CQ,Buffer_CQ,buffer_distance_or_field=3, line_end_type='FLAT') # buffer with a flat finishing
arcpy.Generalize_edit(Buffer_CQ,"2 METERS")

# <markdowncell>

# 2.2. Transform all polygons of the Areas to points or observation points

# <codecell>

arcpy.SplitLine_management(Buffer_CQ,temporal_lines)
arcpy.FeatureVerticesToPoints_management(temporal_lines,Points,'MID') # Second the transformation of Lines to a mid point

# <markdowncell>

# 2.3. Join all the polygons to get extra vertices, make lines and then get points. these points should be added to the original observation points in 2.2

# <codecell>

arcpy.AggregatePolygons_cartography(Buffer_CQ,AggregatedBuffer,"0.5 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL") # agregate polygons
arcpy.SplitLine_management(AggregatedBuffer,temporal_lines3) #make lines
arcpy.FeatureVerticesToPoints_management(temporal_lines3,Points3,'MID')# create extra points

# <codecell>

Points3Updated = temporal2+'\\temp\\'+'Points3Updated'
arcpy.SpatialJoin_analysis(Points3,Buffer_CQ,Points3Updated,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST")# add information to Points3 about their buildings

# <codecell>

arcpy.Erase_analysis(Points3Updated,Points,EraseObservers,"2 Meters")# erase overlaping points
arcpy.Merge_management([Points,EraseObservers],Observers)# erase overlaping points

# <markdowncell>

# 2.4. Eliminate Observation points above roofs of the highest surfaces(a trick to make the spatial selection of exposed surfaces and radiation points congruent, according to the first Chapter

# <codecell>

#Import Secondary Join containing the data about buildings overlaping, eleiminate duplicades, chose only those ones no overlaped and reindex
DataNear = pd.read_csv(Overlaptable)
CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
CleanDataNear.drop_duplicates(cols='Name_x',inplace=True)
CleanDataNear.reset_index(inplace=True)
print CleanDataNear.head()

# <codecell>

rows = CleanDataNear.Name_x.count()
for row in range(rows):
    Field = "Name" # select field where the name exists to iterate
    Value = CleanDataNear.loc[row,'Name_x'] # set the value or name of the City quarter
    Where_clausule =  ''''''+'"'+Field+'"'+"="+"\'"+str(Value)+"\'"+'''''' # strange writing to introduce in ArcGIS
    if row == 0:
        arcpy.MakeFeatureLayer_management(Simple_CQ, 'Simple_lyr')
        arcpy.SelectLayerByAttribute_management('Simple_lyr',"NEW_SELECTION",Where_clausule)
    else:
        arcpy.SelectLayerByAttribute_management('Simple_lyr',"ADD_TO_SELECTION",Where_clausule)
        
    arcpy.CopyFeatures_management('simple_lyr', NonoverlappingBuildings)

# <codecell>

arcpy.ErasePoint_edit(Observers,NonoverlappingBuildings,"INSIDE")

# <markdowncell>

# ###Hourly radiation

# <markdowncell>

# 3.2. Create a Directory for the Community to analyse

# <codecell>

if not os.path.exists(r'c:\ArcGIS\temp'+'\\'+CQ_name):
    os.makedirs(r'c:\ArcGIS\temp'+'\\'+CQ_name)
if not os.path.exists(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'):
    os.makedirs(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global')
if not os.path.exists(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Direct'):
    os.makedirs(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Direct')

# <markdowncell>

# 3.3. Create radiation in the surfaces per hour and return shading factors for each point  - Considering Buildings

# <codecell>

#Initialize variable in the function
for day in range(1,366):
    GlobalRadiation = r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'+'\\'+'Day_'+str(day)+'.shp'
    DirectRadiation = r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Direct'+'\\'+'Day_'+str(day)+'.shp'
    timeConfig =  'WithinDay    '+str(day)+', 0, 24'
    arcpy.gp.PointsSolarRadiation_sa(DEModelFinal,Points,GlobalRadiation,heightoffset,latitude,skySize,timeConfig,dayInterval,hourInterval,"INTERVAL","1","FROM_DEM",calcDirections,zenithDivisions,azimuthDivisions,"STANDARD_OVERCAST_SKY",diffuseProp,transmittivity,DirectRadiation,"#","#")
    Radiation = dbf2df(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'+'\\'+'Day_'+str(day)+'.dbf') #obtain file form the model with buildings
    #Obtain the number of points modeled to do the iterations
    Radiation['ID'] = 0
    Counter = Radiation.ID.count()
    Value = Counter + 1
    Radiation['ID'] = range(1,Value)
    #function to include all the hours and compude final table
    RadiationClean =  Calctable(day,Radiation)
    #Append to create a table with all the values of the year
    if day == 1:
        RadiationClean.to_csv(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'+'\\'+'Day_'+str(day)+'.csv')#Export the Results
        Radiationyear = pd.read_csv(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'+'\\'+'Day_'+str(day)+'.csv')
    else:
        Radiationyear = Radiationyear.merge(RadiationClean, on='ID')

Radiationyear.to_csv(r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'Global'+'\\'+'RadiationYear.csv',Index=False)

# <markdowncell>

# ###Radiation to Surfaces

# <markdowncell>

# 4.1 Create Join of features Observers and CQ_sementscentroids to assign Names and IDS of observers (field ORIG_ID) to the centroids of the lines of the buildings, then create a table to import as a Dataframe

# <codecell>

Outjoin = temporal2+'\\temp\\'+'Join'
arcpy.SpatialJoin_analysis(CQSegments_centroid,Observers,Outjoin,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST")

# <codecell>

arcpy.JoinField_management(Outjoin,'OBJECTID',CQSegments, 'OBJECTID') # add the lenghts of the Lines to the File

# <codecell>

OutTable = 'CentroidsIDobserv.dbf'
arcpy.TableToTable_conversion(Outjoin, temporal1, OutTable)
Centroids_ID_observers = dbf2df(temporal1+'\\'+OutTable, cols={'Name_1','height','ORIG_FID','Shape_Leng'})

# <markdowncell>

# 4.2 Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.

# <codecell>

Datacentroids = pd.read_csv(DataCentroidsCSV)
DataCentroidsFull = pd.merge(Centroids_ID_observers,Datacentroids,left_index=True,right_index=True)

# <markdowncell>

# 4.1. Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...

# <codecell>

Radiationtable = pd.read_csv(temporal1+'\\'+CQ_name+'\\'+'Global'+'\\'+'RadiationYear.csv',index_col='Unnamed: 0.1')
DataRadiation = pd.merge(DataCentroidsFull,Radiationtable, left_on='ORIG_FID_x',right_on='ID')

# <codecell>

DataRadiation.to_csv(DataradiationLocation,index=False)

