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
import re
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
% matplotlib inline

# <headingcell level=3>

# Variables

# <codecell>

Scenario = 'SQ'; Zone_of_study =1
Zone_calc = 1

# <codecell>

type_PVpanel = 1 # monocrystalline
type_SCpanel = 1 # Flatplate collector
type_PVTpanel = 1 # Flatplate collector
misc_losses = 0.10 # losses for a good system due to cabling, regulator and inverters

# <codecell>

database = r'c:\Zernez\EDM.gdb'  #ArcGIS database
database2 = r'c:\Zernez\ERM.gdb'  #ArcGIS database
CQ = database+'\\'+Scenario+'\\'+Scenario+'Zone_'+str(Zone_calc)
context = database+'\\'+Scenario+'\\'+Scenario+'AREA'
DEM = database+'\\DEM_Clip' # DEM of analysis resampled to grid of 1m for more accurracy

# <codecell>

WeatherData = pd.ExcelFile('C:\Zernez\EDMdata\Weatherdata\Temp_Design.xls') # Location of temperature data
T_G_hour = pd.ExcelFile.parse(WeatherData, 'Values_hour') # temperature and radiation table
T_G_day = pd.ExcelFile.parse(WeatherData, 'Values_day') # temperature and radiation table

# <codecell>

locationtemp1 = r'c:\Zernez\temp'
locationtemp2 = r'c:\Zernez\EDM.gdb\temp'

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

T_G_day['sunrise'] = 0
T_G_day=  EDM.calc_sunrise(T_G_day,Yearsimul,timezone,longitude,latitude)

# <headingcell level=2>

# Process

# <codecell>

hourly_horizontal_rad = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Radiation_rooftop'+'\\'+'Rad_hor_roofpoint.csv'
observers_all = database2+'\\'+Scenario+'\\'+Scenario+'rad' #Observers gotten from resource potential

# <headingcell level=4>

# # apply filters to hourly and total values

# <codecell>

# CONDITIONS FOR THE ANALYSIS
min_production = 0.75 # points are selected with at least a minimum production of this % from the maximum in the area.
grid_side = 2 # in a rectangular grid of points, one side of the square. this cannot be changed if the solra potential was made with this.
worst_hour = 8744 # first hour of sun on the solar solstice
angle_north = 122.5
diffuseProp = T_G_day['diff'].mean()
transmittivity = T_G_day['ttr'].mean()
worst_sh = T_G_hour.loc[worst_hour,'Sh']
worst_Az = T_G_hour.loc[worst_hour,'Az']

# <codecell>

# DF WITH HOURLY SOLAR RADAITION
hourly_data = pd.read_csv(hourly_horizontal_rad)

# <codecell>

# YEARLY SOLAR RADIATION 
total = hourly_data.drop({'ID','Unnamed: 0'}, axis = 1).sum(axis=1)
total_df = pd.DataFrame(total,columns=["GB"])
total_df['ID']= hourly_data['ID']
Max_Isol = total_df.GB.max()
Min_Isol = Max_Isol*min_production #80% of the local average maximum in the area
total = None # erase from memory

# <codecell>

#AND APPEND TO GIS OBSERVERS
outpath = "observers.dbf"
df2dbf(total_df, locationtemp1+'\\'+outpath)
arcpy.JoinField_management(observers_all, "pointid", locationtemp1+'\\'+outpath, "ID")

# <codecell>

# Calculate the heights of all buildings
outpath = "buildings.dbf"
arcpy.TableToTable_conversion(CQ,locationtemp1,outpath)
buildings_data = dbf2df(locationtemp1+'\\'+outpath)
height = buildings_data.height.sum()

# <headingcell level=4>

# PV POTENTIAL

# <codecell>

#CREATE DUPLICATE OF OBSERVERS FOR CALCULATION PURPOSES
observers_data = database2+'\\'+Scenario+'\\'+Scenario+'radClean'
arcpy.FeatureClassToFeatureClass_conversion(observers_all, database2+'\\'+Scenario, Scenario+'radClean')

