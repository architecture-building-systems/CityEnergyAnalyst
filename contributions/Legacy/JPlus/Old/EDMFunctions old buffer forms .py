# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ##MODULES

# <codecell>

import arcpy
from arcpy import sa
import sys,os
import pandas as pd
import datetime
import jdcal
import numpy as np
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <markdowncell>

# #FUNCTIONS

# <markdowncell>

# ##RADIATION MODEL

# <markdowncell>

# ###1. Calculation of hourly radiation in a day

# <codecell>

def CalcRadiation(day, CQ_name, DEMfinal, Observers, T_G_day, latitude, locationtemp1, longitude, timezone):
    # Local Variables
    Latitude = str(latitude)
    skySize = '3000'
    dayInterval = '1'
    hourInterval = '1'
    calcDirections = '32'
    zenithDivisions = '1500'
    azimuthDivisions = '160'
    diffuseProp =  str(T_G_day.loc[day-1,'diff'])
    transmittivity =  str(T_G_day.loc[day-1,'ttr'])
    heightoffset = '5'
    global_radiation = locationtemp1+'\\'+CQ_name+'\\'+'radiation'+'\\'+'Day_'+str(day)+'.shp'
    timeConfig =  'WithinDay    '+str(day)+', 0, 24'
    
     #Run the extension of arcgis
    arcpy.gp.PointsSolarRadiation_sa(DEMfinal, Observers, global_radiation, heightoffset,
        Latitude, skySize, timeConfig, dayInterval, hourInterval, "INTERVAL", "1", "FROM_DEM",
       calcDirections, zenithDivisions, azimuthDivisions, "STANDARD_OVERCAST_SKY",
        diffuseProp, transmittivity, "#", "#", "#")
    
    radiation_sunnyhours = dbf2df(locationtemp1+'\\'+CQ_name+'\\'+'radiation'+'\\'+'Day_'+str(day)+'.dbf') #obtain file form the model with buildings
    
    #Obtain the number of points modeled to do the iterations
    radiation_sunnyhours['ID'] = 0
    counter = radiation_sunnyhours.ID.count()
    value = counter+1
    radiation_sunnyhours['ID'] = range(1, value)
    
    #function to include all the hours and compude final table
    radiation_day = calc_radiationday(day, radiation_sunnyhours, longitude, latitude, timezone)
    return radiation_day

# <markdowncell>

# 1.1 Sub-function to calculate radiation non-sunshinehours

# <codecell>

def calc_radiationday(day, radiation_sunnyhours, longitude, latitude, timezone):
    # Table with empty values with the same range as the points.
    Table = pd.DataFrame.copy(radiation_sunnyhours)
    Names = ['T0','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16','T17','T18','T19','T20','T21','T22','T23']
    for Name in Names:
        Table[Name]= 0
    #Counter of Columns in the Initial Table
    Counter = radiation_sunnyhours.count(1)
    Value = Counter[0]-1
    #Condition to take into account daysavingtime in Switzerland as the radiation data in ArcGIS is calculated for 2013.    
    if 90 <= day <300: 
        D = 1
    else:
        D = 0 
    # Calculation of Sunrise time
    Sunrise_time = calc_sunrise(day,longitude, latitude, timezone) + D
    # Calculation of table
    for time in range(Value):
        Hour = int(Sunrise_time)+ int(time)
        Table['T'+str(Hour)] = radiation_sunnyhours['T'+str(time)]
    #rename the table for every T to get in 1 to 8760 hours.
    if day == 1:
        name = 1
    else:
        name = int(day-1)*24+1
    
    Table.rename(columns={'T0':'T'+str(name),'T1':'T'+str(name+1),'T2':'T'+str(name+2),'T3':'T'+str(name+3),'T4':'T'+str(name+4),
                                    'T5':'T'+str(name+5),'T6':'T'+str(name+6),'T7':'T'+str(name+7),'T8':'T'+str(name+8),'T9':'T'+str(name+9),
                                    'T10':'T'+str(name+10),'T11':'T'+str(name+11),'T12':'T'+str(name+12),'T13':'T'+str(name+13),'T14':'T'+str(name+14),
                                    'T15':'T'+str(name+15),'T16':'T'+str(name+16),'T17':'T'+str(name+17),'T18':'T'+str(name+18),'T19':'T'+str(name+19),
                                    'T20':'T'+str(name+20),'T21':'T'+str(name+21),'T22':'T'+str(name+22),'T23':'T'+str(name+23),'ID':'ID'},inplace=True)
    return Table

