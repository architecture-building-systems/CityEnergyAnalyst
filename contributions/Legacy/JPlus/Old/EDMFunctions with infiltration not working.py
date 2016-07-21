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
        # without infiltration - this value is calculated later on
        Occupancy0['Hve'] =  pa_ca*(Occupancy0['Ve']* Af/3600)
        
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
        Occupancy['I_int'] = Occupancy['I_int']*Af+ Occupancy['Qww_dh_ls']*0.8# 80% is recoverable or enter to play in the energy balance
        
        #Determination of Heat Flows for internal loads in W
        Occupancy['I_ia'] = 0.5*Occupancy['I_int']
        
        # Calculation Shading factor per hour due to operation of external shadings, 1 when I > 300 W/m2
        Rf_sh = Calc_Rf_sh(AllProperties.loc[i,'Shading_Po'],AllProperties.loc[i,'Shading_Ty'])
        # Calculation of effecive solar area of surfaces in m2, opaque areas are not considered, reduction factor of overhangs is not included. Fov =0
    
        Num_Hours = Occupancy.tamb.count()
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
        tHC_corr = calc_Qem_ls(str(SystemH),str(SystemC))
        tHset_corr = tHC_corr[0]
        tCset_corr = tHC_corr[1]
        
        Occupancy.loc[0,'tm_t'] = Occupancy.loc[0,'te']
        for j in range(1,Num_Hours):  #mode = 0 
            # first calculation without Losses to get real operation and air temperatures
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
            
            Results0 = calc_TL(str(SystemH),str(SystemC), te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1,
                               Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,
                               tCset_corr)
            #Occupancy.loc[j,'tm_t'] = Results0[0]
            Occupancy.loc[j,'tair'] = Results0[1] # temperature of inside air
            #Occupancy.loc[j,'top'] = Results0[2] # temperature of operation
            #Occupancy.loc[j,'Qhs'] = Results0[3] # net heating load
            #Occupancy.loc[j,'Qcs'] = Results0[4] # net cooling load
            
        #NOW CONSIDERING INFILTRATION
        Temp0 = calc_infiltration(Temp,Occupancy,Awall, Yearcat,height,nfpercent)
        Occupancy['Hve'] =  pa_ca*(Occupancy['Ve']* Af/3600+ Temp0['Ve_inf'])
        Num_Hours = Occupancy.tamb.count()
        for hour in range(Num_Hours):
            Coefficients = calc_Htr(Occupancy.loc[hour,'Hve'], AllProperties.loc[i,'Htr_is'], AllProperties.loc[i,'Htr_ms'], AllProperties.loc[i,'Htr_w'])
            Occupancy.loc[hour,'Htr_1'] = Coefficients[0]
            Occupancy.loc[hour,'Htr_2'] = Coefficients[1]
            Occupancy.loc[hour,'Htr_3'] = Coefficients[2]    
        
        # Determination of Heat Flows for internal heat sources
        Occupancy['I_m'] = (AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])*(Occupancy['I_ia']+Occupancy['I_sol'])
        Occupancy['I_st'] = (1-(AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])-(AllProperties.loc[i,'Htr_w']/(9.1*AllProperties.loc[i,'Atot'])))*(Occupancy['I_ia']+Occupancy['I_sol'])
            
        for j in range(1,Num_Hours):    
            # Determination of net thermal loads and temperatures including emission losses
            Losses = 0
            #tm_t0 = Occupancy.loc[j-1,'tm_t']
            #te_t = Occupancy.loc[j,'te']
            #tintH_set = Occupancy.loc[j,'tintH_set']
            #tintC_set = Occupancy.loc[j,'tintC_set']
            #Htr_em = AllProperties.loc[i,'Htr_em']
            #Htr_ms = AllProperties.loc[i,'Htr_ms']
            #Htr_is = AllProperties.loc[i,'Htr_is']
            Htr_1 = Occupancy.loc[j,'Htr_1']
            Htr_2 = Occupancy.loc[j,'Htr_2']
            Htr_3 = Occupancy.loc[j,'Htr_3']
            Hve = Occupancy.loc[j,'Hve']
            #Htr_w = AllProperties.loc[i,'Htr_w']
            I_st = Occupancy.loc[j,'I_st']
            I_ia = Occupancy.loc[j,'I_ia']
            I_m = Occupancy.loc[j,'I_m']
            #Cm = AllProperties.loc[i,'Cm']
            
            Results0 = calc_TL(str(SystemH),str(SystemC), te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1,
                               Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,
                               tCset_corr)
            Occupancy.loc[j,'tm_t'] = Results0[0]
            Occupancy.loc[j,'tair'] = Results0[1] # temperature of inside air
            Occupancy.loc[j,'top'] = Results0[2] # temperature of operation
            Occupancy.loc[j,'Qhs'] = Results0[3] # net heating load
            Occupancy.loc[j,'Qcs'] = Results0[4] # net cooling load
            
            Losses = 1
            Results1 = calc_TL(str(SystemH),str(SystemC), te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1,
                               Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr)
            Occupancy.loc[j,'Qhs_em_ls'] = Results1[3]- Occupancy.loc[j,'Qhs'] # losses emission and control
            Occupancy.loc[j,'Qcs_em_ls'] = Results1[4]- Occupancy.loc[j,'Qcs'] #losses emission and control

        #Calculation of the emission factor of the distribution system
        Emissionfactor = calc_em_t(str(SystemH),str(SystemC))
        nh = Emissionfactor[4]
    
        # sum of final energy up to the generation first time
        Occupancy['Qhsf'] = Occupancy['Qhs']
        Occupancy['Qcsf'] = -Occupancy['Qcs']
        Occupancy['Qwwf'] = Occupancy['Qww'] 
        
        Occupancy.to_csv(r'C:\ArcGIS\Toerase0.csv')
        
        #Qc MUST BE POSITIVE
        #Calculation temperatures of the distribution system during time
        Results2 = calc_temperatures(str(SystemH),str(SystemC),Occupancy,Temp0,tsh0,trh0,tsc0,trc0,nh,nf,Af)
        Occupancy2 = Results2[0]
    
        #Calculation of lossess distribution system for space heating space cooling 
        Occupancy3 = calc_Qdis_ls(str(SystemH),str(SystemC), nf,nfpercent,Lw,Ll,Year,Af,twws, Bf, AllProperties.loc[i,'Renovated'],
                    Occupancy2, Seasonhours,footprint)

        #Calculation of lossess distribution system for domestic hot water 
        Occupancy4 = calc_Qww_dis_ls(nf, nfpercent, Lw, Ll, Year,Af,twws, Bf, AllProperties.loc[i,'Renovated'],
                    Occupancy3, Seasonhours,footprint,0)#0 when real loads are calculated
        
        Occupancy4.to_csv(r'C:\ArcGIS\Toerase.csv')
    
        Occupancy4['Qww_dis_ls'] = Occupancy4['Qww_d_ls']+ Occupancy4['Qww_dh_ls']
        Occupancy4['Qcs_dis_em_ls'] = -(Occupancy4['Qcs_em_ls']+ Occupancy4['Qcs_d_ls'])
        Occupancy4['Qhs_dis_em_ls'] = Occupancy4['Qhs_em_ls']+ Occupancy4['Qhs_d_ls']    
        # sum of final energy up to the generation
        Occupancy4['Qhsf'] = Occupancy4['Qhs']+Occupancy4['Qhs_dis_em_ls']#it is already taking into account contributon of heating system.
        Occupancy4['Qcsf'] = -Occupancy4['Qcs']+Occupancy4['Qcs_dis_em_ls']
        Occupancy4['Qwwf'] = Occupancy4['Qww'] + Occupancy4['Qww_dis_ls']
        
        Occupancy4.to_csv(r'C:\ArcGIS\Toerase2.csv')
    
        #Calculation temperatures of the distribution system during time second time
        Results3 = calc_temperatures(str(SystemH),str(SystemC),Occupancy4,Temp0,tsh0,trh0,tsc0,trc0,nh,nf,Af)
        Occupancy5 = Results3[0]
        Qhs0 = Results3[1]/1000
        Qcs0 = Results3[2]/1000
        mwh0 = Results3[3]/4190
        mwc0 = Results3[4]/4190
        tsh0 = Results3[5]
        trh0 = Results3[6]
        tsc0 = Results3[7]
        trc0 = Results3[8]
        
        Occupancy5.to_csv(r'C:\ArcGIS\Toerase3.csv')
        
        for j in range(1,Num_Hours):
            if Seasonhours[0] < j < Seasonhours[1]:
                Occupancy4.loc[j,'Qhs'] = 0
                Occupancy4.loc[j,'Qhsf'] = 0
                Occupancy4.loc[j,'Qhs_em_ls'] = 0
                Occupancy4.loc[j,'Qhs_d_ls'] = 0
                Occupancy4.loc[j,'tsh'] = 0
                Occupancy4.loc[j,'trh'] = 0
            elif 0 <= j <= Seasonhours[0] or Seasonhours[1] <= j <= 8759:
                Occupancy4.loc[j,'Qcs'] = 0
                Occupancy4.loc[j,'Qcsf'] = 0
                Occupancy4.loc[j,'Qcs_em_ls'] = 0  
                Occupancy4.loc[j,'Qcs_d_ls'] = 0
                Occupancy4.loc[j,'tsc'] = 0
                Occupancy4.loc[j,'trc'] = 0
        
        #calculation of energy for pumping of all the systems (no air-conditioning
        Occupancy6 =  calc_Aux_hscs(nf,nfpercent,Lw,Ll,footprint,Year,Qhs0,tsh0,trh0,Occupancy5,Qcs0,tsc0,trc0,
                                    str(SystemH),str(SystemC),twws,tw)
    
        #Calculation of Electrical demand
        if SystemC == 'Air conditioning' or SystemC == 'Ceiling cooling':
            for j in range(Num_Hours):  #mode = 0  
                if Seasonhours[0] < j < Seasonhours[1]: #cooling season air conditioning 15 may -15sept
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_ve'] + Occupancy6.loc[j,'Ealf_nove'])*AllProperties.loc[i,'Aef']
                else:
                    Occupancy6.loc[j,'Eal'] = (Occupancy6.loc[j,'Ealf_nove'])*Aef
                    
        if SystemH == 'Air conditioning':
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
        Qhs0 = 0
        Qcs0 = 0
        
    Occupancy6['Eaux'] = Occupancy6['Eaux_hs'] + Occupancy6['Eaux_cs'] + Occupancy6['Eaux_ww']
    Occupancy6['Ealf'] = Occupancy6['Eal'] + Occupancy6['Eaux']
    Occupancy6['NAME'] = AllProperties.loc[i,'Name']
    
    # Calculate Occupancy
    Occupancy6['Occupancy'] = Occupancy6['People']*Af
    
    # Results
    Result_TL = pd.DataFrame(Occupancy6,columns = ['DATE','NAME','Qhs_dis_em_ls','Qcs_dis_em_ls','Qww_dis_ls','Qhs','Qcs','Qww','Qhsf','Qcsf','Qwwf','Ealf','Eaux',
                                                    'I_sol','I_int','tsh','trh','tsc','trc','tair','top','te','Occupancy'])
    Totals_TL = pd.DataFrame(Result_TL.sum()).T/1000000 #in MWh
    GT = {'Name':[AllProperties.loc[i,'Name']],'Qhs_dis_em_ls':Totals_TL.Qhs_dis_em_ls,'Qhsf':Totals_TL.Qhsf,'Qcs_dis_em_ls':Totals_TL.Qcs_dis_em_ls,'Qcsf':Totals_TL.Qcsf,
                  'Qhs':Totals_TL.Qhs,'Qcs':Totals_TL.Qcs,'Qww':Totals_TL.Qww,'Qww_dis_ls':Totals_TL.Qww_dis_ls,'Qwwf':Totals_TL.Qwwf,
                   'Ealf':Totals_TL.Ealf,'Eaux':Totals_TL.Eaux,'Occupancy':Totals_TL.Occupancy,'tsh0':tsh0,'trh0':trh0,'tsc0':tsc0,'trc0':trc0,'Qhs0':Qhs0,'Qcs0':Qcs0,'mwh0':mwh0,'mwc0':mwc0,'Af':Af}
    Grandtotal = pd.DataFrame(GT)
    # EXPORT RESULTS
    Result_TL.to_csv(locationFinal+'\\'+Name+'.csv',index=False)
    Grandtotal.to_csv(locationFinal+'\\'+Name+'T'+'.csv')
    return Grandtotal

