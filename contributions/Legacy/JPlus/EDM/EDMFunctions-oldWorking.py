# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ####MODULES

# <codecell>

from __future__ import division
import arcpy
from arcpy import sa
import sys,os
import pandas as pd
import datetime
import jdcal
import numpy as np
import math
import sympy as sp
import scipy
import scipy.optimize
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <markdowncell>

# ##RADIATION MODEL

# <markdowncell>

# ###1. Calculation of hourly radiation in a day

# <codecell>

def CalcRadiation(day, CQ_name, DEMfinal, Observers, T_G_day, latitude, locationtemp1):
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

    return arcpy.GetMessages()

# <markdowncell>

# 1.1 Sub-function to calculate radiation non-sunshinehours

# <codecell>

def calc_radiationday(day, CQ_name, T_G_day, locationtemp1):
    radiation_sunnyhours = dbf2df(locationtemp1+'\\'+CQ_name+'\\'+'radiation'+'\\'+'Day_'+str(day)+'.dbf')
    #Obtain the number of points modeled to do the iterations
    radiation_sunnyhours['ID'] = 0
    counter = radiation_sunnyhours.ID.count()
    value = counter+1
    radiation_sunnyhours['ID'] = range(1, value)
    
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
    Sunrise_time = T_G_day.loc[day-1,'sunrise']
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
    return Table.copy()

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
    Results.FactorShade_y.fillna(Results['FactorShade_x'],inplace=True)
    Results.Freeheight_y.fillna(Results['Freeheight_x'],inplace=True)
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
    Observers0 = locationtemporal2+'\\'+'observers0'  
    NonoverlappingBuildings = locationtemporal2+'\\'+'Non_overlap'
    templines = locationtemporal2+'\\'+'templines'
    templines2 = locationtemporal2+'\\'+'templines2'
    Buffer_CQ0 = locationtemporal2+'\\'+'Buffer_CQ0'
    Buffer_CQ = locationtemporal2+'\\'+'Buffer_CQ'
    Buffer_CQ1 = locationtemporal2+'\\'+'Buffer_CQ1'
    Simple_CQcopy = locationtemporal2+'\\'+'Simple_CQcopy'
    #First increase the boundaries in 2m of each surface in the community to 
    #analyze- this will avoid that the observers overlap the buildings and Simplify 
    #the community vertices to only create 1 point per surface
    
    arcpy.CopyFeatures_management(Simple_CQ,Simple_CQcopy)
    #Make Square-like buffers
    arcpy.PolygonToLine_management(Simple_CQcopy,templines,"IGNORE_NEIGHBORS")
    arcpy.SplitLine_management(templines,templines2)
    arcpy.Buffer_analysis(templines2,Buffer_CQ0,"0.75 Meters","FULL","FLAT","NONE","#")
    arcpy.Append_management(Simple_CQcopy,Buffer_CQ0,"NO_TEST")
    arcpy.Dissolve_management(Buffer_CQ0,Buffer_CQ1,"Name","#","SINGLE_PART","DISSOLVE_LINES")
    arcpy.SimplifyBuilding_cartography(Buffer_CQ1,Buffer_CQ,simplification_tolerance=8, minimum_area=None)

   #arcpy.Buffer_analysis(Simple_CQ,Buffer_CQ,buffer_distance_or_field=1, line_end_type='FLAT') # buffer with a flat finishing
   #arcpy.Generalize_edit(Buffer_CQ,"2 METERS")
    
    #Transform all polygons of the simplified areas to observation points
    arcpy.SplitLine_management(Buffer_CQ,temporal_lines)
    arcpy.FeatureVerticesToPoints_management(temporal_lines,Points,'MID') # Second the transformation of Lines to a mid point
    
    #Join all the polygons to get extra vertices, make lines and then get points. 
    #these points should be added to the original observation points
    arcpy.AggregatePolygons_cartography(Buffer_CQ,AggregatedBuffer,"0.5 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL") # agregate polygons
    arcpy.SplitLine_management(AggregatedBuffer,temporal_lines3) #make lines
    arcpy.FeatureVerticesToPoints_management(temporal_lines3,Points3,'MID')# create extra points
    
    # add information to Points3 about their buildings
    arcpy.SpatialJoin_analysis(Points3,Buffer_CQ,Points3Updated,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST",search_radius="5 METERS")
    arcpy.Erase_analysis(Points3Updated,Points,EraseObservers,"2 Meters")# erase overlaping points
    arcpy.Merge_management([Points,EraseObservers],Observers0)# erase overlaping points
    
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
        
    arcpy.ErasePoint_edit(Observers0,NonoverlappingBuildings,"INSIDE")
    arcpy.CopyFeatures_management(Observers0,Observers)#copy features to reset the OBJECTID
    return arcpy.GetMessages()

# <markdowncell>

# ###5. Radiation results to surfaces

# <codecell>

def CalcRadiationSurfaces(Observers, Radiationyearfinal, DataFactorsCentroids, DataradiationLocation,  locationtemp1, locationtemp2):
    # local variables
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    Outjoin = locationtemp2+'\\'+'Join'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    OutTable = 'CentroidsIDobserv.dbf'
    # Create Join of features Observers and CQ_sementscentroids to 
    # assign Names and IDS of observers (field TARGET_FID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid,Observers,Outjoin,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST",search_radius="10 METERS")
    arcpy.JoinField_management(Outjoin,'OBJECTID',CQSegments, 'OBJECTID') # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, locationtemp1, OutTable)
    
    Centroids_ID_observers = dbf2df(locationtemp1+'\\'+OutTable, cols={'Name_12','height','ORIG_FID','Shape_Leng'})
    Centroids_ID_observers.rename(columns={'Name_12':'Name'},inplace=True)
    
    #Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(DataFactorsCentroids)
    DataCentroidsFull = pd.merge(Centroids_ID_observers,Datacentroids,left_index=True,right_index=True)
    
    #Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    Radiationtable = pd.read_csv(DataradiationLocation,index_col='Unnamed: 0')
    DataRadiation = pd.merge(DataCentroidsFull,Radiationtable, left_on='ORIG_FID_x',right_on='ID')
    
    DataRadiation.to_csv(Radiationyearfinal,index=False)
    return arcpy.GetMessages()

# <markdowncell>

# ##DETERMINISTIC ENERGY MODEL

# <markdowncell>

# ###1. Thermal properties and geom of buildings

# <codecell>

def CalcProperties(CQ, CQproperties, RadiationFile,locationtemp1):
    #Local Variables
    OutTable = 'CQshape3.dbf'
    
    # Set of estimated constants
    Z = 3 # height of basement for every building in m
    Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1
    
    # Set of constants according to EN 13790
    his = 3.45 #heat transfer coefficient between air and the surfacein W/(m2K)
    hms = 9.1 # Heat transfer coeddicient between nodes m and s in W/m2K 
    # Set of estimated constants

    #Import RadiationFile and Properties of the shapefiles
    rf = pd.read_csv(RadiationFile)
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    CQShape_properties = dbf2df(locationtemp1+'\\'+OutTable)
    
    #Areas above ground #get the area of each wall in the buildings
    rf['Awall'] = rf['Shape_Leng']*rf['Freeheight']*rf['FactorShade'] 
    Awalls0 = pd.pivot_table(rf,rows='Name',values='Awall',aggfunc=np.sum); Awalls = pd.DataFrame(Awalls0) #get the area of walls in the whole buildings
    
    Areas = pd.merge(Awalls,CQproperties, left_index=True,right_on='Name')
    Areas['Aw'] = Areas['Awall']*Areas['fwindow']*Areas['PFloor'] # Finally get the Area of windows 
    Areas['Aop_sup'] = Areas['Awall']*Areas['PFloor'] #....and Opaque areas PFloor represents a factor according to the amount of floors heated
    
    #Areas bellow ground
    AllProperties = pd.merge(Areas,CQShape_properties,on='Name')# Join both properties files (Shape and areas)
    AllProperties['Aop_bel'] = Z*AllProperties['Shape_Leng']+AllProperties['Shape_Area']   # Opague areas in m2 below ground including floor
    AllProperties['Atot'] = AllProperties['Aop_sup']+AllProperties['Aop_bel']+AllProperties['Shape_Area'] # Total area of the building envelope m2, it is considered the roof to be flat
    AllProperties['Af'] = AllProperties['Shape_Area']*AllProperties['Floors_y']*AllProperties['Hs_y']# conditioned area
    AllProperties['Aef'] = AllProperties['Shape_Area']*AllProperties['Floors_y']*AllProperties['Es']# conditioned area only those for electricity
    AllProperties['Am'] = AllProperties.Construction.apply(lambda x:AmFunction(x))*AllProperties['Af'] # Effective mass area in m2

    #Steady-state Thermal transmittance coefficients and Internal heat Capacity
    AllProperties ['Htr_w'] = AllProperties['Aw']*AllProperties['Uwindow']  # Thermal transmission coefficient for windows and glazing. in W/K
    AllProperties ['HD'] = AllProperties['Aop_sup']*AllProperties['Uwall']+AllProperties['Shape_Area']*AllProperties['Uroof']  # Direct Thermal transmission coefficient to the external environment in W/K
    AllProperties ['Hg'] = Bf*AllProperties ['Aop_bel']*AllProperties['Ubasement'] # stady-state Thermal transmission coeffcient to the ground. in W/K
    AllProperties ['Htr_op'] = AllProperties ['Hg']+ AllProperties ['HD']
    AllProperties ['Htr_ms'] = hms*AllProperties ['Am'] # Coupling conduntance 1 in W/K
    AllProperties ['Htr_em'] = 1/(1/AllProperties['Htr_op']-1/ AllProperties['Htr_ms']) # Coupling conduntance 2 in W/K 
    AllProperties ['Htr_is'] = his*AllProperties ['Atot']
    AllProperties['Cm'] = AllProperties.Construction.apply(lambda x:CmFunction(x))*AllProperties['Af'] # Internal heat capacity in J/K
    
    # Year Category of building
    AllProperties['YearCat'] = AllProperties.apply(lambda x: YearCategoryFunction(x['Year_y'], x['Renovated']), axis=1)
    
    AllProperties.rename(columns={'Hs_y':'Hs','Floors_y':'Floors','PFloor_y':'PFloor','Year_y':'Year','fwindow_y':'fwindow'},inplace=True)
    return AllProperties

# <codecell>

def CalcIncidentRadiation(AllProperties, Radiationyearfinal):

    #Import Radiation table and compute the Irradiation in W in every building's surface
    Radiation_Shading2 = pd.read_csv(Radiationyearfinal)
    Columns = 8761
    Radiation_Shading2['AreaExposed'] = Radiation_Shading2['Shape_Leng']*Radiation_Shading2['FactorShade']*Radiation_Shading2['Freeheight']
    for Column in range(1, Columns):
         #transform all the points of solar radiation into Wh
        Radiation_Shading2['T'+str(Column)] = Radiation_Shading2['T'+str(Column)]*Radiation_Shading2['AreaExposed']
        
    #Do pivot table to sum up the irradiation in every surface to the building 
    #and merge the result with the table allProperties
    PivotTable3 = pd.pivot_table(Radiation_Shading2,rows='Name',margins='Add all row')
    RadiationLoad = pd.DataFrame(PivotTable3)
    Solar = AllProperties.merge(RadiationLoad, left_on='Name',right_index=True)
    
    return Solar # total solar radiation in areas exposed to radiation in Watts

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

# ###2. Calculation of thermal and Electrical loads - No processes

# <codecell>

def CalcThermalLoads(i, AllProperties, locationFinal, Solar, Profiles,Profiles_names, Temp, Seasonhours, Servers,Coolingroom): 
    # Mode is a variable 0 without losses, 1 With losses of distribution enmission and control
    #Local Variables
    Name = AllProperties.loc[i,'Name']
    
    # Set of constants according to EN 13790
    g_gl = 0.9*0.75 # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows to be double glazing (0.75)
    pa_ca = 1200  # Air constant J/m3K   
    F_f = 0.3 # Frame area faction coefficient
    Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1
    tw = 10 # the temperature of intake of water for hot water
    
    # Set of variables used offently
    nf = AllProperties.loc[i,'Floors']
    nfpercent = AllProperties.loc[i,'PFloor']
    height = AllProperties.loc[i,'height']
    Lw = AllProperties.loc[i,'MBG_Width']
    Ll = AllProperties.loc[i,'MBG_Length']
    Awall = AllProperties.loc[i,'Awall']
    footprint = AllProperties.loc[i,'Shape_Area']
    Year = AllProperties.loc[i,'Year']
    Yearcat = AllProperties.loc[i,'YearCat']
    Af = AllProperties.loc[i,'Af']
    Aef = AllProperties.loc[i,'Aef']
    SystemH = AllProperties.loc[i,'Emission_heating']
    SystemC = AllProperties.loc[i,'Emission_cooling']
    tsh0 = AllProperties.loc[i,'tsh0']
    trh0 = AllProperties.loc[i,'trh0']
    tsc0 = AllProperties.loc[i,'tsc0']
    trc0 = AllProperties.loc[i,'trc0']
    te_min = Temp.te.min()
    te_max = Temp.te.max()
    
    # Determination of Profile of occupancy to use
    Occupancy0 = calc_Type(Profiles,Profiles_names, AllProperties, i, Servers,Coolingroom)
              
    #Create Labels in data frame to iterate
    Columns = ['IH_nd_ac','IC_nd_ac','g_gl','Htr_1','Htr_2','Htr_3','tm_t','tair_ac','top_ac','IHC_nd_ac', 'Asol', 'I_sol','te',
                    'Eal','Qhsf','Qcsf','Qhs','Qcs','Qwwf','Qww','tair','top','tsc','trc','tsh','trh','Qhs_em_ls','Qcs_em_ls',
                    'Qhs_d_ls','Qcs_d_ls','Qww_dh_ls','Qww_d_ls','tamb','Qcs_dis_em_ls','Qhs_dis_em_ls',
                    'Eaux_hs', 'Eaux_cs', 'Eaux_ww']
    for Label in Columns:
        Occupancy0 [Label] = 0
    
    if Af >0:
        #Assign temperature data to the table
        Occupancy0['te'] = Temp['te']
            
        # Determination of Hourly Thermal transmission coefficient due to Ventilation in W/K
        Occupancy0['Hve'] =  pa_ca*(Occupancy0['Ve']*Af/3600)
        
        #Calculation of hot water use At 60 degrees and 45 degress for  new buildings
        if AllProperties.loc[i,'Year'] >= 2020:
            twws = 45
        else:
            twws = 60
        Occupancy0['Qww'] = Occupancy0['Mww']*Af*4.184*(twws-tw)*0.277777777777778 # in wattshour.
        
        #Calculation of lossess distribution system for domestic hot water
        Occupancy = calc_Qww_dis_ls(nf, nfpercent, Lw, Ll, Year,Af,twws, Bf, AllProperties.loc[i,'Renovated'],
                    Occupancy0, Seasonhours,footprint,1) #1 when internal loads ar calculated
        
        #addd losses of hotwater system into internal loads for the mass balance
        Occupancy['I_int'] = Occupancy['I_int']*Af+Occupancy['Qww_dh_ls']*0.8# 80% is recoverable or enter to play in the energy balance
        
        #Determination of Heat Flows for internal loads in W
        Occupancy['I_ia'] = 0.5*Occupancy['I_int']
        
        # Calculation Shading factor per hour due to operation of external shadings, 1 when I > 300 W/m2
        Rf_sh = Calc_Rf_sh(AllProperties.loc[i,'Shading_Po'],AllProperties.loc[i,'Shading_Ty'])
        # Calculation of effecive solar area of surfaces in m2, opaque areas are not considered, reduction factor of overhangs is not included. Fov =0
    
        Num_Hours = 8760
        for hour in range(Num_Hours):
    
            Occupancy.loc[hour,'g_gl'] = calc_gl(Solar.loc[i,'T'+str(hour+1)]/AllProperties.loc[i,'Awall'], g_gl,Rf_sh)
    
            # Calculation of solar efective area per hour in m2  
            Occupancy.loc[hour,'Asol'] = Occupancy.loc[hour,'g_gl']*(1-F_f)*AllProperties.loc[i,'Aw']
        
            # Calculation of Solar gains in each facade in W it is neglected the extraflow of radiation from the surface to the exterior Fr_k*Ir_k = 0 as well as gains in opaque surfaces
            Occupancy.loc[hour,'I_sol'] = Occupancy.loc[hour,'Asol']*(Solar.loc[i,'T'+str(hour+1)]/AllProperties.loc[i,'Awall'])#-Fr*AllProperties.loc[i,'Aw_N']*AllProperties.loc[i,'Uwindow']*delta_t_er*hr*Rse
            
            # Determination of Hourly thermal transmission coefficients for Determination of operation air temperatures in W/K
            Coefficients = calc_Htr(Occupancy.loc[hour,'Hve'], AllProperties.loc[i,'Htr_is'], AllProperties.loc[i,'Htr_ms'], AllProperties.loc[i,'Htr_w'])
            Occupancy.loc[hour,'Htr_1'] = Coefficients[0]
            Occupancy.loc[hour,'Htr_2'] = Coefficients[1]
            Occupancy.loc[hour,'Htr_3'] = Coefficients[2]
      
        # Determination of Heat Flows for internal heat sources
        Occupancy['I_m'] = (AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])*(Occupancy['I_ia']+Occupancy['I_sol'])
        Occupancy['I_st'] = (1-(AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])-(AllProperties.loc[i,'Htr_w']/(9.1*AllProperties.loc[i,'Atot'])))*(Occupancy['I_ia']+Occupancy['I_sol'])
        
        # Seed for calculation

        # factors of Losses due to emission of systems vector hot or cold water for heating and cooling
        tHC_corr = [0,0]
        tHC_corr = calc_Qem_ls(SystemH,SystemC)
        tHset_corr = tHC_corr[0]
        tCset_corr = tHC_corr[1]
        
        Occupancy.loc[0,'tm_t'] = Occupancy.loc[0,'te']       
        for j in range(1,Num_Hours):    
            # Determination of net thermal loads and temperatures including emission losses
            Losses = 0
            tm_t0 = Occupancy.loc[j-1,'tm_t']
            te_t = Occupancy.loc[j,'te']
            tintH_set = Occupancy.loc[j,'tintH_set']
            tintC_set = Occupancy.loc[j,'tintC_set']
            Htr_em = AllProperties.loc[i,'Htr_em']
            Htr_ms = AllProperties.loc[i,'Htr_ms']
            Htr_is = AllProperties.loc[i,'Htr_is']
            Htr_1 = Occupancy.loc[j,'Htr_1']
            Htr_2 = Occupancy.loc[j,'Htr_2']
            Htr_3 = Occupancy.loc[j,'Htr_3']
            Hve = Occupancy.loc[j,'Hve']
            Htr_w = AllProperties.loc[i,'Htr_w']
            I_st = Occupancy.loc[j,'I_st']
            I_ia = Occupancy.loc[j,'I_ia']
            I_m = Occupancy.loc[j,'I_m']
            Cm = AllProperties.loc[i,'Cm']
            
            Results0 = calc_TL(SystemH,SystemC, te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1,
                               Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,
                               tCset_corr)
            Occupancy.loc[j,'tm_t'] = Results0[0]
            Occupancy.loc[j,'tair'] = Results0[1] # temperature of inside air
            Occupancy.loc[j,'top'] = Results0[2] # temperature of operation
            Occupancy.loc[j,'Qhs'] = Results0[3] # net heating load
            Occupancy.loc[j,'Qcs'] = Results0[4] # net cooling load
            
            Losses = 1
            Results1 = calc_TL(SystemH,SystemC, te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1,
                               Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr)
            Occupancy.loc[j,'Qhs_em_ls'] = Results1[3]- Occupancy.loc[j,'Qhs'] # losses emission and control
            Occupancy.loc[j,'Qcs_em_ls'] = Results1[4]- Occupancy.loc[j,'Qcs'] #losses emission and control
    
        # sum of final energy up to the generation first time
        Occupancy['Qhsf'] = Occupancy['Qhs']
        Occupancy['Qcsf'] = -Occupancy['Qcs']
        Occupancy['Qwwf'] = Occupancy['Qww'] 
        
       # for j in range(Num_Hours):
         #   if Seasonhours[0] < j < Seasonhours[1]:
         #       Occupancy.loc[j,'Qhs'] = 0
        #        Occupancy.loc[j,'Qhsf'] = 0
        #    elif 0 <= j <= Seasonhours[0] or Seasonhours[1] <= j <= 8759:
         #       Occupancy.loc[j,'Qcs'] = 0
          #      Occupancy.loc[j,'Qcsf'] = 0
        
        #Occupancy.to_csv(r'C:\ArcGIS\Toerase0.csv')
        
        #Qc MUST BE POSITIVE
        #Calculation temperatures of the distribution system during time
        Results2 = calc_temperatures(SystemH,SystemC,Occupancy,Temp,tsh0,trh0,tsc0,trc0,nf,Af,Seasonhours)
        Occupancy2 = Results2[0]
    
        #Calculation of lossess distribution system for space heating space cooling 
        Occupancy3 = calc_Qdis_ls(SystemH,SystemC, nf,nfpercent,Lw,Ll,Year,Af,twws, Bf, AllProperties.loc[i,'Renovated'],
                    Occupancy2, Seasonhours,footprint)

        #Calculation of lossess distribution system for domestic hot water 
        Occupancy4 = calc_Qww_dis_ls(nf, nfpercent, Lw, Ll, Year,Af,twws, Bf, AllProperties.loc[i,'Renovated'],
                    Occupancy3, Seasonhours,footprint,0)# 0 when real loads are calculated
        
        #Occupancy4.to_csv(r'C:\ArcGIS\Toerase.csv')
    
        Occupancy4['Qww_dis_ls'] = Occupancy4['Qww_d_ls']+ Occupancy4['Qww_dh_ls']
        Occupancy4['Qcs_dis_em_ls'] = -(Occupancy4['Qcs_em_ls']+ Occupancy4['Qcs_d_ls'])
        Occupancy4['Qhs_dis_em_ls'] = Occupancy4['Qhs_em_ls']+ Occupancy4['Qhs_d_ls']    
        # sum of final energy up to the generation
        Occupancy4['Qhsf'] = Occupancy4['Qhs']+Occupancy4['Qhs_dis_em_ls']#it is already taking into account contributon of heating system.
        Occupancy4['Qcsf'] = -Occupancy4['Qcs']+Occupancy4['Qcs_dis_em_ls']
        Occupancy4['Qwwf'] = Occupancy4['Qww'] + Occupancy4['Qww_dis_ls']
        
        #Occupancy4.to_csv(r'C:\ArcGIS\Toerase2.csv')
        # ERASE VALUES OUT OF SEASON (WHEN THE COOLING OR HEATING SYSTEMS ARE OFF)
        Occupancy4.Qhs[Seasonhours[0]+1:Seasonhours[1]] = 0
        Occupancy4.Qhsf[Seasonhours[0]+1:Seasonhours[1]] = 0
        Occupancy4.Qhs_em_ls[Seasonhours[0]+1:Seasonhours[1]] = 0
        Occupancy4.Qhs_d_ls[Seasonhours[0]+1:Seasonhours[1]] = 0
        Occupancy4.tsh[Seasonhours[0]+1:Seasonhours[1]] = 0
        Occupancy4.trh[Seasonhours[0]+1:Seasonhours[1]] = 0
        
        Occupancy4.Qcs[:Seasonhours[0]+1] = Occupancy4.Qcs[Seasonhours[1]:] = 0
        Occupancy4.Qcs_em_ls[:Seasonhours[0]+1] = Occupancy4.Qcs_em_ls[Seasonhours[1]:] = 0
        Occupancy4.Qcs_d_ls[:Seasonhours[0]+1] = Occupancy4.Qcs_d_ls[Seasonhours[1]:] = 0
        Occupancy4.Qcsf[:Seasonhours[0]+1] = Occupancy4.Qcsf[Seasonhours[1]:] = 0
        Occupancy4.trc[:Seasonhours[0]+1] = Occupancy4.trc[Seasonhours[1]:] = 0
        Occupancy4.tsc[:Seasonhours[0]+1] = Occupancy4.tsc[Seasonhours[1]:] = 0     
        
        #Calculation temperatures of the distribution system during time second time
        Results3 = calc_temperatures(SystemH,SystemC,Occupancy4,Temp,tsh0,trh0,tsc0,trc0,nf,Af,Seasonhours)
        Occupancy5 = Results3[0]
        Qhs0 = Results3[1]/1000 # in kWh
        Qcs0 = Results3[2]/1000 # in kWh
        mwh0 = Results3[3] # in kg.h
        mwc0 = Results3[4] # in kg.h
        tsh0 = Results3[5] # in C
        trh0 = Results3[6] # in C
        tsc0 = Results3[7] # in C
        trc0 = Results3[8] # in C
        
        #Occupancy5.to_csv(r'C:\ArcGIS\Toerase3.csv')
        
        #calculation of energy for pumping of all the systems (no air-conditioning
        Occupancy6 =  calc_Aux_hscs(nf,nfpercent,Lw,Ll,footprint,Year,Qhs0,tsh0,trh0,Occupancy5,Qcs0,tsc0,trc0,
                                    SystemH,SystemC,twws,tw)
    
        #Calculation of Electrical dem
        if SystemC == 3 or SystemC == 4:
            for j in range(Num_Hours):  #mode = 0  
                if Seasonhours[0] < j < Seasonhours[1]: #cooling season air conditioning 15 may -15sept
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_ve'] + Occupancy6.loc[j,'Ealf_nove'])*AllProperties.loc[i,'Aef']
                else:
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_nove'])*Aef
                    
        if SystemH == 3:
            for j in range(Num_Hours):  #mode = 0
                if 0 <= j <= Seasonhours[0]: #heating season air conditioning 15 may -15sept
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_ve'] + Occupancy6.loc[j,'Ealf_nove'])*AllProperties.loc[i,'Aef']
                elif  Seasonhours[1] <= j <= 8759: #cooling season air conditioning 15 may -15sept
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_ve'] + Occupancy6.loc[j,'Ealf_nove'])*AllProperties.loc[i,'Aef']       
                else:
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_nove'])*AllProperties.loc[i,'Aef']
    else:
        Occupancy0['Eal'] = Occupancy0['Ealf_nove']*Aef
        Occupancy6 = Occupancy0
        Qhs0 = Qcs0 = mwh0 = mwc0 = tsh0 = tsc0 = trh0 = trc0 =0
        
    if SystemC ==0:
        Occupancy6['Qcsf'] = Occupancy6['trc'] = Occupancy6['tsc'] = 0
        
    Occupancy6['Eaux'] = Occupancy6['Eaux_hs'] + Occupancy6['Eaux_cs'] + Occupancy6['Eaux_ww']
    Occupancy6['Ealf'] = Occupancy6['Eal'] + Occupancy6['Eaux']
    Occupancy6['NAME'] = AllProperties.loc[i,'Name']
    
    # Calculate Occupancy
    Occupancy6['Occupancy'] = Occupancy6['People']*Af
    MaxOccupancy = Occupancy6['Occupancy'].max()
    
    #calculate amount of water used
    Occupancy6['Water']= (Occupancy6['Mww']+ Occupancy6['Mw'])*Af # in l  
    Water = Occupancy6['Water'].sum()/1000 # total of waterin m3
    
    # Results
    Result_TL = pd.DataFrame(Occupancy6,columns = ['DATE','NAME','Qhs_dis_em_ls','Qcs_dis_em_ls','Qww_dis_ls','Qhs','Qcs','Qww','Qhsf','Qcsf','Qwwf','Ealf','Eaux',
                                                    'I_sol','I_int','tsh','trh','tsc','trc','tair','top','te','Occupancy','Water'])
    Totals_TL = pd.DataFrame(Result_TL.sum()).T/1000000 #in MWh
    GT = {'Name':[AllProperties.loc[i,'Name']],'Qhs_dis_em_ls':Totals_TL.Qhs_dis_em_ls,'Qhsf':Totals_TL.Qhsf,'Qcs_dis_em_ls':Totals_TL.Qcs_dis_em_ls,'Qcsf':Totals_TL.Qcsf,
                  'Qhs':Totals_TL.Qhs,'Qcs':Totals_TL.Qcs,'Qww':Totals_TL.Qww,'Qww_dis_ls':Totals_TL.Qww_dis_ls,'Qwwf':Totals_TL.Qwwf,
                   'Water':Water,'Ealf':Totals_TL.Ealf,'Eaux':Totals_TL.Eaux,'MaxOccupancy':MaxOccupancy,'tsh0':tsh0,'trh0':trh0,'tsc0':tsc0,'trc0':trc0,'Qhs0':Qhs0,'Qcs0':Qcs0,'mwh0':mwh0,'mwc0':mwc0,'Af':Af}
    Grandtotal = pd.DataFrame(GT)
    # EXPORT RESULTS
    Result_TL.to_csv(locationFinal+'\\'+Name+'.csv',index=False)
    Grandtotal.to_csv(locationFinal+'\\'+Name+'T'+'.csv')
    return 