# <markdowncell>

# 1.2 Sub-Function to calculate Sunrise hour

# <codecell>

def calc_sunrise(day,longitude, latitude, timezone): # Calculated according to NOAA website
    # Calculate Date and Julian day
    Date = datetime.datetime(2013, 1, 1) + datetime.timedelta(day - 1)
    JuliandDay = sum(jdcal.gcal2jd(Date.year, Date.month, Date.day))
    JulianCentury = (JuliandDay-2451545)/36525
    # Calculate variables for sunrise
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
    HA_sunrise = np.degrees(np.arccos(np.cos(np.radians(90.833))/(np.cos(np.radians(latitude))*np.cos(np.radians(SunDeclinationAngle)))-np.tan(np.radians(latitude))*np.tan(np.radians(SunDeclinationAngle))))
    Solar_noon =(720-4*longitude-EOT+timezone*60)/1440
    Sun_rise = (Solar_noon-HA_sunrise*4/1440)*24
    return Sun_rise

# <markdowncell>

# ###2. Burn buildings into DEM

# <codecell>

def Burn(Buildings,DEM,DEMfinal,locationtemp1, locationtemp2, database,  DEM_extent = '676682, 218586, 684612, 229286'):

    #Create a raster with all the buildings
    Outraster = locationtemp1+'\\'+'AllRaster'
    arcpy.env.extent = DEM_extent #These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
    arcpy.FeatureToRaster_conversion(Buildings,'height',Outraster,'0.5') #creating raster of the footprints of the buildings
    
    #Clear non values and add all the Buildings to the DEM 
    OutNullRas = sa.IsNull(Outraster) # identify noData Locations
    Output = sa.Con(OutNullRas == 1,0,Outraster)
    RadiationDEM = sa.Raster(DEM) + Output
    RadiationDEM.save(DEMfinal)
    return arcpy.GetMessages()

# <markdowncell>

# ###3. Calculate Boundaries - Factor Height and Factor Shade

# <codecell>