# <codecell>

reload(EDM)
#APPLY FLITER AND CALCULATE OPTIMAL TILT, SPACING AND ORIENTATION:
# remove points with radiation less than 80% the maximum in the obesrvers_all #remove points towards north #calculate tilted area also
#create categories of tilted areas. categorize also potentials.
module_lenght = 1 #m # 1 for PV and 1 for solar collectors
EDM.optimal_angle_and_tilt(observers_data,latitude,worst_sh, worst_Az, transmittivity, diffuseProp, grid_side, module_lenght, angle_north, Min_Isol, Max_Isol)
#IMPORT OBSERVERS WITH FILTER AS DF
outpath = "observers.dbf"
arcpy.TableToTable_conversion(observers_data,locationtemp1,outpath)
observers_fin = dbf2df(locationtemp1+'\\'+outpath)

# <codecell>

# APPLY HOURLY FILTER: minimum solar radiation of  50 W/m2
Clean_hourly = hourly_data.drop({'ID','Unnamed: 0'}, axis =1)
Clean_hourly[Clean_hourly[:]<= 50]= 0
#add again the 'ID' field
Clean_hourly['ID'] = hourly_data['ID']

# <codecell>

#CONSERVE only matching points in Clean hourly data
Clean_hourly = Clean_hourly.merge(observers_fin, on='ID')

# <codecell>

#calculate number of optima groups as number of optimal combiantions.
groups_ob = Clean_hourly.groupby(['CATB','CATGB','CATteta_z'])
hourlydata_groups = groups_ob.mean().reset_index()
hourlydata_groups = pd.DataFrame(hourlydata_groups)
Number_pointsgroup = groups_ob.size().reset_index() 
number_points = Number_pointsgroup[0]   #vector with number of points per group
#Clean_hourly = None #Clear from memory

# <codecell>

groups_ob = observers_fin.groupby(['CATB','CATGB','CATteta_z'])
prop_observers = groups_ob.mean().reset_index()
prop_observers = pd.DataFrame(prop_observers)
Number_groups = groups_ob.size().count()
observers_fin = None #Clear from memory

# <codecell>

hourlydata_groups = hourlydata_groups.drop({'ID','GB','grid_code','pointid','array_s','area_netpv','aspect',
                            'slope','CATB','CATGB','CATteta_z'},axis=1).transpose().reindex(axis = 1) #vector with radiation points of group
hourlydata_groups['newindex'] = hourlydata_groups.index
hourlydata_groups['newindex'] = hourlydata_groups.newindex.apply(lambda x: re.findall('\d+',x))
hourlydata_groups.index = range(8760)
for hour in range(8760):
    hourlydata_groups.loc[hour,'newindex'] = int(hourlydata_groups.loc[hour,'newindex'][0])
    
hourlydata_groups.set_index('newindex', inplace=True)
hourlydata_groups.sort_index(inplace =True)
hourlydata_groups.index = range(8760)

# <codecell>

results, Final = EDM.Calc_pv_generation(type_PVpanel, hourlydata_groups, Number_groups, number_points, prop_observers, T_G_hour, latitude, misc_losses)
Pv_gen = 'C:\ArcGIS\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'PV.csv'
Final.to_csv(Pv_gen, index = False,float_format='%.3f')

# <headingcell level=4>

# SC POTENTIAL

# <codecell>

#CREATE DUPLICATE OF OBSERVERS FOR CALCULATION PURPOSES
observers_data = database2+'\\'+Scenario+'\\'+Scenario+'radClean'
arcpy.FeatureClassToFeatureClass_conversion(observers_all, database2+'\\'+Scenario, Scenario+'radClean')

# <codecell>