# <codecell>

def calc_infiltration(Temp,Occupancy,Awall,Yearcat,height,nfpercent):
    if Yearcat <= 5:         # all renovated buildings plus those from 2000 on are considered tight
        K1 = 0.1
        K2 = 0.011
        K3 = 0.034
    elif 2 < Yearcat <= 4:   # these categories are considered medium
        K1 = 0.1
        K2 = 0.017
        K3 = 0.049   
    else:                    # up to 1970 and not renovated are poorly 
        K1 = 0.1
        K2 = 0.023
        K3 = 0.007 
    Temp['Wind_net'] = 0.21*Temp['Wind']*height**0.33 # city center conditions urban         
    Temp['Ve_inf'] =  0#(K1 + K2*abs(Temp['te'] - Occupancy['tair'])+K3*Temp['Wind_net'])*Awall*nfpercent*3/3600
    
    return Temp.copy()

# <markdowncell>

# Calc temperatures distribution system

# <codecell>

def calc_temperatures(SystemH,SystemC,DATA,Temp0,tsh0,trh0,tsc0,trc0,nh,Af,Floors):
    # FOR HEATING SYSTEMS FOLLOW THIS
    if SystemH == 'No':
        Qhsmax = 0
    else:
        Qh0 = Qhsmax = DATA['Qhsf'].max()
        tair0 = DATA['tintH_set'].max()
        if SystemH == 'Air conditioning':
            HVAC = calc_HVAC(DATA,Temp0,tsh0,trh0,Qh0,tair0,nh)
            RESULT = HVAC[0]
            
        elif SystemH == 'Radiator':
            rad = calc_RAD(DATA,tsh0,trh0,Qh0,tair0,nh)
            RESULT = rad[0]
            mwh0 = rad[1]/4190
            
        elif SystemH == 'Floor heating':
            fH = calc_TABSH(DATA,Qh0,tair0,Af,Floors)
            RESULT = fh[0]
            mwh0 = fh[1]/4190
            tsh0 = rad[2] # this values are designed for the conditions of the building
            trh0 = rad[3] # this values are designed for the conditions of the building
    
    if SystemC == 'No':
        Qcsmax = 0
    else:
        Qc0 = Qcsmax = DATA['Qcsf'].max()
        tair0 = DATA['tintC_set'].min()
        if SystemC == 'Ceiling cooling': # it is considered it has a ventilation system to regulate moisture.
            fc = calc_TABSC(DATA, Qc0,tair0,Af)
            RESULT = fc[0]
            mwc0 = fc[1]/4190
            tsc0 = fc[2]
            trc0 = fc[3] 
                    
    return RESULT.copy(),Qhsmax,Qcsmax, mwh0, mwc0, tsh0, trh0, tsc0, trc0