def CalcBoundaries (Simple_CQ,locationtemp1, locationtemp2, DataFactorsCentroids, DataFactorsBoundaries):
    #local variables
    NearTable = locationtemp1+'\\'+'NearTable.dbf'
    CQLines = locationtemp2+'\\'+'\CQLines'
    CQVertices = locationtemp2+'\\'+'CQVertices'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    centroidsTable_name = 'CentroidCQdata.dbf'
    centroidsTable = locationtemp1+'\\'+centroidsTable_name
    Overlaptable = locationtemp1+'\\'+'overlapingTable.csv'
    
    #Create points in the centroid of segment line and table with near features: 
    # indentifying for each segment of line of building A the segment of line of building B in common.  
    arcpy.FeatureToLine_management(Simple_CQ,CQLines)
    arcpy.FeatureVerticesToPoints_management(Simple_CQ,CQVertices,'ALL')
    arcpy.SplitLineAtPoint_management(CQLines,CQVertices,CQSegments,'2 METERS')
    arcpy.FeatureVerticesToPoints_management(CQSegments,CQSegments_centroid,'MID')
    arcpy.GenerateNearTable_analysis(CQSegments_centroid,CQSegments_centroid,NearTable,"1 Meters","NO_LOCATION","NO_ANGLE","CLOSEST","0")
    
    #Import the table with NearMatches
    NearMatches = dbf2df(NearTable)
    
    # Import the table with attributes of the centroids of the Segments
    arcpy.TableToTable_conversion(CQSegments_centroid, locationtemp1, centroidsTable_name)
    DataCentroids = dbf2df(centroidsTable, cols={'Name','height','ORIG_FID'})
    
    # CreateJoin to Assign a Factor to every Centroid of the lines,
    FirstJoin = pd.merge(NearMatches,DataCentroids,left_on='IN_FID', right_on='ORIG_FID')
    SecondaryJoin = pd.merge(FirstJoin,DataCentroids,left_on='NEAR_FID', right_on='ORIG_FID')
    
    # delete matches within the same polygon Name (it can happen that lines are too close one to the other)
    # also delete matches with a distance of more than 20 cm making room for mistakes during the simplicfication of buildings but avoiding deleten boundaries 
    rows = SecondaryJoin.IN_FID.count()
    for row in range(rows):
        if SecondaryJoin.loc[row,'Name_x'] == SecondaryJoin.loc[row,'Name_y'] or SecondaryJoin.loc[row,'NEAR_DIST'] > 0.2:
           SecondaryJoin = SecondaryJoin.drop(row)
    SecondaryJoin.reset_index(inplace=True)
    
    #FactorShade = 0 if the line exist in a building totally covered by another one, and Freeheight is equal to the height of the line 
    # that is not obstructed by the other building
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
        
    #Create and export Secondary Join with results, it will be Useful for the function CalcObservers
    SecondaryJoin.to_csv(DataFactorsBoundaries,index=False)
    
    #Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without
    #shading boundaries these factors are equal to 1 and the field 'height' respectively.
    DataCentroids['FactorShade'] = 1
    DataCentroids['Freeheight'] = DataCentroids['height']
    Results = DataCentroids.merge(SecondaryJoin, left_on='ORIG_FID', right_on='ORIG_FID_x', how='outer')
    Results.FactorShade_y.fillna(results['FactorShade_x'],inplace=True)
    Results.Freeheight_y.fillna(results['Freeheight_x'],inplace=True)
    Results.rename(columns={'FactorShade_y':'FactorShade','Freeheight_y':'Freeheight'},inplace=True)
    FinalDataCentroids = pd.DataFrame(Results,columns={'ORIG_FID','height','FactorShade','Freeheight'})
            
    FinalDataCentroids.to_csv(DataFactorsCentroids,index=False)
    return arcpy.GetMessages()

# <markdowncell>

# ###4. Calculate observation points

# <codecell>

