# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import pandas as pd
import arcpy

# <headingcell level=4>

# Variables

# <codecell>

Scenario = 'UC'; Zone_of_study = 4
Zone_calc = 4

# <codecell>

database = r'c:\ArcGIS\EDM.gdb'  #ArcGIS database

# <codecell>

locationFinal = r'c:\ArcGIS\ESMdata\DataFinal\GEO'

# <codecell>

if Zone_calc != Zone_of_study:
    CQ = database+'\\'+'Surroundings'+'\\'+'Zone_'+str(Zone_calc)
else:
    CQ = database+'\\'+Scenario+'\\'+Scenario+'Zone_'+str(Zone_calc)

# <headingcell level=4>

# Process

# <codecell>

with arcpy.da.SearchCursor(CQ, ["Name","Floors","SHAPE@AREA"]) as cursor:
    Name = []
    Area = []
    for row in cursor:
        if row[1] >= 20: #Skyscraper or tall building geothermal allowed 20 Floors
            Area.append(row[2])
            Name.append(row[0])
        else:
            Area.append(0)
            Name.append(row[0])
pd.DataFrame({'Name':Name,'Area_geo':Area}).to_csv(locationFinal+'\\'+Scenario+'\\'+'Geothermal.csv', index=False)

