# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from __future__ import division
import pandas as pd
import datetime
import sys
if r'C:\Console\EDM' not in sys.path: sys.path.append(r'C:\Console\EDM')
import EDMFunctions as EDM
import os
from math import *
import arcpy
import sys
import datetime
import jdcal
import numpy as np
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")

# <headingcell level=3>

# Variables

# <codecell>

Scenario = 'SQ'; Zone_of_study = 3
Zone_calc = 3

# <codecell>

type_SCpanel = 2 # Flatplate collector

# <codecell>

database = r'c:\ArcGIS\EDM.gdb'  #ArcGIS database
database2 = r'c:\ArcGIS\ERM.gdb'  #ArcGIS database
CQ = database+'\\'+Scenario+'\\'+Scenario+'Zone_'+str(Zone_calc)
context = database+'\\'+Scenario+'\\'+Scenario+'AREA'
DEM = database+'\\DEM_Clip' # DEM of analysis resampled to grid of 1m for more accurracy

# <codecell>

WeatherData = pd.ExcelFile('C:\ArcGIS\EDMdata\Weatherdata\Temp_Design.xls') # Location of temperature data
T_G_hour = pd.ExcelFile.parse(WeatherData, 'Values_hour') # temperature and radiation table
T_G_day = pd.ExcelFile.parse(WeatherData, 'Values_day') # temperature and radiation table

# <codecell>

locationtemp1 = r'c:\ArcGIS\temp'
locationtemp2 = r'c:\ArcGIS\EDM.gdb\temp'

# <codecell>

if Zone_calc != Zone_of_study:
    CQ = database+'\\'+'Surroundings'+'\\'+'Zone_'+str(Zone_calc)
else:
    CQ = database+'\\'+Scenario+'\\'+Scenario+'Zone_'+str(Zone_calc)

# <codecell>

latitude = 47.1628017306431      #longitude of the city
longitude = 8.31                 #latitude of the city
timezone = 1                     #Timezone of the city
Yearsimul = 2010

# <codecell>

reload(EDM)
T_G_day['sunrise'] = 0
for day in range(1,366): # Calculated according to NOAA website
    # Calculate Date and Julian day
    Date = datetime.datetime(Yearsimul, 1, 1) + datetime.timedelta(day-1)
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
    Solar_noon  = (720-4*longitude-EOT+timezone*60)/1440
    T_G_day.loc[day-1,'sunrise'] = (Solar_noon-HA_sunrise*4/1440)*24

# <headingcell level=2>

# Process

# <headingcell level=4>

# 1. Simplify buildings and create raster model for radiation analysis

# <codecell>

# Define local variables  - Outputs
Simple_CQ = locationtemp2+'\\'+'Simple_CQ'
Simple_context = locationtemp2+'\\'+'Simple_context'
DEMfinal = locationtemp1+'\\'+'DEM_All2'

# <codecell>

# Simplify buildings of the cityquarter and of the context
arcpy.SimplifyBuilding_cartography(CQ,Simple_CQ,simplification_tolerance=8, minimum_area=None)

# <codecell>

arcpy.SimplifyBuilding_cartography(context,Simple_context,simplification_tolerance=8, minimum_area=None)

# <codecell>

# Burn buildings of the context into the DEM model
EDM.Burn(Simple_context,DEM,DEMfinal,locationtemp1,locationtemp2,database)

# <headingcell level=4>

# 2. Create observers on roof tops for the analysis

# <codecell>

min_production = 0.75 # points are selected with at least a minimum production of this % from the maximum in the area.
DEM_zone_loc = locationtemp1+"\\"+"DEM_zone"+str(Zone_calc) #DEM raster of rooftops in the zone
observers_all = database2+'\\'+Scenario+'\\'+Scenario+'rad' #Observers before getting to reduce potential
Aspect_raster = locationtemp1+"\\"+"aspectZone"
Slope_raster = locationtemp1+"\\"+"slopeZoner"

# <codecell>