#APPLY FLITER AND CALCULATE OPTIMAL TILT, SPACING AND ORIENTATION:
# remove points with radiation less than 80% the maximum in the obesrvers_all #remove points towards north #calculate tilted area also
#create categories of tilted areas. categorize also potentials.
module_lenght = 2 #m # 1 for PV and 1 for solar collectors
EDM.optimal_angle_and_tilt(observers_data,latitude,worst_sh, worst_Az, transmittivity, diffuseProp, grid_side, module_lenght, angle_north, Min_Isol, Max_Isol)
#IMPORT OBSERVERS WITH FILTER AS DF
outpath = "observers.dbf"
arcpy.TableToTable_conversion(observers_data,locationtemp1,outpath)
observers_fin = dbf2df(locationtemp1+'\\'+outpath)

# <codecell>

# take out the unnamed
Clean_hourly = hourly_data.drop({'Unnamed: 0'}, axis =1)
#add again the 'ID' field
Clean_hourly['ID'] = hourly_data['ID']

# <codecell>

#CONSERVE only matching points in Clen hourly data
Clean_hourly = Clean_hourly.merge(observers_fin, on='ID')

# <codecell>

#calculate number of optima groups as number of optimal combiantions.
groups_ob = Clean_hourly.groupby(['CATB','CATGB','CATteta_z'])
hourlydata_groups = groups_ob.mean().reset_index()
hourlydata_groups = pd.DataFrame(hourlydata_groups)
Number_pointsgroup = groups_ob.size().reset_index() 
number_points = Number_pointsgroup[0]   #vector with number of points per group
#Clean_hourly = None #Clear from memory

# <codecell>

groups_ob = observers_fin.groupby(['CATB','CATGB','CATteta_z'])
prop_observers = groups_ob.mean().reset_index()
prop_observers = pd.DataFrame(prop_observers)
Number_groups = groups_ob.size().count()
observers_fin = None #Clear from memory

# <codecell>

hourlydata_groups = hourlydata_groups.drop({'ID','GB','grid_code','pointid','array_s','area_netpv','aspect',
                            'slope','CATB','CATGB','CATteta_z'},axis=1).transpose().reindex(axis = 1) #vector with radiation points of group
hourlydata_groups['newindex'] = hourlydata_groups.index
hourlydata_groups['newindex'] = hourlydata_groups.newindex.apply(lambda x: re.findall('\d+',x))
hourlydata_groups.index = range(8760)
for hour in range(8760):
    hourlydata_groups.loc[hour,'newindex'] = int(hourlydata_groups.loc[hour,'newindex'][0])
    
hourlydata_groups.set_index('newindex', inplace=True)
hourlydata_groups.sort_index(inplace =True)
hourlydata_groups.index = range(8760)

# <codecell>

Tin = 75
result, Final = EDM.SC_generation(type_SCpanel, hourlydata_groups, prop_observers, number_points, T_G_hour, latitude, Tin, height)

# <codecell>

SC_gen = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'SC_'+str(Tin)+'.csv'
Final.to_csv(SC_gen, index=True, float_format='%.3f')

# <headingcell level=3>

# PVT potential

# <codecell>

#CREATE DUPLICATE OF OBSERVERS FOR CALCULATION PURPOSES
observers_data = database2+'\\'+Scenario+'\\'+Scenario+'radClean'
arcpy.FeatureClassToFeatureClass_conversion(observers_all, database2+'\\'+Scenario, Scenario+'radClean')

# <codecell>

#APPLY FLITER AND CALCULATE OPTIMAL TILT, SPACING AND ORIENTATION:
# remove points with radiation less than 80% the maximum in the obesrvers_all #remove points towards north #calculate tilted area also
#create categories of tilted areas. categorize also potentials.
module_lenght = 2 #m # 1 for PV and 2 for solar collectors
EDM.optimal_angle_and_tilt(observers_data,latitude,worst_sh, worst_Az, transmittivity, diffuseProp, grid_side, module_lenght, angle_north, Min_Isol, Max_Isol)
#IMPORT OBSERVERS WITH FILTER AS DF
outpath = "observers.dbf"
arcpy.TableToTable_conversion(observers_data,locationtemp1,outpath)
observers_fin = dbf2df(locationtemp1+'\\'+outpath)

