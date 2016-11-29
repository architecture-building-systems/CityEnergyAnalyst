# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #RADIATION MODEL
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
# - Longitude: Longitude of the City of the case study (+) if East of Grenwhich meridian, (-) if West.
# - Timezone: GMT + (?)
# - Daylightsaving dates: Number of day of the year where daylightsaving measures take place. for Zug in 2013 = 90 and 300
# 
# ###The Output:
# 
# - DEModelFinal = a .asci or tif (raster) file containing a high definition Digital Elevation Model with Buildings.
# - DataRadiation = a .csv file containing the hourly radiation values Wh/m2 incident in a point representing every vertical surface of the Buildings analyzed,
# This file contents the Length of everysurface, the name of the building at which this surface belons too, the height of the building related, the Factor " Freeheight" and the Factpr "FactorShade"
# Freeheight stands for the height of the surface that is exposed to the exterior, factor Shade represents the amount of area of the surface facing the exterior.

# <markdowncell>

# ##Modules

# <codecell>

import arcpy
import sys
import pandas as pd
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
import os
import datetime
import jdcal
import numpy as np
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <markdowncell>

# ##Variables

# <codecell>

Scenario = 'SQ' #Name of the City Quarter to calculate
Zone = 1

# <codecell>

database = r'c:\Zernez\EDM.gdb'  #ArcGIS database
CQ = database+'\\'+Scenario+'\\'+Scenario+'Zone_'+str(Zone)
context = database+'\\'+Scenario+'\\'+Scenario+'AREA'
DEM = database+'\\DEM_Clip' # DEM of analysis resampled to grid of 1m for more accurracy
locationfinal = r'c:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone)+'\\'+'Radiation_faces'

# <codecell>

WeatherData = pd.ExcelFile('C:\Zernez\EDMdata\Weatherdata\Temp_Design.xls') # Location of temperature data
T_G_hour = pd.ExcelFile.parse(WeatherData, 'Values_hour') # temperature and radiation table
T_G_day = pd.ExcelFile.parse(WeatherData, 'Values_day') # temperature and radiation table

# <codecell>

latitude =  46.95240555555556   #47.1628017306431      #longitude of the city
longitude = 7.439583333333333    #8.31                 #latitude of the city
timezone = 1                     #Timezone of the city
Yearsimul = 2014
DEM_extent = '801979, 174609, 804203, 176423' #lef,bottom,right,top

# <codecell>

environment = r'c:\Zernez'
locationtemp1 = r'c:\Zernez\temp'
locationtemp2 = r'c:\Zernez\EDM.gdb\temp'

# <codecell>

T_G_day['sunrise'] = 0
T_G_day=  EDM.calc_sunrise(T_G_day,Yearsimul,timezone,longitude,latitude)

# <markdowncell>

# ##Processes

# <markdowncell>

# ####1. Simplify buildings and create raster model for radiation analysis

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
EDM.Burn(Simple_context,DEM,DEMfinal,locationtemp1,locationtemp2,database,DEM_extent)

# <markdowncell>

# ####2. Calculate boundaries of buildings and derive factorheight and FactorShade.

# <codecell>

# Define local variables  - Outputs
DataFactorsBoundaries = locationtemp1+'\\'+'DataFactorsBoundaries.csv'
DataFactorsCentroids = locationtemp1+'\\'+'DataFactorsCentroids.csv'

# <codecell>

EDM.CalcBoundaries(Simple_CQ, locationtemp1, locationtemp2, DataFactorsCentroids, DataFactorsBoundaries)

# <markdowncell>

# ####3. Calculate observation points eliminating any overlap of those boundaries

# <codecell>

# Local variables
Observers = locationtemp2+'\\'+'observers'

# <codecell>

EDM.CalcObservers(Simple_CQ, Observers, DataFactorsBoundaries, locationtemp2, environment)

# <markdowncell>

# #### 4. Calculate radiation - in parallel

# <codecell>

from IPython.parallel import Client # Create Parallel modules nd star the 8 cores
client = Client()
lview = client.load_balanced_view()
lview.block = True
dview = client[:]
dview.push({'Scenario':Scenario, 'T_G_day':T_G_day, 'latitude':latitude, 'locationfinal':locationfinal,
            'longitude':longitude, 'timezone': timezone,'DEMfinal':DEMfinal,'Observers':Observers})
%px import sys
%px if r'C:\Console\EDM' not in sys.path: sys.path.append(r'C:\Console\EDM')
%px import EDMFunctions as EDM

# <codecell>

@lview.parallel()
def radiation(day):
    aspect_slope = "FROM_DEM"
    heightoffset = 1
    return EDM.CalcRadiation(day, Scenario, DEMfinal, Observers, T_G_day, latitude, locationfinal, aspect_slope, heightoffset)

# <codecell>

radiation.map(range(350,351))

# <codecell>

@lview.parallel()
#run the transformation of files in parallel - appending all and adding non-sunshine hours
def radiationday(day):
    return EDM.calc_radiationday(day,T_G_day, locationfinal)

# <codecell>

radiations = radiationday.map(range(1,366))

# <codecell>

Radiationyear = radiations[0]
for r in radiations[1:]:
    Radiationyear = Radiationyear.merge(r, on='ID',how='outer')
Radiationyear.fillna(value=0,inplace=True)
Radiationyear.to_csv(locationfinal+'\\'+'RadiationYear.csv',Index=False)
print 'Complete!'

# <markdowncell>

# ###5. Assign ratiation to every surface of the buildings
# ####ATTENTION: to run this the boundaries and observers have to be re run first if they have not been

# <codecell>

# local variables
DataradiationLocation = locationfinal+'\\'+'RadiationYear.csv'
Radiationyearfinal = locationfinal+'\\'+'RadiationYearFinal.csv'

# <codecell>

reload(EDM)

# <codecell>

EDM.CalcRadiationSurfaces(Observers,Radiationyearfinal, DataFactorsCentroids, DataradiationLocation,  locationtemp1, locationtemp2)