arcpy.Clip_management(DEMfinal, "#", DEM_zone_loc ,Simple_CQ, "0","ClippingGeometry","MAINTAIN_EXTENT")
arcpy.RasterToPoint_conversion(DEM_zone_loc,observers_all,"Value")

# <codecell>

# calculate properties of observers (slope, angle)
arcpy.gp.Aspect_sa(DEM_zone_loc,Aspect_raster)
arcpy.gp.Slope_sa(DEM_zone_loc,Slope_raster,"DEGREE","1")
arcpy.gp.ExtractMultiValuesToPoints_sa(observers_all,Aspect_raster,"NONE")
arcpy.gp.ExtractMultiValuesToPoints_sa(observers_all,Slope_raster,"NONE")

# <codecell>

# if it is the case it would be needed to do some postprocessing and check that the slope and aspect of the raster agree with reality.

# <headingcell level=3>

# 2. Calculate hourly values in each observer for the horizontal plane

# <codecell>

# local variables
hourly_horizontal_rad = 'C:\ArcGIS\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Rad_hor_roofpoint.csv'
Pv_gen = 'C:\ArcGIS\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Pv.csv'

# <codecell>

from IPython.parallel import Client # Create Parallel modules nd star the 8 cores
client = Client()
lview = client.load_balanced_view()
lview.block = True
dview = client[:]
dview.push({'Scenario':Scenario, 'T_G_day':T_G_day, 'latitude':latitude, 'locationtemp1':locationtemp1,
            'longitude':longitude, 'timezone': timezone,'DEMfinal':DEMfinal,'observers_all':observers_all,
            'type_panel':type_panel, 'observers_data':observers_data, 'T_G_hour':T_G_hour, 'misc_losses':misc_losses,
            'properties':properties})
%px import sys
%px if r'C:\Console\EDM' not in sys.path: sys.path.append(r'C:\Console\EDM')
%px import EDMFunctions as EDM

# <codecell>

@lview.parallel()
def radiation(day):
    aspect_slope = "FLAT_SURFACE"
    heightoffset = 0
    return EDM.CalcRadiation(day, Scenario, DEMfinal, observers_all, T_G_day, latitude, locationtemp1, aspect_slope, heightoffset)

# <codecell>

radiation.map(range(1,366))

# <codecell>

@lview.parallel()
#run the transformation of files in parallel - appending all and adding non-sunshine hours
def radiationday(day):
    rad =   EDM.calc_radiationday(day, Scenario, T_G_day, locationtemp1)
    #pv =    EDM.pv_generation(properties, rad, observers_data, T_G_hour, latitude, misc_losses, day)
    return rad#,pv

# <codecell>

radiations = radiationday.map(range(1,366))

# <codecell>

Radiationyear = radiations[0]
for r in radiations[1:]:
    Radiationyear = Radiationyear.merge(r, on='ID')
Radiationyear.fillna(value=0,inplace=True)
Radiationyear.to_csv(hourly_horizontal_rad,Index=False)
print 'Complete!'

# <headingcell level=4>

# # apply filters to hourly and total values

# <codecell>

# variables
grid_side = 2 # in a rectangular grid of points, one side of the square.
module_lenght = 0.99 #m
worst_hour = 8744 # first hour of sun on the solar solstice
diffuseProp = T_G_day['diff'].mean()
transmittivity = T_G_day['ttr'].mean()
worst_sh = T_G_hour.loc[worst_hour,'Sh']
worst_Az = T_G_hour.loc[worst_hour,'Az']
angle_north = 122.5

# <codecell>

# DF WITH HOURLY SOLAR RADAITION
hourly_data = pd.read_csv(hourly_horizontal_rad)

# <codecell>

# YEARLY SOLAR RADIATION AND APPEND TO GIS OBSERVERS
total = hourly_data.drop({'ID','Unnamed: 0'}, axis =1).sum(axis=1)
total_df = pd.DataFrame(total,columns=["GB"])
total_df['ID']= hourly_data['ID']

# <codecell>