# <codecell>

# take out the unnamed
Clean_hourly = hourly_data.drop({'Unnamed: 0'}, axis =1)

# <codecell>

#CONSERVE only matching points in Clen hourly data
Clean_hourly = Clean_hourly.merge(observers_fin, on='ID')

# <codecell>

#calculate number of optima groups as number of optimal combiantions.
groups_ob = Clean_hourly.groupby(['CATB','CATGB','CATteta_z'])
hourlydata_groups = groups_ob.mean().reset_index()
hourlydata_groups = pd.DataFrame(hourlydata_groups)
Number_pointsgroup = groups_ob.size().reset_index() 
number_points = Number_pointsgroup[0]   #vector with number of points per group
#Clean_hourly = None #Clear from memory

# <codecell>

groups_ob = observers_fin.groupby(['CATB','CATGB','CATteta_z'])
prop_observers = groups_ob.mean().reset_index()
prop_observers = pd.DataFrame(prop_observers)
Number_groups = groups_ob.size().count()
observers_fin = None #Clear from memory

# <codecell>

hourlydata_groups = hourlydata_groups.drop({'ID','GB','grid_code','pointid','array_s','area_netpv','aspect',
                            'slope','CATB','CATGB','CATteta_z'},axis=1).transpose().reindex(axis = 1) #vector with radiation points of group
hourlydata_groups['newindex'] = hourlydata_groups.index
hourlydata_groups['newindex'] = hourlydata_groups.newindex.apply(lambda x: re.findall('\d+',x))
hourlydata_groups.index = range(8760)
for hour in range(8760):
    hourlydata_groups.loc[hour,'newindex'] = int(hourlydata_groups.loc[hour,'newindex'][0])
    
hourlydata_groups.set_index('newindex', inplace=True)
hourlydata_groups.sort_index(inplace =True)
hourlydata_groups.index = range(8760)

# <codecell>

reload(EDM)
Tin = 35
result, Final = EDM.calc_PVT_generation(type_PVpanel, hourlydata_groups,Number_groups, number_points, prop_observers, T_G_hour, latitude, misc_losses,
                                        type_SCpanel, Tin, height)

# <codecell>

PVT_gen = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'PVT_35.csv'
Final.to_csv(PVT_gen, index=True, float_format='%.3f')

# <headingcell level=3>

# PLOTTING SOLAR ISOLATION

# <codecell>

%matplotlib inline
import matplotlib.pyplot as plt

# <codecell>

