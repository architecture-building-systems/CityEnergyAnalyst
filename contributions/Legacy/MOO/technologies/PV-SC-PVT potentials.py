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
import numpy as np
import re


latitude = 47.1628017306431      #longitude of the city
longitude = 8.31                 #latitude of the city
timezone = 1                     #Timezone of the city
Yearsimul = 2010
min_production = 0.75 # points are selected with at least a minimum production of this % from the maximum in the area.
grid_side = 2 # in a rectangular grid of points, one side of the square. this cannot be changed if the solra potential was made with this.
worst_hour = 8744 # first hour of sun on the solar solstice
angle_north = 122.5

type_PVpanel = 1 # monocrystalline
type_SCpanel = 1 # Flatplate collector
type_PVTpanel = 1 # Flatplate collector
misc_losses = 0.10 # losses for a good system due to cabling, regulator and inverters

WeatherData = pd.ExcelFile('C:\Zernez\EDMdata\Weatherdata\Temp_Design.xls') # Location of temperature data
T_G_hour = pd.ExcelFile.parse(WeatherData, 'Values_hour') # temperature and radiation table
T_G_day = pd.ExcelFile.parse(WeatherData, 'Values_day') # temperature and radiation table
T_G_day['sunrise'] = 0
T_G_day=  EDM.calc_sunrise(T_G_day,Yearsimul,timezone,longitude,latitude)

diffuseProp = T_G_day['diff'].mean()
transmittivity = T_G_day['ttr'].mean()
worst_sh = T_G_hour.loc[worst_hour,'Sh']
worst_Az = T_G_hour.loc[worst_hour,'Az']

locationtemp1 = r'c:\Zernez\temp'
locationtemp2 = r'c:\Zernez\EDM.gdb\temp'

# read files
hourly_horizontal_rad = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Radiation_rooftop'+'\\'+'Rad_hor_roofpoint.csv'
observers_all = database2+'\\'+Scenario+'\\'+Scenario+'rad' #Observers gotten from resource potential

# DF WITH HOURLY SOLAR RADAITION
hourly_data = pd.read_csv(hourly_horizontal_rad)

# YEARLY SOLAR RADIATION 
total = hourly_data.drop({'ID','Unnamed: 0'}, axis = 1).sum(axis=1)
total_df = pd.DataFrame(total,columns=["GB"])
total_df['ID']= hourly_data['ID']
Max_Isol = total_df.GB.max()
Min_Isol = Max_Isol*min_production #80% of the local average maximum in the area
total = None # erase from memory

#AND APPEND TO GIS OBSERVERS
outpath = "observers.dbf"
df2dbf(total_df, locationtemp1+'\\'+outpath)
arcpy.JoinField_management(observers_all, "pointid", locationtemp1+'\\'+outpath, "ID")

# Calculate the heights of all buildings
outpath = "buildings.dbf"
arcpy.TableToTable_conversion(CQ,locationtemp1,outpath)
buildings_data = dbf2df(locationtemp1+'\\'+outpath)
height = buildings_data.height.sum()

# PV POTENTIAL

#CREATE DUPLICATE OF OBSERVERS FOR CALCULATION PURPOSES
observers_data = database2+'\\'+Scenario+'\\'+Scenario+'radClean'
arcpy.FeatureClassToFeatureClass_conversion(observers_all, database2+'\\'+Scenario, Scenario+'radClean')

#APPLY FLITER AND CALCULATE OPTIMAL TILT, SPACING AND ORIENTATION:
# remove points with radiation less than 80% the maximum in the obesrvers_all #remove points towards north #calculate tilted area also
#create categories of tilted areas. categorize also potentials.
module_lenght = 1 #m # 1 for PV and 1 for solar collectors
optimal_angle_and_tilt(observers_data,latitude,worst_sh, worst_Az, transmittivity, diffuseProp, grid_side, module_lenght, angle_north, Min_Isol, Max_Isol)
#IMPORT OBSERVERS WITH FILTER AS DF
outpath = "observers.dbf"
arcpy.TableToTable_conversion(observers_data,locationtemp1,outpath)
observers_fin = dbf2df(locationtemp1+'\\'+outpath)

# APPLY HOURLY FILTER: minimum solar radiation of  50 W/m2
Clean_hourly = hourly_data.drop({'ID','Unnamed: 0'}, axis =1)
Clean_hourly[Clean_hourly[:]<= 50]= 0
#add again the 'ID' field
Clean_hourly['ID'] = hourly_data['ID']


#CONSERVE only matching points in Clean hourly data
Clean_hourly = Clean_hourly.merge(observers_fin, on='ID')

#calculate number of optima groups as number of optimal combiantions.
groups_ob = Clean_hourly.groupby(['CATB','CATGB','CATteta_z'])
hourlydata_groups = groups_ob.mean().reset_index()
hourlydata_groups = pd.DataFrame(hourlydata_groups)
Number_pointsgroup = groups_ob.size().reset_index() 
number_points = Number_pointsgroup[0]   #vector with number of points per group
#Clean_hourly = None #Clear from memory

groups_ob = observers_fin.groupby(['CATB','CATGB','CATteta_z'])
prop_observers = groups_ob.mean().reset_index()
prop_observers = pd.DataFrame(prop_observers)
Number_groups = groups_ob.size().count()
observers_fin = None #Clear from memory


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