Max_Isol = total_df.GB.max()
Min_Isol = Max_Isol*min_production #80% of the local average maximum in the area

# <codecell>

outpath = "observers.dbf"
df2dbf(total_df, locationtemp1+'\\'+outpath)
arcpy.JoinField_management(observers_all, "pointid", locationtemp1+'\\'+outpath, "ID")

# <codecell>

#CREATE DUPLICATE OF OBSERVERS FOR CALCULATION PURPOSES
observers_data = database2+'\\'+Scenario+'\\'+Scenario+'radClean'
arcpy.FeatureClassToFeatureClass_conversion(observers_all, database2+'\\'+Scenario, Scenario+'radClean')

# <codecell>

#APPLY FLITER AND CALCULATE OPTIMAL TILT, SPACING AND ORIENTATION:
# remove points with radiation less than 80% the maximum in the obesrvers_all #remove points towards north #calculate tilted area also
#create categories of tilted areas.
reload(EDM)
EDM.optimal_angle_and_tilt(observers_data,latitude,worst_sh, worst_Az, transmittivity, diffuseProp, grid_side, module_lenght, angle_north, Min_Isol, Max_Isol)

# <headingcell level=4>

# Calculate groups append and import data

# <codecell>

#IMPORT OBSERVERS WITH FILTER AS DF
outpath = "observers.dbf"
arcpy.TableToTable_conversion(observers_data,locationtemp1,outpath)
observers_fin = dbf2df(locationtemp1+'\\'+outpath)

# <codecell>

#calculate number of optima groups as number of optimal combiantions.
groups_ob = observers_fin.groupby(['CATB','CATGB','CATteta_z'])
prop_observers = groups_ob.mean().reset_index()
prop_observers = pd.DataFrame(prop_observers)
Number_groups = groups_ob.size().count()

# <codecell>

#calculate groups in arcgis
observers_groups = database2+'\\'+Scenario+'\\'+Scenario+'radGR'
#these guys have to be changed in the partition.py script of arcpy #maxNumGroups = 40#maxNumVars = 40 #aSpatialOptimizeIters = 10 #aSpatialIters = 300
arcpy.GroupingAnalysis_stats(observers_data,"pointid",observers_groups,str(Number_groups),"CATB;CATGB;CATteta_z","NO_SPATIAL_CONSTRAINT","EUCLIDEAN","#","#","FIND_SEED_LOCATIONS","#","#","DO_NOT_EVALUATE")

# <codecell>

#overwrite observers with gorup information
outpath = "observergroups.dbf"
arcpy.TableToTable_conversion(observers_groups,locationtemp1,outpath)
observers_groups = dbf2df(locationtemp1+'\\'+outpath)
observers_fin['group'] = observers_groups['SS_GROUP']

# <headingcell level=4>

# PV POTENTIAL

# <codecell>

# APPLY HOURLY FILTER: minimum solar radiation of  50 W/m2
Clean_hourly = hourly_data.drop({'ID','Unnamed: 0'}, axis =1)
Clean_hourly[Clean_hourly[:]<= 50]= 0
#add again the 'ID' field.
Clean_hourly['ID'] = hourly_data['ID']

# <codecell>

#CONSERVE only matching points in Clen hourly data
clean_hourly2 = Clean_hourly.merge(observers_fin, on='ID')

# <codecell>

groups = clean_hourly2.groupby(['group'])
Grouped_hourlyrad = groups.mean().reset_index() # the mean is only used to calculate the cell temperature
Hourly_radgrouped = pd.DataFrame(Grouped_hourlyrad)
Number_pointsgroup = groups.size().reset_index()
Hourly_radgrouped['num_points'] = Number_pointsgroup[0]

# <codecell>

reload(EDM)
results = EDM.pv_generation(type_PVpanel, Hourly_radgrouped, T_G_hour, latitude, misc_losses)

# <codecell>

PotentialPV = results.drop({'ID','GB','grid_code','pointid','array_s','area_netpv','aspectZone',
                            'slopeZoner','group','CATB','CATGB','CATteta_z'},axis=1)