def CalcObservers(Simple_CQ,Observers, DataFactorsBoundaries, locationtemporal2):
    #local variables
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
    #First increase the boundaries in 2m of each surface in the community to 
    #analyze- this will avoid that the observers overlap the buildings and Simplify 
    #the community vertices to only create 1 point per surface
    arcpy.Buffer_analysis(Simple_CQ,Buffer_CQ,buffer_distance_or_field=1, line_end_type='FLAT') # buffer with a flat finishing
    arcpy.Generalize_edit(Buffer_CQ,"2 METERS")
    
    #Transform all polygons of the simplified areas to observation points
    arcpy.SplitLine_management(Buffer_CQ,temporal_lines)
    arcpy.FeatureVerticesToPoints_management(temporal_lines,Points,'MID') # Second the transformation of Lines to a mid point
    
    #Join all the polygons to get extra vertices, make lines and then get points. 
    #these points should be added to the original observation points
    arcpy.AggregatePolygons_cartography(Buffer_CQ,AggregatedBuffer,"0.5 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL") # agregate polygons
    arcpy.SplitLine_management(AggregatedBuffer,temporal_lines3) #make lines
    arcpy.FeatureVerticesToPoints_management(temporal_lines3,Points3,'MID')# create extra points
    
    # add information to Points3 about their buildings
    arcpy.SpatialJoin_analysis(Points3,Buffer_CQ,Points3Updated,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST")
    arcpy.Erase_analysis(Points3Updated,Points,EraseObservers,"2 Meters")# erase overlaping points
    arcpy.Merge_management([Points,EraseObservers],Observers)# erase overlaping points
    
    #  Eliminate Observation points above roofs of the highest surfaces(a trick to make the 
    #Import Overlaptable from function CalcBoundaries containing the data about buildings overlaping, eliminate duplicades, chose only those ones no overlaped and reindex
    DataNear = pd.read_csv(DataFactorsBoundaries)
    CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
    CleanDataNear.drop_duplicates(cols='Name_x',inplace=True)
    CleanDataNear.reset_index(inplace=True)
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
        
    arcpy.ErasePoint_edit(Observers,NonoverlappingBuildings,"INSIDE")
    return arcpy.GetMessages()

# <markdowncell>

# ###5. Radiation results to surfaces

# <codecell>

def CalcRadiationSurfaces(Observers, Radiationyearfinal, DataFactorsObservers, DataradiationLocation,  locationtemp1, locationtemp2):
    # local variables
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    Outjoin = locationtemp2+'\\'+'Join'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    OutTable = 'CentroidsIDobserv.dbf'
    # Create Join of features Observers and CQ_sementscentroids to 
    # assign Names and IDS of observers (field ORIG_ID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid,Observers,Outjoin,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST")
    arcpy.JoinField_management(Outjoin,'OBJECTID',CQSegments, 'OBJECTID') # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, locationtemp1, OutTable)
    Centroids_ID_observers = dbf2df(locationtemp1+'\\'+OutTable, cols={'Name_1','height','ORIG_FID','Shape_Leng'})
    
    #Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(DataFactorsObservers)
    DataCentroidsFull = pd.merge(Centroids_ID_observers,Datacentroids,left_index=True,right_index=True)
    
    #Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    Radiationtable = pd.read_csv(DataradiationLocation,index_col='Unnamed: 0')
    DataRadiation = pd.merge(DataCentroidsFull,Radiationtable, left_on='ORIG_FID_x',right_on='ID')
    
    DataRadiation.to_csv(Radiationyearfinal,index=False)
    return arcpy.GetMessages()

# <markdowncell>

# ##DETERMINISTIC ENERGY MODEL

# <markdowncell>

# ###1. Thermal properties and geometry of buildings

# <codecell>

def CalcAreas(CQ, CQproperties, Radiationyearfinal,locationtemp1):
    #Local Variables
    OutTable = 'CQshape3.dbf'
    
    # Set of estimated constants
    Z = 3 # height of basement for every building in m
    
    #Import RadiationFile and Properties of the shapefiles
    Radiation_Shading = pd.read_csv(Radiationyearfinal)
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    CQShape_properties = dbf2df(locationtemp1+'\\'+OutTable)
    
    #Areas above ground #get the area of each wall in the buildings
    Radiation_Shading['Awall'] = Radiation_Shading['Shape_Leng']*Radiation_Shading['Freeheight']*Radiation_Shading['FactorShade'] 
    PivotTable = pd.pivot_table(Radiation_Shading,rows='Name',values='Awall',aggfunc=np.sum) #get the area of walls in the whole buildings
    PivotTable2 = pd.DataFrame(PivotTable)
    
    CQproperties2 = pd.merge(PivotTable2,CQproperties, left_index=True,right_on='Name')
    CQproperties2['Aw'] = CQproperties2['Awall']*CQproperties2['fwindow'] # Finally get the Area of windows 
    CQproperties2['Aop_sup'] = CQproperties2['Awall']*CQproperties2['AFloor'] - CQproperties2['Aw'] #....and Opaque areas AFloor represents a factor according to the amount of floors heated
    
    #Areas bellow ground
    AllProperties = pd.merge(CQproperties2,CQShape_properties,on='Name')# Join both properties files (Shape and areas)
    AllProperties['Aop_bel'] = Z*AllProperties['Shape_Leng']+AllProperties['Shape_Area']   # Opague areas in m2 below ground including floor
    AllProperties['Atot'] = AllProperties['Aop_sup']+AllProperties['Aop_bel']+AllProperties['Aw']+AllProperties['Shape_Area'] # Total area of the building envelope m2, it is considered the roof to be flat
    AllProperties['Af'] = AllProperties['Shape_Area']*AllProperties['Floors_x']*AllProperties['Hs_x'] # conditioned area
    AllProperties['Am'] = AllProperties.Construction.apply(lambda x:AmFunction(x))*AllProperties['Af'] # Effective mass area in m2

    return AllProperties

# <codecell>

def CalcIncidentRadiation(AllProperties, Radiationyearfinal):

    #Import Radiation table and compute the Irradiation in W in every building's surface
    Radiation_Shading2 = pd.read_csv(Radiationyearfinal)
    Columns = 8761
    for Column in range(1, Columns):
         #transform all the points of solar radiation into Wh
        Radiation_Shading2['T'+str(Column)] = Radiation_Shading2['T'+str(Column)]*Radiation_Shading2['Shape_Leng']*Radiation_Shading2['FactorShade']*Radiation_Shading2['Freeheight']
    
    #Do pivot table to sum up the irradiation in every surface to the building 
    #and merge the result with the table allProperties
    PivotTable3 = pd.pivot_table(Radiation_Shading2,rows='Name',margins='Add all row')
    RadiationLoad = pd.DataFrame(PivotTable3)
    Solar = AllProperties.merge(RadiationLoad, left_on='Name',right_index=True)
    
    #final step multiply the total irradiation in the building per the percentage of Window/wall area to get the result
    for Column in range(1, Columns):
        Solar['T'+str(Column)] = Solar['T'+str(Column)]*Solar['fwindow']
    
    return Solar

# <codecell>

def CalcThermalProperties(AllProperties):
    #local variables
    # Set of constants according to EN 13790
    his = 3.45 #heat transfer coefficient between air and the surfacein W/(m2K)
    hms = 9.1 # Heat transfer coeddicient between nodes m and s in W/m2K        
    
    # Set of estimated constants
    Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1

    #Steady-state Thermal transmittance coefficients and Internal heat Capacity
    AllProperties ['Htr_w'] = AllProperties['Aw']*AllProperties['Uwindow']  # Thermal transmission coefficient for windows and glazing. in W/K
    AllProperties ['HD'] = AllProperties['Aop_sup']*AllProperties['Uwall']+AllProperties['Shape_Area']*AllProperties['Uroof']  # Direct Thermal transmission coefficient to the external environment in W/K
    AllProperties ['Hg'] = Bf*AllProperties ['Aop_bel']*AllProperties['Uground'] # stady-state Thermal transmission coeffcient to the ground. in W/K
    AllProperties ['Htr_op'] = AllProperties ['Hg']+ AllProperties ['HD']
    AllProperties ['Htr_ms'] = hms*AllProperties ['Am'] # Coupling conduntance 1 in W/K
    AllProperties ['Htr_em'] = 1/(1/AllProperties['Htr_op']-1/ AllProperties['Htr_ms']) # Coupling conduntance 2 in W/K 
    AllProperties ['Htr_is'] = his*AllProperties ['Atot']
    AllProperties['Cm'] = AllProperties.Construction.apply(lambda x:CmFunction(x))*AllProperties['Af'] # Internal heat capacity in J/K
    return AllProperties

# <markdowncell>

# 1.1 Sub-functions of  Thermal mass

# <codecell>

def CmFunction (x): 
    if x == 'Medium':
        return 165000
    elif x == 'Heavy':
        return 300000
    elif x == 'Light':
        return 110000
    else:
        return 165000

# <codecell>

def AmFunction (x): 
    if x == 'Medium':
        return 2.5
    elif x == 'Heavy':
        return 3.2
    elif x == 'Light':
        return 2.5
    else:
        return 2.5

# <markdowncell>

# 1.2. Sub- Function Hourly thermal transmission coefficients

# <codecell>

def calc_Htr(Hve, Htr_is, Htr_ms, Htr_w):
    Htr_1 = 1/(1/Hve+1/Htr_is)
    Htr_2 = Htr_1+Htr_w
    Htr_3 = 1/(1/Htr_2+1/Htr_ms)
    Coefficients = [Htr_1,Htr_2,Htr_3]
    return Coefficients

# <markdowncell>

# ###2. Calculation of thermal loads

# <codecell>

def CalcThermalLoads(i, AllProperties, locationFinal, Solar, Profiles,Profiles_names, Temp, Losses, Servers): # Mode is a variable 0 without losses, 1 With losses of distribution enmission and control
    #Local Variables
    Name = AllProperties.loc[i,'Name']
    
    # Set of constants according to EN 13790
    g_gl = 0.9*0.75 # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows to be double glazing (0.75)
    pa_ca = 1200  # Air constant J/m3K   
    F_f = 0.3 # Frame area faction coefficient
    
    # Determination of Profile of occupancy to use
    Occupancy = calc_Type(Profiles,Profiles_names, AllProperties, i, Servers)
              
    #Create Labels in data framte to iterate
    Columns = ['IH_nd_ac','IC_nd_ac','Fsh_gl','Htr_1','Htr_2','Htr_3','tm_t','tair_ac','top_ac','IHC_nd_ac', 'Asol', 'I_sol','te']
    for Label in Columns:
        Occupancy [Label] = 0
    
    #Assign temperature data to the table
    Occupancy['te'] = Temp['te']
        
    # Determination of Hourly Thermal transmission coefficient due to Ventilation in W/K
    Occupancy['Hve'] =  pa_ca*Occupancy['Ve']* AllProperties.loc[i,'Af']/3600
    
    #Determination of Heat Flows for internal loads in W
    Occupancy['I_ia'] = 0.5*Occupancy['I_int']*AllProperties.loc[i,'Af']
    
    # Calculation of effecive solar area of surfaces in m2, opaque areas are not considered, reduction factor of overhangs is not included. Fov =0
    Num_Hours = Occupancy.DATE.count()
    for hour in range(Num_Hours):

        # Calculation Shading factor per hour due to operation of external shadings, 1 when I > 300 W/m2
        Rf_sh = Calc_Rf_sh(AllProperties.loc[i,'Shading_position'],AllProperties.loc[i,'Shading_Type'])
        Occupancy.loc[hour,'Fsh_gl'] = calc_Fsh_gl(Solar.loc[i,'T'+str(hour+1)],AllProperties.loc[i,'Aw'], g_gl,Rf_sh)

        # Calculation of solar efective area per hour in m2  
        Occupancy.loc[hour,'Asol'] = Occupancy.loc[hour,'Fsh_gl']*g_gl*(1-F_f)*AllProperties.loc[i,'Aw']
    
        # Calculation of Solar gains in each facade in W it is neglected the extraflow of radiation from the surface to the exterior Fr_k*Ir_k = 0 as well as gains in opaque surfaces
        Occupancy.loc[hour,'I_sol'] = Occupancy.loc[hour,'Asol']*(Solar.loc[i,'T'+str(hour+1)]/AllProperties.loc[i,'Aw'])#-Fr*AllProperties.loc[i,'Aw_N']*AllProperties.loc[i,'Uwindow']*delta_t_er*hr*Rse
        
        # Determination of Hourly thermal transmission coefficients for Determination of operation air temperatures in W/K
        Coefficients = calc_Htr(Occupancy.loc[hour,'Hve'], AllProperties.loc[i,'Htr_is'], AllProperties.loc[i,'Htr_ms'], AllProperties.loc[i,'Htr_w'])
        Occupancy.loc[hour,'Htr_1'] = Coefficients[0]
        Occupancy.loc[hour,'Htr_2'] = Coefficients[1]
        Occupancy.loc[hour,'Htr_3'] = Coefficients[2]
  
    # Determination of Heat Flows for internal heat sources
    Occupancy['I_m'] = (AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])*(Occupancy['I_ia']+Occupancy['I_sol'])
    Occupancy['I_st'] = (1-(AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])-(AllProperties.loc[i,'Htr_w']/(9.1*AllProperties.loc[i,'Atot'])))*(Occupancy['I_ia']+Occupancy['I_sol'])
    
    # factors of Losses due to emission of systems vector hot or cold water for heating and cooling
    tHC_corr = [0,0]
    tHC_corr = calc_Qem_ls(AllProperties.loc[i,'Emission_heating'],AllProperties.loc[i,'Emission_cooling'])
    tHset_corr = tHC_corr[0]
    tCset_corr = tHC_corr[1]
    # Seed for calculation
    Occupancy.loc[0,'tm_t'] = Occupancy.loc[0,'te']
    for j in range(1,Num_Hours):  #mode = 0 
        # Determination of net thermal loads and temperatures
        Results = calc_TL(Occupancy.loc[j-1,'tm_t'], Occupancy.loc[j,'te'], Occupancy.loc[j,'tintH_set'],
                          Occupancy.loc[j,'tintC_set'],AllProperties.loc[i,'Htr_em'],AllProperties.loc[i,'Htr_ms'], 
                          AllProperties.loc[i,'Htr_is'],Occupancy.loc[j,'Htr_1'], Occupancy.loc[j,'Htr_2'], 
                          Occupancy.loc[j,'Htr_3'], Occupancy.loc[j,'I_st'], Occupancy.loc[j,'Hve'], 
                          AllProperties.loc[i,'Htr_w'], Occupancy.loc[j,'I_ia'], Occupancy.loc[j,'I_m'], 
                          AllProperties.loc[i,'Cm'], AllProperties.loc[i,'Af'], AllProperties.loc[i,'IC_max'], 
                          AllProperties.loc[i,'IH_max'],Losses,tHset_corr,tCset_corr)
        Occupancy.loc[j,'tm_t'] = Results[0]
        Occupancy.loc[j,'tair_ac'] = Results[1] # temperature of inside air
        Occupancy.loc[j,'top_ac'] = Results[2] # temperature of operation
        Occupancy.loc[j,'IH_nd_ac'] = Results[3] # net heating load
        Occupancy.loc[j,'IC_nd_ac'] = Results[4] # net cooling load
    
    # Results
    Result_Thermalloads = pd.DataFrame(Occupancy,columns = ['IH_nd_ac','IC_nd_ac','tair0','top','te'])
        
    # EXPORT RESULTS
    Occupancy.to_csv(locationFinal+'\\'+Name+'.csv')
    return Result_Thermalloads