# <markdowncell>

# Calc temperatures distribution system

# <codecell>

def calc_temperatures(SystemH,SystemC,DATA,Temp,tsh0,trh0,tsc0,trc0,Af,Floors,Seasonhours):
    # FOR HEATING SYSTEMS FOLLOW THIS
    if SystemH == 0:
        Qhsmax = 0
        mwh0 =0  
        
    if SystemC == 0:
        Qcsmax = 0
        mwc0 =0
        
    if SystemH == 3 and SystemC == 3:
        Qc0 = Qcsmax = DATA['Qcsf'].max()
        tairc0 = DATA['tintC_set'].min()
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tairh0 = DATA['tintH_set'].max()
        HVAC = calc_HVAC(SystemH,SystemC,DATA,Temp,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        RESULT = HVAC[0]
        mwh0 = HVAC[1]/4.190*3.6 # in kg/h
        mwc0 = HVAC[2]/4.190*3.6 # in kg/h
        
    if SystemH == 3 and SystemC != 3:
        Qc0 = Qcsmax = DATA['Qcsf'].max()
        tairc0 = DATA['tintC_set'].min()
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tairh0 = DATA['tintH_set'].max()
        HVAC = calc_HVAC(SystemH,SystemC,DATA,Temp,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        RESULT = HVAC[0]
        mwh0 = HVAC[1]/4.190*3.6 # in kg/h
        mwc0 = HVAC[2]/4.190*3.6 # in kg/h
    
    if SystemC == 3 and SystemH != 3:
        Qc0 = Qcsmax = DATA['Qcsf'].max()
        tairc0 = DATA['tintC_set'].min()
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tairh0 = DATA['tintH_set'].max()
        HVAC = calc_HVAC(SystemH,SystemC,DATA,Temp,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        RESULT = HVAC[0]
        mwh0 = HVAC[1]/4.190*3.6 # in kg/h
        mwc0 = HVAC[2]/4.190*3.6 # in kg/h
        
    if SystemH == 1:
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tair0 = DATA['tintH_set'].max()
        rad = calc_RAD(DATA,tsh0,trh0,Qh0,tair0)
        RESULT = rad[0]
        mwh0 = rad[1]/4.190*3.6 # in kg/h
    
    if SystemH == 2:
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tair0 = DATA['tintH_set'].max()
        fh = calc_TABSH(DATA,Qh0,tair0,Af,Floors)
        RESULT = fh[0]
        mwh0 = fh[1]/4.190*3.6 # in kg/h
        tsh0 = fh[2] # these values are designed for the conditions of the building
        trh0 = fh[3] # these values are designed for the conditions of the building
    
    if SystemC == 4: # it is considered it has a ventilation system to regulate moisture.
        Qc0 = Qcsmax = DATA['Qcsf'].max()
        tair0 = DATA['tintC_set'].min()
        fc = calc_TABSC(DATA, Qc0,tair0,Af)
        RESULT = fc[0]
        mwc0 = fc[1]/4.190*3.6 # in kg/h
        tsc0 = fc[2]
        trc0 = fc[3] 
        
    return RESULT.copy(),Qhsmax,Qcsmax, mwh0, mwc0, tsh0, trh0, tsc0, trc0

# <markdowncell>

# 2.1 Sub-function temperature radiator systems

# <codecell>

def calc_RAD(DATA,tsh0,trh0,Qh0,tair0):
    nh =0.33
    tair0 = tair0 + 273
    tsh0 = tsh0 + 273
    trh0 = trh0 + 273
    mCw0 = Qh0/(tsh0-trh0) 
    LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
    k1 = 1/mCw0
    def fh(x): 
        Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
        return Eq
    rows = DATA.Qhsf.count()
    for row in range(rows):
        if DATA.loc[row,'Qhsf'] != 0 and (DATA.loc[row,'tair'] == (tair0-273) or DATA.loc[row,'tair'] == 16): # in case hotel or residential 
            k2 = DATA.loc[row,'Qhsf']*k1
            tair = DATA.loc[row,'tair']+ 273
            result = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
            DATA.loc[row,'trh'] = result.real
            DATA.loc[row,'tsh'] = DATA.loc[row,'trh'] + k2
    return DATA.copy(), mCw0

# <markdowncell>

# 2.1 Sub-function temperature Floor activated slabs

# <codecell>

def calc_TABSH(DATA, Qh0,tair0,Af,Floors):
    tair0 = tair0 + 273
    tmean_max = tair0 + 10           # according ot EN 1264, simplifying to +9 k inernal surfaces and 15 perimeter and batroom    
    n = 0.025
    q0 = Qh0/Af                                            
    S0 = 5                                             #drop of temperature of supplied water at nominal conditions
    U0 = q0/(tmean_max-tair0)
    deltaH0 = (Qh0/(U0*Af))
    
    if S0/deltaH0 <= 0.5: #temperature drop of water should be in this range
        deltaV0 = deltaH0 + S0/2 
    else:
        deltaV0 = deltaH0 + S0/2+(S0**2/(12*deltaH0))
    
    tsh0 = deltaV0 + tair0
    trh0 = tsh0 - S0
    tsh0 = tsh0 + 273
    trh0 = trh0 + 273
    mCw0 = q0*Af/(tsh0-trh0)
    LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
    qh0 = 8.92*(tmean_max-tair0)**1.1
    kH0 = qh0*Af/(LMRT**(1+n))
    k1 = 1/mCw0
    def fh(x): 
        Eq = mCw0*k2-kH0*(k2/(scipy.log((x+k2-tair)/(x-tair))))**(1+n)
        return Eq
    rows = DATA.Qhsf.count()
    DATA['surface']=0
    for row in range(rows):
        if DATA.loc[row,'Qhsf'] != 0 and (DATA.loc[row,'tair'] == (tair0-273) or DATA.loc[row,'tair'] == 16):
            Q = DATA.loc[row,'Qhsf']
            q =Q/Af
            k2 = Q*k1
            tair = DATA.loc[row,'tair'] + 273
            result = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
            DATA.loc[row,'trh'] = result.real
            DATA.loc[row,'tsh'] = DATA.loc[row,'trh'] + k2
            DATA.loc[row,'surface'] = (q/U0)**(1/1.1)+ DATA.loc[row,'tair']
            
    #FLOW CONSIDERING LOSSES Floor slab prototype
    # no significative losses are considered
    # !!!!!!!!!this text is just in case if in the future it will be used!!!!!
    #sins = 0.07
    #Ru = sins/0.15+0.17+0.1
    #R0 = 0.1+0.0093+0.045/1 # su = 0.045 it is the tickness of the slab    
    # CONSTANT FLOW CONDITIONS
    #tu = 13 # temperature in the basement
    #if Floors ==1:
    #    mCw0 = Af*q0/(S0)*(1+R0/Ru+(tair-tu)/(q0*Ru))
    #else:
    #     Af1 = Af/Floors
    #     mCw0 = Af1*q0/(S0)*(1+R0/Ru+(tair-tu)/(Qh0*Ru/Af1))+((Af-Af1)*q0/(S0*4190)*(1+R0/Ru))   
        
    tsh0 = DATA.loc[row,'tsh'].max()
    trh0 = DATA.loc[row,'trh'].max()
        
    return  DATA.copy(), mCw0, tsh0, trh0

# <markdowncell>

# 2.1 Subfunction temperature and flow TABS Cooling

# <codecell>

def calc_TABSC(DATA,Qc0,tair0, Af):
    tair0 = tair0 + 273
    qc0 = Qc0/(Af*0.5)    # 50% of the area available for heat exchange = to size of panels
    tmean_min = dewP = 18
    deltaC_N = 8          # estimated difference of temperature room and panel at nominal conditions
    Sc0 = 2.5             # rise of temperature of supplied water at nominal conditions
    delta_in_des = deltaC_N + Sc0/2
    U0 = qc0/deltaC_N
    
    tsc0 = tair0 - 273 - delta_in_des
    if tsc0 <= dewP:
        tsc0 = dewP - 1
    trc0 = tsc0  + Sc0
    
    tsc0 = tsc0 + 273
    trc0 = trc0 + 273    
    tmean_min = (tsc0+trc0)/2 # for design conditions difference room and cooling medium    
    mCw0 = Qc0/(trc0-tsc0)
    LMRT = (trc0-tsc0)/scipy.log((tsc0-tair0)/(trc0-tair0))
    kC0 = Qc0/(LMRT)
    k1 = 1/mCw0
    def fc(x): 
        Eq = mCw0*k2-kC0*(k2/(scipy.log((x-k2-tair)/(x-tair))))
        return Eq
    rows = DATA.Qcsf.count()
    DATA['surfaceC']=0
    for row in range(rows):
        if DATA.loc[row,'Qcsf'] != 0 and (DATA.loc[row,'tair'] == (tair0-273) or DATA.loc[row,'tair'] == 30):# in a hotel
            Q = DATA.loc[row,'Qcsf']
            q = Q/(Af*0.5)
            k2 = Q*k1
            tair = DATA.loc[row,'tair'] + 273
            DATA.loc[row,'trc'] = scipy.optimize.newton(fc, trc0, maxiter=100,tol=0.01) - 273 
            DATA.loc[row,'tsc'] = DATA.loc[row,'trc'] - k2
            DATA.loc[row,'surfaceC'] = DATA.loc[row,'tair'] - (q/U0)
            
    #FLOW CONSIDERING LOSSES Floor slab prototype
    # no significative losses are considered
    tsc0 = (tsc0-273)
    trc0 = (trc0-273)    
    
    return  DATA.copy(), mCw0, tsc0, trc0

# <markdowncell>

# 2.1 Sub-function temperature Air conditioning

# <codecell>

def calc_HVAC(SystemH,SystemC,DATA,Temp,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours):
    # Initialize variables
    mCwh0 = mCwc0 = 0
    Temp['mh_air'] = 0
    Temp['mc_air'] = 0
    Temp['tsc_air'] = 0
    Temp['tsh_air'] = 0
    Temp['tsc_air_1'] = 0
    Temp['tsh_air_1'] = 0
    Temp['RH5'] = 0
    DATA['Qlat'] = 0
    Temp['deltaT'] = 0
    Temp['w5'] = 0
    Temp['t5'] = 0
    Temp['w3'] = 0
    Temp['w1'] = 0
    Temp['t3'] = 0   
    DATA['Qlat'] = 0
    DATA['Qhum'] = 0
    DATA['Qdhum'] = 0
    DATA['Qslcf'] = 0
    DATA['Qcsf_coil'] = 0
    DATA['Qhsf_coil'] = 0
    # Assumptions    
    Num_hours = DATA.tair.count()
    nrec_N = 0.75 
    C1 = 0.054 # assumed a flat plate heat exchanger
    Vmax = 3 # maximum estimated flow.
    Pair = 998 #kg/m3
    Seasonhours = [3216,6192]
    lv = 2257 #kJ/kg
    Cpa_w3 = 1.007 #in kJ/kgK
    for j in range(Num_hours):
        if DATA.loc[j,'People'] > 0:  # during operation times only for the first itme step
            # Air temperature one step before including gain from fan as
            # as it is hourly it is assumed that the initial need of power takes just a small
            #amount of time in relation to the performance of the whole hour
            tset = DATA.loc[j,'tair']
            # OUTSIDE AIR
            RH1 = Temp.loc[j,'RH']
            t1 = Temp.loc[j,'te']
            w1 = calc_w(t1,RH1) #kg/kg
            h1 = calc_h(t1,w1)
            # AFTER HEAT RECOVERY
            qv_req = DATA.loc[j,'Ve']*Af/3600 # in m3/s
            qv = qv_req*0.8*1.04*1.02*1.2     # in m3/s corrected taking into acocunt leakage
            Veff = Vmax*qv/qv_req              
            nrec = nrec_N-C1*(Veff-2)   #$ heat exchanger coefficient
            # EXHAUST DUCT 
            t5_1 = tset + tset*0.2 #increase in temperature form the last step in the extracted air
            # initial state
            if RH1 >= 70:
                RH5_1 = 70
            elif 30 < RH1 < 70:
                RH5_1 = RH1
            else:
                RH5_1 = 30
            w5_1 =  calc_w(t5_1,RH5_1)
            t2 = t1 + nrec*(t5_1-t1)
            w2 = w1 + nrec*(w5_1-w1)
            if j-1 >=0:
                if DATA.loc[j-1,'People'] > 0 :
                    t5_1 = DATA.loc[j-1,'tair'] + DATA.loc[j-1,'tair']*0.2
                    RH5_1 = Temp.loc[j-1,'RH5']
                    w5_1 =  calc_w(t5_1,RH5_1)
                    # AFTER AHU
                    t2 = t1 + nrec*(t5_1-t1)
                    w2 = w1 + nrec*(w5_1-w1)
            #production of humidity:
            Qlat = DATA.loc[j,'w_int']*(Af/(1000*3600)*lv)*3.6 #in kJ
            
            # ASSUMPTION  the HVAc does not alter the humidity content at the first step
            if Seasonhours[0] <= j+1 <= Seasonhours[1] and SystemC == 3 and DATA.loc[j,'Qcsf']>0: # this is cooling season
                Qs = DATA.loc[j,'Qcsf']*3.6 #in kJ
                w3 = w2
                t3 = 17      #which is the supply temperature?
                t5 = tset
                h5 = calc_h(t5,w3)
                h3 = calc_h(t3,w3)
                m = max(Qs/(h5-h3),(Pair*qv_req)) #kg/s # from the point of view of internal loads
                #VERIFICATION WITH HUMIDITY
                t5 = Qs/(m*Cpa_w3)+t3
                w5 = (m*w3+Qlat/lv)/m
                if w5 > calc_w(t5,70):
                    #dehumidification
                    w3 = max(min(calc_w(t5,70)-w5+w2,calc_w(t3,100)),0)
                    Qdhum = 0.83*qv_req*3600*(w2-w3)*1000 #in Wh
                elif w5 < calc_w(t5,30):
                    # Humidification
                    w3 = calc_w(t5,30)- w5 + w2
                    Qhum = 0.83*qv_req*3600*(calc_w(t5,30)- w5)*1000 # in Wh
                else:
                    w3 = min(w2,calc_w(t3,100))
                    Qhum = 0
                    Qdhum = 0
                    
                h2 = calc_h(t2,w2)
                t5  = Qs/(m*Cpa_w3)+t3
                w5 = (m*w3+Qlat/lv)/m
                h5 = calc_h(t5,w5)
                h3 = calc_h(t3,w3)
                RH5 = calc_RH(w5,t5)
                m = max(Qs/(h5-h3),(Pair*qv_req))
                Temp.loc[j,'mc_air'] = m
                Temp.loc[j,'tsc_air'] = t3
                Temp.loc[j,'tsc_air_1'] = t2
                Temp.loc[j,'RH5'] = RH5
                Temp.loc[j,'w5'] = w5
                Temp.loc[j,'t5'] = t5
                Temp.loc[j,'w3'] = w3
                Temp.loc[j,'t3'] = t3
                DATA.loc[j,'Qcsf_coil'] = m*abs(h3-h2)/3.6 # in Wh
                
            elif SystemH == 3 and DATA.loc[j,'Qhsf']>0:
                Qs = DATA.loc[j,'Qhsf']*3.6
                w3 = w2
                t3 = tset # taking into account that the fan adds heat
                t5 = tset + tset*0.2
                h5 = calc_h(t5,w3)
                h3 = calc_h(t3,w3)
                m = max(Qs/(h5-h3),(Pair*qv_req)) # from the point of view of internal loads
                #VERIFICATION WITH HUMIDITY
                t5 = Qs/(m*Cpa_w3)+t3
                w5 = (m*w3+Qlat/lv)/m
                if  w5 < calc_w(t5,30):
                    #Humidification
                    w3 = calc_w(t5,30) - w5 + w2
                    Qhum = 0.83*qv_req*3600*(calc_w(t5,30) - w5)*1000 # in Watts
                elif w5 > calc_w(t5_1,70) and w5 < calc_w(26,70): #dew point
                    #heaitng with no dehumidification
                    deltaT = calc_t(w5,70) - t5
                    w3 = w2
                elif w5 > calc_w(26,70):
                    #Dehumidification
                    w3 = max(min(min(calc_w(26,70)-w5+w2,calc_w(t3,100)),calc_w(t5,70)-w5+w2),0)
                    Qdhum = 0.83*qv_req*3600*(w2-w3)*1000 #in Watts
                else:
                    # No mositure control necessary
                    w3=w2
                    Qhum = 0
                    Qdhum = 0
                    deltaT =0
                
                h2 = calc_h(t2,w2)
                h3 = calc_h(t3,w3)
                t5  = Qs/(m*Cpa_w3)+t3
                w5 = (m*w3+Qlat/lv)/m
                h5 = calc_h(t5,w5)
                RH5 = calc_RH(w5,t5)
                m = max(Qs/(h5-h3),(Pair*qv_req))
                Temp.loc[j,'mh_air'] = m
                Temp.loc[j,'tsh_air'] = t3
                Temp.loc[j,'tsh_air_1'] = t2
                Temp.loc[j,'deltaT'] = deltaT
                DATA.loc[j,'Qhsf_coil'] = m*abs(h3-h2)/3.6 # in Wh
                Temp.loc[j,'RH5'] = RH5
                Temp.loc[j,'w5'] = w5
                Temp.loc[j,'t5'] = t5
                Temp.loc[j,'w3'] = w3
                Temp.loc[j,'t3'] = t3 
                Temp.loc[j,'w1'] = w1
            
            else: 
                Qhum = 0
                Qdhum = 0
                deltaT =0
            
            DATA.loc[j,'Qlat'] = Qlat/3.6 #in Wh
            DATA.loc[j,'Qhum'] = Qhum
            DATA.loc[j,'Qdhum'] = Qdhum
    
    #Calculate temperatures of cooling and heating coils            
    if SystemH == 3 and SystemC == 3:
        R = calc_Hcoil(Temp,DATA,Qh0,tsh0,trh0,tairh0)
        Result1 = R[0]
        mCwh0 = R[1]
        R2  = calc_Ccoil(Temp,Result1,Qc0,tsc0,trc0,tairc0)
        RESULT = R2[0]
        mCwc0 = R2[1]
    if SystemH == 3 and SystemC != 3:
        R = calc_Hcoil(Temp,DATA,Qh0,tsh0,trh0,tairh0)
        RESULT = R[0]
        mCwh0 = R[1]
    if SystemC == 3 and SystemH != 3:
        R = calc_Ccoil(Temp,DATA,Qc0,tsc0,trc0,tairc0)
        RESULT = R[0]
        mCwc0 = R[1]
    
    return RESULT.copy(),mCwh0,mCwc0 

# <codecell>

def calc_Hcoil(Temp,DATA,Qh0,tsh0,trh0,tair0):
    tair0 = tair0 + 273
    tsh0 = tsh0 + 273
    trh0 = trh0 + 273
    Qh0 = DATA.Qhsf.max()
    mCw0 = Qh0/(tsh0-trh0)
    Num_hours = DATA.tair.count()
    for j in range(Num_hours):
        if DATA.loc[j,'Qhsf'] == DATA.Qhsf.max():
            ti_1_0 = Temp.loc[j,'tsh_air_1'] +273
            ti_0 = Temp.loc[j,'tsh_air'] + 273
    
    LMRT0 = ((tsh0 - ti_1_0)-(trh0 - ti_0))/scipy.log((tsh0-ti_1_0)/(trh0-ti_0))
    UA0 = Qh0/LMRT0
    def fh(x): 
            Eq = Q-UA0*((k2-ti_1+ti)/scipy.log((k2+x-ti_1)/(x-ti)))
            return Eq
        
    for j in range(Num_hours):
        if DATA.loc[j,'Qhsf'] != 0 and (DATA.loc[j,'tair'] == (tair0-273) or DATA.loc[j,'tair'] == 16):
            Q = DATA.loc[j,'Qhsf']
            ti = Temp.loc[j,'tsh_air'] + 273
            ti_1 = Temp.loc[j,'tsh_air_1']+ 273
            k2 = Q/mCw0
            DATA.loc[j,'trh'] = scipy.optimize.newton(fh, trh0, maxiter=1000,tol=0.01) - 273
            DATA.loc[j,'tsh'] = DATA.loc[j,'trh'] + k2
    
    return DATA.copy(),mCw0

# <codecell>

def calc_Ccoil(Temp,DATA,Qc0,tsc0,trc0,tair0):
    tair0 = tair0 + 273
    tsc0 = tsc0 + 273
    trc0 = trc0 + 273
    Qc0 = DATA.Qcsf.max()
    mCw0 = Qc0/(trc0-tsc0)
    Num_hours = DATA.tair.count()
    for j in range(Num_hours):
        if DATA.loc[j,'Qcsf'] == DATA.Qcsf.max():
            ti_1_0 = Temp.loc[j,'tsc_air_1'] + 273
            ti_0 = Temp.loc[j,'tsc_air'] + 273
    
    LMRT0 = (trc0-tsc0)/scipy.log((tsc0-ti_0)/(trc0-ti_0))
    UA0 = Qc0/LMRT0
    def fh(x): 
        Eq = mCw0*k2-UA0*(k2/(scipy.log((x-k2-ti)/(x-ti))))
        return Eq
        
    for j in range(Num_hours):
        if DATA.loc[j,'Qcsf'] > 0 and (DATA.loc[j,'tair'] == (tair0-273) or DATA.loc[j,'tair'] == 30):
            Q = DATA.loc[j,'Qcsf']
            ti = Temp.loc[j,'tsc_air'] + 273
            ti_1 = Temp.loc[j,'tsc_air_1']+ 273
            k2 = Q/mCw0
            DATA.loc[j,'trc'] = scipy.optimize.newton(fh, tsc0, maxiter=1000,tol=0.01) - 273
            DATA.loc[j,'tsc'] = DATA.loc[j,'trc'] - k2

    return DATA.copy(),mCw0

# <codecell>

def calc_w(t,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    Ps = 610.78*scipy.exp(t/(t+238.3*17.2694))
    Pv = RH/100*Ps
    w = 0.62*Pv/(Pa-Pv)
    return w

# <codecell>

def calc_h(t,w): # enthalpyh of most air in kJ/kg
    if 0 < t < 60:
        h = (1.007*t-0.026)+w*(2501+1.84*t)    
    elif -100 < t <= 0:
        h = (1.005*t)+w*(2501+1.84*t)
    return h

# <codecell>

def calc_t(w,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(RH/100*610.78*scipy.exp(x/(x+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 19, maxiter=100,tol=0.01)
    t = result.real
    return t

# <codecell>

def calc_RH(w,t): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(x/100*610.78*scipy.exp(t/(t+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 50, maxiter=100,tol=0.01)
    RH = result.real
    return RH

# <markdowncell>

# 2.1. Sub-Function Hourly thermal load

# <codecell>

def calc_TL(SystemH, SystemC, te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr):
    # assumptions
    # the installed capacities are assumed to be gigantic, it is assumed that the building can 
    # generate heat and cold at anytime
    IC = 500 
    IH = 500 
    if Losses == 1:
        #Losses due to emission and control of systems
        tintH_set = tintH_set + tHset_corr
        tintC_set = tintC_set + tCset_corr
    
    # Case 1 IHC_nd = 0
    IHC_nd = 0
    IC_nd_ac = 0
    IH_nd_ac = 0
    Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2
    tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
    tm = (tm_t+tm_t0)/2
    if SystemH ==2 or SystemC ==5:#by norm 29 max temperature of operation,
        t_TABS = 29 - (29-15)*(te_t-te_min)/(te_max-te_min)
        I_TABS = Af/0.08*(t_TABS-tm)
        Im_tot = Im_tot+I_TABS
        tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
        tm = (tm_t+tm_t0)/2
    ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)  
    tair0 = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
    top0 = 0.31*tair0+0.69*ts
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
        if SystemH ==2 or SystemC ==5:#by norm 29 max temperature of operation,
            t_TABS = 29 - (29-15)*(te_t-te_min)/(te_max-te_min)
            I_TABS = Af/0.08*(t_TABS-tm)
            Im_tot = Im_tot+I_TABS
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
            top_ac = 0.31*tair_ac+0.69*ts
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
            if SystemH ==2 or SystemC ==5:#by norm 29 max temperature of operation,
                t_TABS = 29 - (29-15)*(te_t-te_min)/(te_max-te_min)
                I_TABS = Af/0.08*(t_TABS-tm)
                Im_tot = Im_tot+I_TABS
                tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
                tm = (tm_t+tm_t0)/2
            ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd_ac)/Hve))/(Htr_ms+Htr_w+Htr_1)  
            tair_ac = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
            top_ac = 0.31*tair_ac+0.69*ts
       # Results
        if IHC_nd_ac > 0:
            IH_nd_ac = IHC_nd_ac
        else:
            IC_nd_ac = IHC_nd_ac

    Results = [tm_t, tair_ac ,top_ac, IH_nd_ac, IC_nd_ac]
    return list(Results)

# <markdowncell>

# 2.1. Sub-Function Shading Factors of movebale parts

# <codecell>

#It calculates the rediction factor of shading due to type of shading
def Calc_Rf_sh (ShadingPosition,ShadingType):
    #0 for not #1 for Louvres, 2 for Rollo, 3 for Venetian blinds, 4 for Courtain, 5 for Solar control glass
    d ={'Type':[0, 1, 2, 3, 4,5],'ValueIN':[1, 0.2,0.2,0.3,0.77,0.1],'ValueOUT':[1, 0.08,0.08,0.15,0.57,0.1]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 1: #1 is exterior
            return ValuesRf_Table.loc[row,'ValueOUT']
        elif ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 0: #0 is intetiror
            return ValuesRf_Table.loc[row,'ValueIN']

# <codecell>

def calc_gl(radiation, g_gl,Rf_sh):
    if radiation > 300: #in w/m2
        return g_gl*Rf_sh
    else:
        return g_gl

# <markdowncell>

# 2.2. Sub-Function equivalent profile of Occupancy

# <codecell>

def calc_Type(Profiles, Profiles_names, AllProperties, i, Servers, Coolingroom):
    profiles_num = len(Profiles)
    if Servers == 0:
        Profiles[1] = Profiles[0]
        
    if Coolingroom == 0:
        Profiles[10] = Profiles[15]
    
    Profiles[0].Ve = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Ve 
    Profiles[0].I_int = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].I_int
    Profiles[0].tintH_set = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].tintH_set
    Profiles[0].tintC_set = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].tintC_set
    Profiles[0].Mww = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Mww
    Profiles[0].Mw = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Mw
    Profiles[0].Ealf_ve = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Ealf_ve
    Profiles[0].Ealf_nove = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].Ealf_nove
    Profiles[0].People = AllProperties.loc[i,Profiles_names[0]] * Profiles[0].People
    for num in range(1,profiles_num):
        Profiles[0].Ve = Profiles[0].Ve + AllProperties.loc[i,Profiles_names[num]]*Profiles[num].Ve
        Profiles[0].I_int = Profiles[0].I_int + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].I_int
        Profiles[0].tintH_set = Profiles[0].tintH_set + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].tintH_set
        Profiles[0].tintC_set = Profiles[0].tintC_set + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].tintC_set
        Profiles[0].Mww = Profiles[0].Mww + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].Mww
        Profiles[0].Mw = Profiles[0].Mw + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].Mw
        Profiles[0].Ealf_ve = Profiles[0].Ealf_ve + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].Ealf_ve
        Profiles[0].Ealf_nove = Profiles[0].Ealf_nove + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].Ealf_nove
        Profiles[0].People = Profiles[0].People + AllProperties.loc[i,Profiles_names[num]] * Profiles[num].People
    return Profiles[0].copy()

