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

Scenario = 'SQ'; Zone_of_study = 1
Zone_calc = 1

# <codecell>

database = r'c:\Zernez\EDM.gdb'  #ArcGIS database
database2 = r'c:\Zernez\ERM.gdb'  #ArcGIS database
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
    CQFPrint = database+'\\'+Scenario+'\\'+Scenario+'3DFPZone_'+str(Zone_calc)
    context3D = database+'\\'+Scenario+'\\'+Scenario+'3DAREA'

# <codecell>

latitude = 47.1628017306431      #longitude of the city
longitude = 8.31                 #latitude of the city
timezone = 1                     #Timezone of the city
Yearsimul = 2010
elevRaster = arcpy.sa.Raster(DEM)
DEM_extent = elevRaster.extent

# <codecell>

T_G_day['sunrise'] = 0
T_G_day=  EDM.calc_sunrise(T_G_day,Yearsimul,timezone,longitude,latitude)

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
EDM.Burn(Simple_context,DEM,DEMfinal,locationtemp1,locationtemp2,database, DEM_extent)

# <headingcell level=4>

# FOR 3D BUILDINGS 1. Simplify buildings and create raster model for radiation analysis 

# <codecell>

# Define local variables  - Outputs
Simple_CQ = CQFPrint #just the footprint is necesary
Simple_context = context3D #here all the 3D buildings are necesary
DEMfinal = locationtemp1+'\\'+'DEM_All2'

# <codecell>

# Burn buildings of the context into the DEM model
EDM.Burn3D( Simple_context, DEM, DEMfinal, locationtemp1, locationtemp2, database, DEM_extent)

# <headingcell level=4>

# 2. Create observers on roof tops for the analysis

# <codecell>

DEM_zone_loc = locationtemp1+"\\"+"DEM_zone"+str(Zone_calc) #DEM raster of rooftops in the zone
observers_all = database2+'\\'+Scenario+'\\'+Scenario+'rad' #Observers before getting to reduce potential
Aspect_raster = locationtemp1+"\\"+"aspect"
Slope_raster = locationtemp1+"\\"+"slope"

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
hourly_horizontal_rad = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Radiation_rooftop'+'\\'+'Rad_hor_roofpoint.csv'
locationfinal = 'C:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_calc)+'\\'+'Radiation_rooftop'

# <codecell>

from IPython.parallel import Client # Create Parallel modules nd star the 8 cores
client = Client()
lview = client.load_balanced_view()
lview.block = True
dview = client[:]
dview.push({'Scenario':Scenario, 'T_G_day':T_G_day, 'latitude':latitude, 'locationfinal':locationfinal,
            'longitude':longitude, 'timezone': timezone,'DEMfinal':DEMfinal,'observers_all':observers_all, 'T_G_hour':T_G_hour})
#px import sys
#px if r'C:\Console\EDM' not in sys.path: sys.path.append(r'C:\Console\EDM')
#px import EDMFunctions as EDM

# <codecell>

@lview.parallel()
def radiation(day):
    aspect_slope = "FLAT_SURFACE"
    heightoffset = 0
    return EDM.CalcRadiation(day, Scenario, DEMfinal, observers_all, T_G_day, latitude, locationfinal, aspect_slope, heightoffset)

# <codecell>

radiation.map(range(1,366))

# <codecell>

@lview.parallel()
#run the transformation of files in parallel - appending all and adding non-sunshine hours
def radiationday(day):
    rad =   EDM.calc_radiationday(day, T_G_day, locationfinal)
    return rad

# <codecell>

radiations = radiationday.map(range(1,366))

# <codecell>

Radiationyear = radiations[0]
for r in radiations[1:]:
    Radiationyear = Radiationyear.merge(r, on='ID')
Radiationyear.fillna(value=0,inplace=True)
Radiationyear.to_csv(hourly_horizontal_rad,Index=False)
print 'Complete!'

# <codecell>