# <markdowncell>

# 2.1. Sub-Function Hourly thermal load

# <codecell>

def calc_TL(tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, IC, IH, Losses, tHset_corr,tCset_corr):
    if Losses == 1:
        #Losses due to emission and distribution of systems
        tintH_set = tintH_set + tHset_corr
        tintC_set = tintC_set + tCset_corr
    if Af >0:
        # Case 1 IHC_nd = 0
        IHC_nd = 0
        IC_nd_ac = 0
        IH_nd_ac = 0
        Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2
        tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
        tm = (tm_t+tm_t0)/2
        ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)  
        tair0 = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
        top0 = 0.3*tair0+0.7*ts
        if (tintH_set <= tair0) and (tair0<=tintC_set): 
            tair_ac = tair0 
            top_ac = top0
            IHC_nd_ac = 0
            IH_nd_ac = IHC_nd_ac
            IC_nd_ac = IHC_nd_ac
        else:
            if tair0 > tintC_set:
                tair_set = tintC_set
            else:
                tair_set = tintH_set
            
            # Case 2 IHC_nd = 10 * Af  
            IHC_nd = IHC_nd_10 = 10*Af
            Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2
            tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
            tm = (tm_t+tm_t0)/2
            ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)  
            tair10 = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
            top10 = 0.3*tair10+0.7*ts
            IHC_nd_un =  IHC_nd_10*(tair_set - tair0)/(tair10-tair0)
            IC_max = -IC*Af
            IH_max = IH*Af
            if  IC_max < IHC_nd_un < IH_max:
                tair_ac = tair_set 
                top_ac = 0.3*tair_ac+0.7*ts
                IHC_nd_ac = IHC_nd_un 
            else:
                if IHC_nd_un > 0:
                    IHC_nd_ac = IH_max
                else:
                    IHC_nd_ac = IC_max
                # Case 3 when the maximum power is exceeded
                Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd_ac)/Hve)+ te_t))/Htr_2
                tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
                tm = (tm_t+tm_t0)/2
                ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd_ac)/Hve))/(Htr_ms+Htr_w+Htr_1)  
                tair_ac = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
                top_ac = 0.3*tair_ac+0.7*ts
           # Results
            if IHC_nd_ac > 0:
                IH_nd_ac = IHC_nd_ac
            else:
                IC_nd_ac = IHC_nd_ac
    
        Results = [tm_t, tair_ac ,top_ac, IH_nd_ac, IC_nd_ac]
    else:
        Results = [0 , 0 , 0, 0, 0]
    return Results

