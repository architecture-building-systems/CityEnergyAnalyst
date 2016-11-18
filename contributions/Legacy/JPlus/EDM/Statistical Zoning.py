# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=3>

# uP TO nOW THIS ROUTINE IS MADE MANUALLY IN ARCGIS. BUT IT CAN BE AUTOMIZED FOLLOWING THE RESULTS OF THE PAPER"INTEGRATED MODEL FOR CHARACTERIZATION OF SPATIOTEMPORAL PATTERNS OF BUILDING ENERGY DEMAND IN NEIGHBORHOODS AND CITY DISTRICTS"
# HERE AFTER IS INTEGRATED A MODEL TO RELOCATE THE FILES FROM THE PRELIMINAR ZONING (THIS IS TEMPORAL) IN THE FUTURE THE ZONING IS MADE BEFORE CALCULATING EVERYTHING. (RIGHT AFTER THE RESULTS OF THE STATISTICAL MODEL) AVOIDING THIS STEP

# <codecell>

import arcpy
import pandas as pd
arcpy.env.workspace = 'c:\ArcGIS\EDM.gdb'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
import shutil

# <codecell>

import sys, os
sys.path.append("C:\Users\Jimeno Fonseca\Documents\Console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 

# <codecell>

Zone_calc = 4
database = r'c:\ArcGIS\EDM.gdb'
scenario = 'SQ'
Boundaries_Zones = r'c:\ArcGIS\Zoning.gdb\DataCollection\Energyareas' #Not necessarly adminsitrative boundaries, more dependent on typology and social aspects (Zone) - Contents: Zone, CityQuarter, and a ID 
temporal1 = r'c:\ArcGIS\temp' # location of temporal files out of the database
temporal2 = r'c:\ArcGIS\EDM.gdb\temp' #location of temptemporal2ral files inside the database

# <codecell>

Zone = database+'\\'+scenario+'\\'+scenario+'AREA'
#Import List of Cityquarters and Count them for iteration
OutTable = 'table.dbf'
arcpy.TableToTable_conversion(Boundaries_Zones, temporal1, OutTable)
List_Boundaries_Zones = dbf2df(temporal1+'\\'+OutTable)
Counter = List_Boundaries_Zones.OBJECTID.count()
List_Boundaries_Zones['ID']= range(1,Counter+1)

for City_Quarter in range(1,Counter+1):
    # list of variables
    Where_clausule =  ''''''+'"'+"ID"+'"'+"="+"\'"+str(int(City_Quarter))+"\'"+'''''' # strange writing to introduce in ArcGIS

    # selection
    Single_CityQuarter = temporal1+"\\"+"zone"+str(City_Quarter)+'.shp' # location of the result of each CityQuarter
    arcpy.Select_analysis(Boundaries_Zones,Single_CityQuarter,Where_clausule) # routine
    arcpy.env.workspace = 'c:\ArcGIS\EDM.gdb'

    # copy of city quarters
    arcpy.MakeFeatureLayer_management(Zone, 'CQ_lyr') 
    arcpy.SelectLayerByLocation_management('CQ_lyr', 'intersect', Single_CityQuarter)

    if City_Quarter != Zone_calc:
        dstname = r'C:\ArcGIS\EDMdata\DataFinal\EDM\Surroundings'+'\\'+'Zone_'+str(City_Quarter)
        location = database+'\\'+'Surroundings'+"\\"+"ZONE"+str(City_Quarter)
        arcpy.CopyFeatures_management('CQ_lyr', location)
    else:
        dstname = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+scenario+'\\'+"Zone_"+str(City_Quarter)
        location = database+'\\'+scenario+"\\"+scenario+"ZONE"+str(City_Quarter)
        arcpy.CopyFeatures_management('CQ_lyr', location)

    OutTable = 'table.dbf'
    arcpy.TableToTable_conversion(location, temporal1, OutTable)
    List = dbf2df(temporal1+'\\'+OutTable)
    List_names = list(List.Name)
    COUNTER = List_Boundaries_Zones.OBJECTID.count()

    listzones = [1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]
    for x in listzones:
        srcname = r'C:\ArcGIS\EDMdata\DataFinal\EDM\Surroundings'+'\\'+'Zone_'+str(x)
        names = os.listdir(srcname)
        for name in List_names:
            namecsv = name+'.csv' 
            if namecsv in names:
                src= os.path.join(srcname, namecsv)
                dst = os.path.join(dstname, namecsv)
                shutil.move(src, dst)

# <codecell>