PotentialPV = PotentialPV.sum(axis=0)/1000
PotentialPV.to_csv(Pv_gen)

# <codecell>

%matplotlib inline
import matplotlib.pyplot as plt
plt.figure(); plt.plot(PotentialPV); plt.legend(('Pv'),loc='best')

# <headingcell level=4>

# SC POTENTIAL

# <codecell>

# take out the unnamed
Clean_hourly = hourly_data.drop({'Unnamed: 0'}, axis =1)

# <codecell>

#CONSERVE only matching points in Clen hourly data
clean_hourly2 = Clean_hourly.merge(observers_fin, on='ID')

# <codecell>

#CONSERVE only matching points in Clen hourly data
groups = clean_hourly2.groupby(['CATB','CATGB','CATteta_z'])
Grouped_hourlyrad = groups.mean().reset_index() # the mean is only used to calculate the cell temperature
Hourly_radgrouped = pd.DataFrame(Grouped_hourlyrad)

# <codecell>

group_radiation = Hourly_radgrouped.drop({'ID','GB','grid_code','pointid','array_s','area_netpv','aspectZone',
                            'slopeZoner','CATB','CATGB','CATteta_z'},axis=1).transpose().reindex(axis = 1) #vector with radiation points of group
group_radiation.index = range(8760) #reset index

# <codecell>

Number_pointsgroup = groups.size().reset_index() 
number_points = Number_pointsgroup[0]   #vector with number of points per group

# <codecell>

reload(EDM)
result = EDM.SC_generation(1, group_radiation, prop_observers, number_points, T_G_hour, latitude)

# <codecell>

import matplotlib.pyplot as plt
#plt.figure(); result[0]['qout'][4010:4030].plot(subplots=False, figsize=(6, 3)); plt.figure()
#plt.figure(); result[1]['Tout'][4010:4030].plot(subplots=False, figsize=(6, 3))
plt.figure(); result[2]['qout'][4010:4030].plot(subplots=False, figsize=(6, 3))
plt.figure(); result[2]['Tout'][4010:4030].plot(subplots=False, figsize=(6, 3))
plt.figure(); result[4]['qout'][4000:8030].plot(subplots=False, figsize=(6, 3))
plt.figure(); result[4]['mopt'][4000:8030].plot(subplots=False, figsize=(6, 3))
plt.figure(); result[4]['Eaux'][4000:8030].plot(subplots=False, figsize=(6, 3))

# <codecell>

result[0]['qout'][result[0]['qout']<0]= 0
result[1]['qout'][result[1]['qout']<0]= 0
result[2]['qout'][result[2]['qout']<0]= 0
result[3]['qout'][result[3]['qout']<0]= 0
result[4]['qout'][result[4]['qout']<0]= 0

# <codecell>

result[1]['qout'].sum(), result[2]['qout'].sum(),result[3]['qout'].sum(),result[4]['qout'].sum()

# <codecell>

result[1]['Eaux'].sum(), result[2]['Eaux'].sum(),result[3]['Eaux'].sum(),result[4]['Eaux'].sum()

# <codecell>

result[4]['mopt']

# <codecell>

resultee = np.empty([2,1])
balances = [result[1].qout,result[2]['qout']]

# <codecell>

balances2 = [balances[0][0],balances[1][0]]
balances2
maxenergy = np.max(balances2)
ix_maxenergy = np.where(balances2==maxenergy)
ix_maxenergy[0][0]

# <codecell>

maxenergy

# <codecell>

result[4]['losses4'] = result[4]['qout'] - result[4]['mopt']*/1044/0.8
result[4]['losses3'] = result[3]['qout'] - 1044/0.8
result[4]['losses2'] = result[2]['qout'] - 1044/0.8
result[4]['losses1'] = result[1]['qout'] - 1044/0.8
result[4]['losses4'].sum(), result[4]['losses3'].sum(), result[4]['losses2'].sum(), result[4]['losses1'].sum() 