# <markdowncell>

# 2.1. Sub-Function Shading Factors of movebale parts

# <codecell>

#It calculates the rediction factor of shading due to type of shading
def Calc_Rf_sh (ShadingPosition,ShadingType):
    d ={'Type':['Louvres','Rollo', 'Venetian Blinds', 'Courtain'],'ValueIN':[0.2,0.2,0.3,0.77],'ValueOUT':[0.08,0.08,0.15,0.57]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Exterior':
            return ValuesRf_Table.loc[row,'ValueOUT']
        elif ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Interior':
            return ValuesRf_Table.loc[row,'ValueIN']
        else:
            return 1

# <codecell>

def calc_Fsh_gl(Iwindows, Aw, g_gl,Rf_sh):
    if Iwindows/Aw > 300:
        Fsh_with = 1
        return ((1-Fsh_with)*g_gl+Fsh_with*g_gl*Rf_sh)/g_gl
    else:
        return 1

# <markdowncell>

# 2.2. Sub-Function equivalent profile of Occupancy

# <codecell>

def calc_Type(Profiles, Profiles_names, AllProperties, i, Servers):
    profiles_num = len(Profiles)
    if Servers == 0:
        Profiles[1] = Profiles[0]
    
    Profiles[0].Ve = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Ve 
    Profiles[0].I_int = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].I_int
    Profiles[0].tintH_set = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].tintH_set
    Profiles[0].tintC_set = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].tintC_set
    for num in range(1,profiles_num):
        Profiles[0].Ve = Profiles[0].Ve + AllProperties.loc[i,Profiles_names[num]]*Profiles[num].Ve
        Profiles[0].I_int = Profiles[0].I_int + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].I_int
        Profiles[0].tintH_set = Profiles[0].tintH_set + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].tintH_set
        Profiles[0].tintC_set = Profiles[0].tintC_set + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].tintC_set
    return Profiles[0]

# <markdowncell>

# 2.3 Sub-Function calculation of thermal losses of emission systems differet to air conditioning

# <codecell>

def calc_Qem_ls(SystemH,SystemC):
    tHC_corr = [0,0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 'Wall heating' or 'Ceiling heating' or 'Radiatior':
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 'Floor heating': 
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 'Air conditioning': # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 #regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2
    
    if SystemC == 'Ceiling cooling':
        tHC_corr[1] = 0 -1.8
    elif SystemC == 'Floor cooling': 
        tHC_corr[1] = -0.4-1.8
    elif SystemC == 'Air conditioning': # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 #regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + -1.8
        
    return tHC_corr