# <markdowncell>

# 2.1 Sub-function temperature radiator systems

# <codecell>

def calc_RAD(DATA,tsh0,trh0,Qh0,tair0,nh):
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
    return DATA.copy(), mCw0, tsh0, trh0

# <markdowncell>

# 2.1 Sub-function temperature Floor activated slabs

# <codecell>

def calc_TABSH(DATA, Qh0,tair0,Floors,Af):
    tair0 = tair0 + 273
    tmean_max = tair0 + 10           # according ot EN 1264, simplifying to +9 k inernal surfaces and 15 perimeter and batroom    
    nh = 0.025
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
        if DATA.loc[row,'Qhsf'] != 0 (DATA.loc[row,'tair'] == (tair0-273) or DATA.loc[row,'tair'] == 16):
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

def calc_TABSC(DATA, Qc0,tair0, Af):
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

def calc_HVAC(Temp,DATA,tsh0,trh0,Qh0,tair0,nh):
    #Claculate net ventilation required taking into account losses and efficiency of ventilation system
    #assumptions
    # ev = 1
    #nrec_teta = 0.75    
    #Cctr = 0.8
    #Cdu_lea = 
    #Ci_lea = Cdu_lea*CAHU_lea
    #CRCA = 
    
    # DATA['Ve_req'] = (DATA['Ve']+Temp0['Ve_inf'])*Cctr*Ci_lea*CRCA/ev
    
    return 0

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
    if SystemH =='Floor heating' or SystemC =='Floor cooling':#by norm 29 max temperature of operation,
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
        if SystemH =='Floor heating' or SystemC =='Floor cooling':#by norm 29 max temperature of operation,
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
            if SystemH =='Floor heating' or SystemC =='Floor cooling':#by norm 29 max temperature of operation,
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
    if SystemH == 'Ceiling heating' or 'Radiator':
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 'Floor heating': 
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 'Air conditioning': # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1 #regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2
    
    if SystemC == 'Ceiling cooling':
        tHC_corr[1] = 0 - 1.8
    elif SystemC == 'Floor cooling': 
        tHC_corr[1] = - 0.4 - 1.8
    elif SystemC == 'Air conditioning': # no emission losses but emissions for ventilation
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
    hf = 3*(nf-1) # standard height of every floor -1 for the distribution system
    Lv = (2*Ll+0.0325*Ll*Lw+6)*fforma
    Lvww_c = (2*Ll+0.0125*Ll*Lw)*fforma
    Lvww_dis = (Ll+0.0625*Ll*Lw)*fforma
    Lsww_c = (0.075*Ll*Lw*nf*nfpercent*hf)*fforma
    Lsww_dis = (0.038*Ll*Lw*nf*nfpercent*hf)*fforma
    Lslww_dis = (0.05*Ll*Lw*nf*nfpercent)*fforma
    
    # Calculate tamb in basement according to EN
    hours = Occupancy.tamb.count()
    for hour in range(hours):
        if Seasonhours[0] < hour < Seasonhours[1]: # cooling season
            Occupancy.loc[hour,'tamb'] = Occupancy.loc[hour,'tintC_set'] - Bf*(Occupancy.loc[hour,'tintC_set']-Occupancy.loc[hour,'te'])
        elif 0 <= hour <= Seasonhours[0] or Seasonhours[1] <= hour <= 8759:
            Occupancy.loc[hour,'tamb'] = Occupancy.loc[hour,'tintH_set'] - Bf*(Occupancy.loc[hour,'tintH_set']-Occupancy.loc[hour,'te'])
    
    # Calculation of losses only nonrecoverable losses are considered for the calculation, # those of the distribution in the basement for space heating and cooling system
    # This part applies the method described by SIA 2044
    if SystemH != 'No':
        if Occupancy['Qhs'].max()!=0:
            Occupancy['Qhs_d_ls'] = ((Occupancy['tsh']+Occupancy['trh'])/2-Occupancy['tamb'])*(Occupancy['Qhs']/Occupancy['Qhs'].max())*(Lv*Y[0]) 
        else:
            Occupancy['Qhs_d_ls'] = 0
    
    if SystemC != 'No':    
        if Occupancy['Qcs'].min()!=0:       
            Occupancy['Qcs_d_ls'] = ((Occupancy['tsc']+Occupancy['trc'])/2-Occupancy['tamb'])*(Occupancy['Qcs']/Occupancy['Qcs'].min())*(Lv*Y[0])
        else:
            Occupancy['Qcs_d_ls']=0
    
    # Calculation of lossesof the distribution and cirulation loop of the hotwater system in the basement.
    
    Occupancy['Qww_d_ls'] = (twws-Occupancy['tamb'])*Y[0]*(Lvww_c+Lvww_dis)*(Occupancy['Mww']*Af)/(12*60) #velocity of flow of 12 l/min
    
    # Physical approach, losses Inside the conditioned space
    hours = Occupancy.tamb.count()
    for hour in range(hours):
        if Seasonhours[0] < hour < Seasonhours[1]: # cooling season
            Occupancy.loc[hour,'tamb'] = Occupancy['tintC_set'].min()
        else:
            Occupancy.loc[hour,'tamb'] = Occupancy['tintH_set'].max()
    
    Occupancy['Qww_dh_ls'] = ((twws-Occupancy['tamb'])*Y[1]*(Lsww_c+Lsww_dis)*((Occupancy['Mww']*Af)/1000)+
                              (tws-Occupancy['tamb'])*Y[1]*(Lslww_dis)*((Occupancy['Mww']*Af)/1000))
    
    
        
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
    hf = 3*(nf-1) # standard height of every floor
    Lsww_c = 0.075*Ll*Lw*nf*nfpercent*hf*fforma
    Lsww_dis = 0.038*Ll*Lw*nf*nfpercent*hf*fforma
    Lslww_dis = (0.05*Ll*Lw*nf*nfpercent)*fforma
    
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
    
    Occupancy['Qww_dh_ls'] = ((twws-Occupancy['tamb'])*Y[1]*(Lsww_c+Lsww_dis)*((Occupancy['Mww']*Af)/1000)+
                              (tws-Occupancy['tamb'])*Y[1]*(Lslww_dis)*((Occupancy['Mww']*Af)/1000))
              
    return Occupancy.copy()