isolation = hourlydata_groups.rename(columns={0:'Group 1',1:'Group 3',2:'Group 2'})

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
isolation.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
isolation[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
isolation[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
isolation[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('Solar isolation (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <headingcell level=3>

# PLOTTING PV POTENTIAL

# <codecell>

PV_production = pd.DataFrame({'Group 1':results[0],'Group 2':results[2],'Group 3':results[1], 'Total':(results[0]+results[1]+results[2])})
PV_production_perarea = pd.DataFrame({'Group 1':results_perarea[0]*1000,'Group 2':results_perarea[2]*1000,'Group 3':results_perarea[1]*1000})

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
PV_production_perarea.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
PV_production_perarea[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
PV_production_perarea[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
PV_production_perarea[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV specific potential (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
PV_production.plot(ax = ax1); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('PV potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
PV_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('PV potential (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
PV_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('PV potential (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
PV_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV potential (kW)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <headingcell level=3>

# SC POLOTTING POTENTIAL

# <codecell>

%matplotlib inline
import matplotlib.pyplot as plt
Area_group1 = prop_observers.loc[0,'area_netpv']*number_points[0]
Area_group2 = prop_observers.loc[1,'area_netpv']*number_points[1]
Area_group3 = prop_observers.loc[2,'area_netpv']*number_points[2]

# <codecell>

SC_production = pd.DataFrame({'Group 1':result[0][1]/Area_group1*1000,'Group 2':result[2][1]/Area_group3*1000,'Group 3':result[1][1]/Area_group2*1000})

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
SC_production.plot(ax = ax1, ylim=([0,600])); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
SC_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True, ylim=([0,600])); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
SC_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True, ylim=([0,200])); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
SC_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('SC specific potential (W/m2)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <codecell>

SC_production = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
SC_production.plot(ax = ax1, ylim=([0,25000])); ax1.set_title('Year',fontsize=25); ax1.set_ylabel('SC potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
SC_production[4000:4200].plot(ax = ax2, legend =False, antialiased=True, ylim=([0,25000])); ax2.set_title('Summer',fontsize=25); ax2.set_ylabel('SC potential (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
SC_production[1600:1800].plot(ax = ax3, legend =False, antialiased=True, ylim=([0,8000])); ax3.set_title('Intermediate season',fontsize=25); ax3.set_ylabel('SC potential (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
SC_production[8300:8500].plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Winter',fontsize=25); ax4.set_ylabel('PV potential (kW)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <codecell>

Toutvector = np.nan_to_num(np.divide((result[0][1]+result[2][1]+result[1][1]),(result[0][5]+result[2][5]+result[1][5])) + Tin)
SC_production = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})
SC_losses = pd.DataFrame({'Group 1':result[0][0],'Group 2':result[2][0],'Group 3':result[1][0], 'Total':(result[0][0]+result[2][0]+result[1][0])})
SC_aux = pd.DataFrame({'Group 1':result[0][2],'Group 2':result[2][2],'Group 3':result[1][2], 'Total':(result[0][2]+result[2][2]+result[1][2])})
SC_Tout = pd.DataFrame({'Group 1':result[0][3],'Group 2':result[2][3],'Group 3':result[2][3], 'Total':Toutvector})
SC_mcp = pd.DataFrame({'Group 1':result[0][5],'Group 2':result[2][5],'Group 3':result[1][5], 'Total':(result[0][5]+result[2][5]+result[1][5])})

# <codecell>

fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize=(32, 16), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]
SC_production.plot(ax = ax1, ylim=([0,20000])); ax1.set_title('Thermal Output',fontsize=25); ax1.set_ylabel('SC potential (kW)',fontsize=20);ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
SC_losses.plot(ax = ax2, legend =False, antialiased=True, ylim=([0,1000])); ax2.set_title('Thermal Losses',fontsize=25); ax2.set_ylabel('losses (kW)',fontsize=20);ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
SC_aux.plot(ax = ax3, legend =False, antialiased=True, ylim=([0,200])); ax3.set_title('Auxiliary electricity',fontsize=25); ax3.set_ylabel('Eaux (kW)',fontsize=20);ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
SC_Tout.plot(ax = ax4, legend =False, antialiased=True); ax4.set_title('Return temperature',fontsize=25); ax4.set_ylabel('Tout (C)',fontsize=20);ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)

# <headingcell level=3>

# PVT PLOTTING POTENTIAL

# <codecell>

%matplotlib inline
import matplotlib.pyplot as plt

# <codecell>

Toutvector = np.nan_to_num(np.divide((result[0][1]+result[2][1]+result[1][1]),(result[0][5]+result[2][5]+result[1][5])) + Tin)
PVT_thermal_gen = pd.DataFrame({'Group 1':result[0][1],'Group 2':result[2][1],'Group 3':result[1][1], 'Total':(result[0][1]+result[2][1]+result[1][1])})
PVT_losses = pd.DataFrame({'Group 1':result[0][0],'Group 2':result[2][0],'Group 3':result[1][0], 'Total':(result[0][0]+result[2][0]+result[1][0])})
PVT_aux = pd.DataFrame({'Group 1':result[0][2],'Group 2':result[2][2],'Group 3':result[1][2], 'Total':(result[0][2]+result[2][2]+result[1][2])})
PVT_Tout = pd.DataFrame({'Group 1':result[0][3],'Group 2':result[2][3],'Group 3':result[2][3], 'Total':Toutvector})
PVT_mcp = pd.DataFrame({'Group 1':result[0][5],'Group 2':result[2][5],'Group 3':result[1][5], 'Total':(result[0][5]+result[2][5]+result[1][5])})
PVT_electrical_gen = pd.DataFrame({'Group 1':result[0][6],'Group 2':result[2][6],'Group 3':result[1][6], 'Total':(result[0][6]+result[2][6]+result[1][6])})

# <codecell>

fig, axes = plt.subplots(nrows = 3, ncols = 2, figsize=(32, 24), dpi=4200)
ax1 = axes[0,0]; ax2 = axes[0,1]; ax3 = axes[1,0]; ax4 = axes[1,1]; ax5 = axes[2,0]; ax6 = axes[2,1]
PVT_thermal_gen.plot(ax = ax1, ylim=([0,30000])); ax1.set_title('Thermal Output',fontsize=25); ax1.set_ylabel(r'$\Phi_{PVT,th}$'+'  (kW)',fontsize = 30 );ax1.set_xlabel('Hour of the year',fontsize=20);ax1.tick_params(axis='x', labelsize=20);ax1.tick_params(axis='y', labelsize=20);ax1.legend(fontsize=20)
PVT_losses.plot(ax = ax2, legend =False, antialiased=True, ylim=([0,400])); ax2.set_title('Distribution thermal Losses',fontsize=25); ax2.set_ylabel(r'$\Phi_{PVT,dis,l}$'+'  (kW)',fontsize = 30 );ax2.set_xlabel('Hour of the year',fontsize=20);ax2.tick_params(axis='x', labelsize=20);ax2.tick_params(axis='y', labelsize=20)
PVT_electrical_gen.plot(ax = ax3, legend =False, antialiased=True); ax3.set_title('Electrical Output',fontsize=25); ax3.set_ylabel(r'$\Phi_{PVT,e}$'+'  (kW)',fontsize = 30 );ax3.set_xlabel('Hour of the year',fontsize=20);ax3.tick_params(axis='x', labelsize=20);ax3.tick_params(axis='y', labelsize=20)
PVT_aux.plot(ax = ax4, legend =False, antialiased=True, ylim=([0,200])); ax4.set_title('Auxiliary electricity',fontsize=25); ax4.set_ylabel(r'$\Phi_{PVT,aux}$'+'  (kW)',fontsize = 30 );ax4.set_xlabel('Hour of the year',fontsize=20);ax4.tick_params(axis='x', labelsize=20);ax4.tick_params(axis='y', labelsize=20)
PVT_mcp.plot(ax = ax5, legend =False, antialiased=True); ax5.set_title('Capacity mass flow rate',fontsize=25); ax5.set_ylabel(r'$\.{mCp}$'+'  (kW/C)',fontsize = 30 );ax5.set_xlabel('Hour of the year',fontsize=20);ax5.tick_params(axis='x', labelsize=20);ax5.tick_params(axis='y', labelsize=20)
PVT_Tout.plot(ax = ax6, legend =False, antialiased=True); ax6.set_title('Return temperature',fontsize=25); ax6.set_ylabel(r'$\mathit{T_{PVT, out}}$'+'  (kW)',fontsize = 30 );ax6.set_xlabel('Hour of the year',fontsize=20);ax6.tick_params(axis='x', labelsize=20);ax6.tick_params(axis='y', labelsize=20)

# <codecell>


