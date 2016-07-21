# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #1. Pre-Areas and Zones:
# 
# ##INTRODUCTION
# This subroutine creates diverse zones/clusters/cityquarter of Buildings for the city of interest.
# 
# ###The input:
# 
# -  Context: a .shp (multi-polygon) file including the buildings of the city of interest and its surroundings.
# -  Boundaries_City: a .shp (single-polygon) file of the administrative/political boundaries of the city with the surroundings.
# -  Boundaries_CQ: a (multi-polygon) file of the administratiev/political boundaries of the zones/clusters/cityquarters to study.
#    Specific Requirements, fields: "Zone" (Zone/cluster/Cityquarter to study), "CityQuarter"(City quarter or district where the zone,/Cluster belongs to)
# 
# ###The Output:
# 
# - Buildings for the next areas:
# - City: a .shp (multi-polygon) file including the Buildings inside the boundaries of the city.
# - Surroundings: a .shp (multi-polygon) file including the Buildings outside the boundaries of the city.
# - City Quarter 'n': Multiple .shp (multi-polygon) files including the Buildings inside the boundaries of the n City-quarters/zones/Clusters to analyse.
# 
# ###Data Requierements:
# 
# The next data requieremnts are not completely necessary to run this routine, but this is in total
# all the information requiered to Model the Urban Energy System.
# 
# 1. For the Buildings inside the area of study (the zones/clusters/cityquarters):
# 
# - Factor of occupancy (0-1): Ratio of ocuppied area in every building for the categories (14) of SDU(Single dwelling units), 
#   MDU (Multiple dwelling units) ADMIN(Administrative), INDUS(Industrial), COM(Comercial),HOT(Hotel),  SR(,
#   EDU (Schools, excl. University), CR(Cooling rooms), REST(restaurants HEALTH(Hospital), SPORT(Sport, leisure), SWIM(Swimming pool,
#   PUBLIC(Chuches, public halls), DEPO(deposits- unheated spaces), ICE(Ice hokey stadiums).
# - Height in meters.
# - Factor of heated space (0-1): if unknown it is considered 0.9 = 90% of footprint area.
# - Year of construction.
# - Energy system for heating and cooling: ratio of energy demand currently supplied by a X energysystem between the categories of:.......
# 
# 
# 2. For the Buildings inside the Main Cluster/Zone/Cityquarter of study:
# 
# - All of point (I).
# - U values of Roof, Walls, Basement, Windows,
# - Type of Glazing.
# - Number of Floors.
# - Ratio of windows/opaque surfaces,
# - Type of construction(light, Heavy,Medium)
# 
# 3. For the Buildings out of the area of study
# 
# - Height in meters.

# <markdowncell>

# ##MODULES

# <codecell>

import arcpy
import pandas as pd
arcpy.env.workspace = 'c:\ArcGIS\EDM.gdb'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")

# <codecell>

import sys, os
sys.path.append("C:\Users\Jimeno Fonseca\Documents\Console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 

# <markdowncell>

# ##VARIABLES

# <codecell>

Zone_calc = 4
database = r'c:\ArcGIS\EDM.gdb'
Scenarios = ['SQ','BAU','HEB','CAMP','UC']
Boundaries_City = r'c:\ArcGIS\EDM.gdb\RawData\Boundaries_City' # administrative boundaries - Contents: No special contents.
Boundaries_Zones = r'c:\ArcGIS\EDM.gdb\RawData\Boundaries_CQ' #Not necessarly adminsitrative boundaries, more dependent on typology and social aspects (Zone) - Contents: Zone, CityQuarter, and a ID which is an Integer

# <codecell>

temporal1 = r'c:\ArcGIS\temp' # location of temporal files out of the database
temporal2 = r'c:\ArcGIS\EDM.gdb\temp' #location of temptemporal2ral files inside the database

# <markdowncell>

# ###PROCESSES

# <markdowncell>

# #### Definition of Area and zones

# <codecell>

for scenario in Scenarios:
    Context = database+'\\'+scenario+'\\'+scenario+'CONTEXT'
    Zone = database+'\\'+scenario+'\\'+scenario+'AREA'
    arcpy.MakeFeatureLayer_management(Context, 'CTR_lyr')
    arcpy.SelectLayerByLocation_management('CTR_lyr', 'intersect', Boundaries_Zones)
    arcpy.CopyFeatures_management('CTR_lyr', database+'\\'+x+'\\'+x+'AREA')
    
    #Import List of Cityquarters and Count them for iteration
    OutTable = 'Boundaries_CQ.dbf'
    arcpy.TableToTable_conversion(Boundaries_Zones, temporal1, OutTable)
    List_Boundaries_Zones = dbf2df(temporal1+'\\'+OutTable)
    Counter = List_Boundaries_Zones.Zone.count()
    List_Boundaries_Zones['ID']= range(1,Counter+1)
    
    if x == 'SQ':
        r1= 1
        r2= Counter+1
    else:
        r1= Zone_of_study
        r2 = Zone_of_study+1
    
    for City_Quarter in range(r1,r2):
        # list of variables
        Value = List_Boundaries_Zones.loc[City_Quarter-1,Field] # set the value or name of the City quarter
        Where_clausule =  ''''''+'"'+"ID"+'"'+"="+"\'"+str(Value)+"\'"+''''''
        
        # selection
        Single_CityQuarter = temporal1+"\\"+"zone"+str(City_Quarter)+'.shp' # location of the result of each CityQuarter
        arcpy.Select_analysis(Boundaries_Zones,Single_CityQuarter,Where_clausule) # routine
        arcpy.env.workspace = 'c:\ArcGIS\EDM.gdb'
        
        # copy of city quarters
        arcpy.MakeFeatureLayer_management(Zone, 'CQ_lyr') 
        arcpy.SelectLayerByLocation_management('CQ_lyr', 'intersect', Single_CityQuarter)
        
        if City_Quarter != Zone_calc:
            arcpy.CopyFeatures_management('CQ_lyr', database+'\\'+'Surroundings'+"\\"+"ZONE_"+str(City_Quarter))
        else:
            arcpy.CopyFeatures_management('CQ_lyr', database+'\\'+scenario+"\\"+scenario+"ZONE_"+str(City_Quarter))    

# <codecell>