# <markdowncell>

# 2.3 Sub-Function calculation of thermal losses of emission systems differet to air conditioning

# <codecell>

def calc_Qem_ls(SystemH,SystemC):
    tHC_corr = [0,0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 4 or 1:
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 2: 
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 3: # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1 #regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2
    
    if SystemC == 4:
        tHC_corr[1] = 0 - 1.2
    elif SystemC == 5: 
        tHC_corr[1] = - 0.4 - 1.2
    elif SystemC == 3: # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 - 1 #regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + - 1.2
        
    return list(tHC_corr)

# <markdowncell>

# 2.1. Sub-Function losses heating system distribution

# <codecell>

def calc_Qdis_ls(SystemH,SystemC,nf,nfpercent, Lw,Ll,year,Af,twws, Bf, Renovated, Occupancy,Seasonhours,footprint):
    # Local variables
    D = 20 #in mm the diameter of the pipe to calculate losses
    tws = 32 # t at the spurs according to EN 1516 3-2
    # Ifdentification of linera trasmissivity coefficeitn dependent on dimensions and year of construction of building W/(m.K)
    if year >= 1995 or Renovated == 'Yes':
        Y = [0.2,0.3,0.3]
    elif 1985 <= year < 1995 and Renovated == 'No':
        Y = [0.3,0.4,0.4]
    else:
        Y = [0.4,0.4,0.4]
    
    fforma = Calc_form(Lw,Ll,footprint)
    # Identification of equivalent lenghts
    Lv = (2*Ll+0.0325*Ll*Lw+6)*fforma
    Lvww_c = (2*Ll+0.0125*Ll*Lw)*fforma
    Lvww_dis = (Ll+0.0625*Ll*Lw)*fforma
    
    # Calculate tamb in basement according to EN
    hours = Occupancy.tamb.count()
    for hour in range(hours):
        if Seasonhours[0] < hour < Seasonhours[1]: # cooling season
            Occupancy.loc[hour,'tamb'] = Occupancy.loc[hour,'tintC_set'] - Bf*(Occupancy.loc[hour,'tintC_set']-Occupancy.loc[hour,'te'])
        elif 0 <= hour <= Seasonhours[0] or Seasonhours[1] <= hour <= 8759:
            Occupancy.loc[hour,'tamb'] = Occupancy.loc[hour,'tintH_set'] - Bf*(Occupancy.loc[hour,'tintH_set']-Occupancy.loc[hour,'te'])
    
    # Calculation of losses only nonrecoverable losses are considered for the calculation, # those of the distribution in the basement for space heating and cooling system
    # This part applies the method described by SIA 2044
    if SystemH != 0:
        if Occupancy['Qhs'].max()!=0:
            Occupancy['Qhs_d_ls'] = ((Occupancy['tsh']+Occupancy['trh'])/2-Occupancy['tamb'])*(Occupancy['Qhs']/Occupancy['Qhs'].max())*(Lv*Y[0]) 
        else:
            Occupancy['Qhs_d_ls'] = 0
    
    if SystemC != 0:    
        if Occupancy['Qcs'].min()!=0:       
            Occupancy['Qcs_d_ls'] = ((Occupancy['tsc']+Occupancy['trc'])/2-Occupancy['tamb'])*(Occupancy['Qcs']/Occupancy['Qcs'].min())*(Lv*Y[0])
        else:
            Occupancy['Qcs_d_ls']=0
    
    # CIRUCLATION LOSSES
    Occupancy['Qww_d_circ'] = (twws-Occupancy['tamb'])*Y[0]*(Lvww_c)*(Occupancy['Mww']/Occupancy['Mww'].max())
    # DISTRIBUTION LOSSES
    Occupancy['Qww_d_dis'] = 0
    V = (Lvww_dis)* ((D/1000)**2/4)*scipy.pi # voume in the network in m3
    # add distribution losses
    rows = Occupancy.tamb.count()
    p = 988
    c = 4.184
    li = Lvww_dis
    Flowtap = (12*3/1000) # 12 l/min during 3 min every tap opening
    for j in range(rows):
        if Occupancy.loc[j,'Mww']>0: 
            t = 3600/((Occupancy.loc[j,'Mww']*Af/1000)/Flowtap)
            if t > 3600: t =3600
            q = (twws-Occupancy.loc[j,'tamb'])*Y[0]
            exponential = scipy.exp(-(q*li*t)/(p*c*V*(twws-Occupancy.loc[j,'tamb'])*1000))
            Occupancy.loc[j,'tamb'] = Occupancy.loc[j,'tamb'] + (twws-Occupancy.loc[j,'tamb'])*exponential  
            Occupancy.loc[j,'Qww_d_dis'] = (twws-Occupancy.loc[j,'tamb'])*V*c*p/1000*278
        else:
            Occupancy.loc[j,'Qww_d_dis'] = 0
    
    Occupancy['Qww_d_ls'] =  Occupancy['Qww_d_dis'] + Occupancy['Qww_d_circ']
    
    return Occupancy.copy()

# <codecell>

def calc_Qww_dis_ls(nf,nfpercent,Lw,Ll,year,Af,twws, Bf, Renovated, Occupancy,Seasonhours,footprint,calcintload):
    # Local variables
    D = 20 #in mm the diameter of the pipe to calculate losses
    tws = 32 # t at the spurs according to EN 1516 3-2
    # Ifdentification of linera trasmissivity coefficeitn dependent on dimensions and year of construction of building W/(m.K)
    if year >= 1995 or Renovated == 'Yes':
        Y = [0.2,0.3,0.3]
    elif 1985 <= year < 1995 and Renovated == 'No':
        Y = [0.3,0.4,0.4]
    else:
        Y = [0.4,0.4,0.4]  
    
    fforma = Calc_form(Lw,Ll,footprint)
    # Identification of equivalent lenghts
    hf = 3
    # standard height of every floor
    Lc = 2*(Ll+2.5+nf*nfpercent*hf)*fforma
    #Lsww_c = 0.075*Ll*Lw*nf*nfpercent*hf*fforma
    Lsww_dis = 0.038*Ll*Lw*nf*nfpercent*hf*fforma
    
    # Calculate tamb in basement according to EN
    if calcintload == 1:
        hours = Occupancy.tamb.count()
        for hour in range(hours):
            if Seasonhours[0] < hour < Seasonhours[1]: # cooling season
                Occupancy.loc[hour,'tamb'] = Occupancy['tintC_set'].min()
            else:
                Occupancy.loc[hour,'tamb'] = Occupancy['tintH_set'].max()
    else:
        Occupancy['tamb'] = Occupancy['tair']
    
    # CIRUCLATION LOSSES
    Occupancy['Qww_dh_circ'] = (twws-Occupancy['tamb'])*Y[1]*Lc*(Occupancy['Mww']/Occupancy['Mww'].max())
    # DISTRIBUTION LOSSES
    Occupancy['Qww_dh_dis'] = 0
    V = (Lsww_dis)* ((D/1000)**2/4)*scipy.pi # voume in the network in m3
    # add distribution losses
    rows = Occupancy.tamb.count()
    p = 988
    c = 4.184
    li = Lsww_dis
    Flowtap = (12*3/1000) # 12 l/min during 3 min every tap opening
    for j in range(rows):
        if Occupancy.loc[j,'Mww']>0: 
            t = 3600/((Occupancy.loc[j,'Mww']*Af/1000)/Flowtap)
            if t > 3600: t =3600
            q = (twws-Occupancy.loc[j,'tamb'])*Y[1]
            exponential = scipy.exp(-(q*li*t)/(p*c*V*(twws-Occupancy.loc[j,'tamb'])*1000))
            Occupancy.loc[j,'tamb'] = Occupancy.loc[j,'tamb'] + (twws-Occupancy.loc[j,'tamb'])*exponential  
            Occupancy.loc[j,'Qww_dh_dis'] = (twws-Occupancy.loc[j,'tamb'])*V*c*p/1000*278
        else:
            Occupancy.loc[j,'Qww_dh_dis'] = 0
    Occupancy['Qww_dh_ls'] =  Occupancy['Qww_dh_dis']+ Occupancy['Qww_dh_circ']       
    
    return Occupancy.copy()

# <codecell>

#a factor taking into account that Ll and lw are measured from an aproximated rectangular surface
def Calc_form(Lw,Ll,footprint): 
    factor = footprint/(Lw*Ll)
    return factor

# <codecell>

def calc_Aux_hscs(nf,nfpercent,Lw,Ll,footprint,Year,Qhs0,tsh0,trh0,dataTemplate,Qcs0,tsc0,trc0,SystemH,SystemC,twws,tw): 
    data = dataTemplate.copy()
    # accoridng to SIA 2044
    # Identification of equivalent lenghts
    hf = 3
    fforma = Calc_form(Lw,Ll,footprint)
    # constants
    deltaP_l = 0.1
    fsr = 0.3
    cp = 1000*4.186
    #variable depending on new or old building. 2000 as time line
    if Year >= 2000:
        b =1
    else:
        b =1.2
        
    # for heating system   
    #the power of the pump in Watts 
    if SystemH != 3 or SystemH != 0:
        fctr = 1.05
        qV_des = Qhs0*1000/((tsh0-trh0)*cp)
        Imax = 2*(Ll+Lw/2+hf+(nf*nfpercent)+10)*fforma          
        deltaP_des = Imax*deltaP_l*(1+fsr)
        Phy_des = 0.2278*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        hours = data.tamb.count()
        for hour in range(hours):
            if data.loc[hour,'Qhsf'] > 0:
                if data.loc[hour,'Qhsf']/Qhs0 > 0.67:
                    Ppu_dis_hy_i = Phy_des
                    feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                    data.loc[hour,'Eaux_hs'] = Ppu_dis_hy_i*feff
                else:
                    Ppu_dis_hy_i = 0.0367*Phy_des
                    feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                    data.loc[hour,'Eaux_hs'] = Ppu_dis_hy_i*feff
    else:
        data.loc[hour,'Eaux_hs']=0
      
    # for Cooling system   
    #the power of the pump in Watts 
    if SystemH != 3 or SystemH != 0:
        fctr = 1.10
        qV_des = Qcs0/((trc0-tsc0)*cp)
        Imax = 2*(Ll+Lw/2+hf+(nf*nfpercent)+10)*fforma          
        deltaP_des = Imax*deltaP_l*(1+fsr)
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        hours = data.tamb.count()
        for hour in range(hours):
            if data.loc[hour,'Qcsf'] > 0:
                if data.loc[hour,'Qcsf']/(Qcs0*1000) > 0.67:
                    Ppu_dis_hy_i = Phy_des
                    feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                    data.loc[hour,'Eaux_cs'] = Ppu_dis_hy_i*feff
                else:
                    Ppu_dis_hy_i = 0.0367*Phy_des
                    feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                    data.loc[hour,'Eaux_cs'] = Ppu_dis_hy_i*feff 
    else:
        data.loc[hour,'Eaux_cs']=0
    
    # for domestichotwater 
    #the power of the pump in Watts 
    qV_des = data['Qwwf'].max()/((twws-tw)*cp)
    Imax = 2*(Ll+2.5+hf+(nf*nfpercent))*fforma          
    deltaP_des = Imax*deltaP_l*(1+fsr)
    Phy_des = 0.2778*deltaP_des*qV_des
    feff = (1.25*(200/Phy_des)**0.5)*fctr*b
    Ppu_dis = Phy_des*feff
    #the power of the pump in Watts 
    hours = data.tamb.count()
    for hour in range(hours):
        if data.loc[hour,'Qwwf']>0:
            if data.loc[hour,'Qwwf']/data['Qwwf'].max() > 0.67:
                Ppu_dis_hy_i = Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
                data.loc[hour,'Eaux_ww'] = Ppu_dis_hy_i*feff
            else:
                Ppu_dis_hy_i = 0.0367*Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
                data.loc[hour,'Eaux_ww'] = Ppu_dis_hy_i*feff 
    
    return data

# <markdowncell>

# ##STATISTICAL ENERGY MODEL

# <codecell>

def Querystatistics(CQ, CQ_name, Model, locationtemp1,locationFinal):

    #Create the table or database of the CQ to generate the values
    OutTable = 'Database.dbf'
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database0 = dbf2df(locationtemp1+'\\'+OutTable)
    
    #THE FIRST PART RELATED TO THE BUILDING PROPERTIES
    
    #Assing main use of the building To assign systems of heating or cooling in a building basis.
    Database = MainUse(Database0)
    
    # assign the year of each category and create a new code 
    Database['YearCat'] = Database.apply(lambda x: YearCategoryFunction(x['Year'], x['Renovated']), axis=1)
    Database['CODE'] = Database.Type + Database.YearCat
    # Create join with the model
    Joineddata = pd.merge(Database, Model, left_on='CODE', right_on='Code')
    Joineddata.rename(columns={'Hs_x':'Hs'},inplace=True)
    # EXPORT PROPERTIES
    Joineddata.to_excel('c:\ArcGIS\EDMdata\Statistical'+'\\'+CQ_name+'\\'+'Properties.xls',
                        sheet_name='Values',index=False,cols={'Name','tsh0','trh0','tsc0','trc0','Hs','Es','PFloor','Year','fwindow',
                                                              'Floors','Construction','Emission_heating','Emission_cooling',
                                                              'Uwall','Uroof','Ubasement','Uwindow'})
                                                                                  
    #EXPORT PROPERTIES RELATED TO PROCESEES AND EQUIPMENT
    Counter = Joineddata.INDUS.count()
    Joineddata['E4'] = Joineddata['SRFlag'] = Joineddata['CRFlag'] = Joineddata['ICEFlag'] = 0
    for row in range(Counter):
        if Joineddata.loc[row,'INDUS'] >0:
            Joineddata.loc[row,'E4'] = 1
        if Joineddata.loc[row,'SR'] >0:
            Joineddata.loc[row,'SRFlag'] = 1
        if Joineddata.loc[row,'ICE'] >0:
            Joineddata.loc[row,'ICEFlag'] = 1     
        if Joineddata.loc[row,'CR'] >0:
            Joineddata.loc[row,'CRFlag'] = 1            
    
    Joineddata.to_excel('c:\ArcGIS\EDMdata\Statistical'+'\\'+CQ_name+'\\'+'Equipment.xls',
                        sheet_name='Values',index=False,cols={'Name','CRFlag','SRFlag','ICEFlag',
                                                              'E4'})
                                                                                                                                
    
    #THE OTHER PART RELATED TO THE ENERGY VALUES'
    DatabaseUnpivoted = pd.melt(Database, id_vars=('Name','Shape_Area','YearCat','Hs','Floors'))
    DatabaseUnpivoted['CODE'] = DatabaseUnpivoted.variable + DatabaseUnpivoted.YearCat
    #Now both Database with the new codification is merged or joined to the values of the Statistical model
    DatabaseModelMerge = pd.merge(DatabaseUnpivoted, Model, left_on='CODE', right_on='Code')
    
    #Now the values are created. as all the intensity values are described in MJ/m2. 
    ##they are transformed into MWh, Heated space is assumed as an overall 90% of the gross area according to the standard SIA, 
    ##unless it is known (Siemens buildings and surroundings, Obtained during visual inspection a report of the area Grafenau)
    counter = DatabaseModelMerge.value.count()
    for r in range (counter):
        if DatabaseModelMerge.loc[r,'Hs_x']>=0:
            DatabaseModelMerge.loc[r,'Hs_y'] = DatabaseModelMerge.loc[r,'Hs_x']
            
    DatabaseModelMerge['Qhsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhsf_kWhm2/1000
    DatabaseModelMerge['Qhpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhpf_kWhm2/1000
    DatabaseModelMerge['Qwwf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qwwf_kWhm2/1000
    DatabaseModelMerge['Qcsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcsf_kWhm2/1000
    DatabaseModelMerge['Qcdataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcdataf_kWhm2/1000
    DatabaseModelMerge['Qcicef'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcicef_kWhm2/1000
    DatabaseModelMerge['Qcpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcpf_kWhm2/1000
    DatabaseModelMerge['Ealf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Es* DatabaseModelMerge.Ealf_kWhm2/1000
    DatabaseModelMerge['Edataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Edataf_kWhm2/1000 
    DatabaseModelMerge['Epf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Epf_kWhm2/1000
    DatabaseModelMerge['Ecaf'] = 0 #compressed air is 0 for all except siemens where data is measured.
    
    # Pivoting the new table and summing rows all in MWh
    Qhsf = pd.pivot_table(DatabaseModelMerge, values='Qhsf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qhpf = pd.pivot_table(DatabaseModelMerge, values='Qhpf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qwwf = pd.pivot_table(DatabaseModelMerge, values='Qwwf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qcsf = pd.pivot_table(DatabaseModelMerge, values='Qcsf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Qcdataf = pd.pivot_table(DatabaseModelMerge, values='Qcdataf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows') 
    Qcicef = pd.pivot_table(DatabaseModelMerge, values='Qcicef', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows') 
    Qcpf = pd.pivot_table(DatabaseModelMerge, values='Qcpf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Ealf = pd.pivot_table(DatabaseModelMerge, values = 'Ealf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Edataf = pd.pivot_table(DatabaseModelMerge, values='Edataf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Epf = pd.pivot_table(DatabaseModelMerge, values='Epf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Ecaf = pd.pivot_table(DatabaseModelMerge, values='Ecaf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    
    Total = pd.DataFrame({'Qhsf': Qhsf['All'],'Qhpf': Qhpf['All'],'Qwwf': Qwwf['All'],'Qcsf': Qcsf['All'],'Qcpf': Qcpf['All'],
                         'Ealf': Ealf['All'],'Epf': Epf['All'],'Edataf': Edataf['All'],'Qcdataf': Qcdataf['All'],
                         'Ecaf': Ecaf['All'],'Qcicef': Qcicef['All'] })
    # reset index
    Total['Name'] = Total.index
    counter = Total.Qhsf.count()
    Total.index = range(counter)
    
    Total.to_csv(locationFinal+'\\'+CQ_name+'\\'+'Loads.csv', index=False)
    
    return Total

# <markdowncell>

# This function estimates the main type of ocupation in the building. as a result those values such as coefficients of trasnmittance, temperatures of operation and type of emission systems are selected in a mayority basis.

# <codecell>

def MainUse(Database0):
    uses = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU','EDU','CR','HEALTH','SPORT',
            'SWIM','PUBLIC','SUPER','ICE','HOT']  
    Database0['Type'] = 'MDU'
    n_buildings = Database0.ADMIN.count()
    n_uses = len(uses)
    for r in range (n_uses):
        for row in range(n_buildings):
            if Database0.loc[row, uses[r]]>=0.5:
                Database0.loc[row, 'Type']= uses[r]
    return Database0.copy()

# <markdowncell>

# Sub-function: assign As the values in the statistical model are codified according to a secuence of 1, 2, 3, 4 and 5, a function has to be define to codify in the same therms the Database, a new filed (YearCAt) is assigned to the Database

# <codecell>

def YearCategoryFunction(x,y):
    if x <= 1920:
        #Database['Qh'] = Database.ADMIN.value * Model.
        result = '1'
    elif x > 1920 and x <= 1970:
        result = '2'
    elif x > 1970 and x <= 1980:
        result = '3'
    elif x > 1980 and x <= 2000:
        result = '4'
    elif x > 2000 and x <= 2020:
        result = '5'
    elif x > 2020:
        result = '6'
        
    if x <= 1920 and y=='Yes':
        result = '7'
    elif 1920 < x <= 1970 and y=='Yes':
        result = '8'
    elif 1970 < x <= 1980 and y=='Yes':
        result = '9'
    elif 1980 < x <= 2000 and y=='Yes':
        result = '10'
    
    return result