# <codecell>

#a factor taking into account that Ll and lw are measured from an aproximated rectangular surface
def Calc_form(Lw,Ll,footprint): 
    factor = footprint/(Lw*Ll)
    return factor

# <codecell>

def calc_Aux_hscs(nf,nfpercent,Lw,Ll,footprint,Year,Qhs0,tsh0,trh0,data,Qcs0,tsc0,trc0,SystemH,SystemC,twws,tw): 
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
    if SystemH != 'Air conditioning' or SystemH != 'No':
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
    if SystemH != 'Air conditioning' or SystemH != 'No':
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
    
    return data.copy()

# <markdowncell>

# 2.1. Sub-Function calculation of nominal temperatures of system

# <codecell>

def calc_em_t(SystemH,SystemC):
    # References: 70 supply 50 return radiatior system #several authors
    # Floor cooling/ceiling cooling 18 -22 /thermofloor.co.uk
    # Floor heating /ceiling heating EN 1264-3
    # Emission factors extracted from SIA 384/2,1984
    #Default values
    nh =0.3
    tsh0 = 70
    trh0 = 50
    tsc0 = 7
    trc0 = 12
    # Create tables with information of nominal temperatures
    h={'Type':['Ceiling heating', 'Radiator', 'Floor heating', 'Air conditioning'],'tsnominal':[35,70,35,60],
                'trnominal':[25,50,25,50],'EmissionFactor':[0.22,0.33,0.24,0.3]}
    Heating = pd.DataFrame(h)
    c ={'Type':['Ceiling cooling','Floor cooling', 'Air conditioning'],'tsnominal':[15,15,7],
                'trnominal':[20,20,12]}
    Cooling = pd.DataFrame(c)
    
    # Calculate the nominal temperatures and emission factors based on the type of system.
    # for heating systems
    rows = Heating.Type.count()
    for row in range(rows):
        if SystemH == Heating.loc[row,'Type']:
            tsh0 = Heating.loc[row,'tsnominal']
            trh0 = Heating.loc[row,'trnominal']
            nh = Heating.loc[row,'EmissionFactor']
    #for cooling sytems
    rows = Cooling.Type.count()
    for row in range(rows):
        if SystemC == Cooling.loc[row,'Type']:
            tsc0 = Cooling.loc[row,'tsnominal']
            trc0 = Cooling.loc[row,'trnominal']
    return tsh0,trh0,tsc0,trc0,nh

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
        if DatabaseModelMerge.loc[r,'Hs_x']>0:
            DatabaseModelMerge.loc[r,'Hs_y'] = DatabaseModelMerge.loc[r,'Hs_x']
            
    DatabaseModelMerge['Qhsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhsf_kWhm2/1000
    DatabaseModelMerge['Qhpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhpf_kWhm2/1000
    DatabaseModelMerge['Qwwf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qwwf_kWhm2/1000
    DatabaseModelMerge['Qcsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcsf_kWhm2/1000
    DatabaseModelMerge['Qcdataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcdataf_kWhm2/1000
    DatabaseModelMerge['Qcicef'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcicef_kWhm2/1000
    DatabaseModelMerge['Qcpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcpf_kWhm2/1000
    DatabaseModelMerge['Ealf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Ealf_kWhm2/1000
    DatabaseModelMerge['Edataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Edataf_kWhm2/1000 
    DatabaseModelMerge['Epf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Es* DatabaseModelMerge.Epf_kWhm2/1000
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

