# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #Dynamic visualization
# 
# This subroutine intends to create a dynamic visualization hour per hour of every cluster in the area
# The main enduse of energy considered for this analysis are:
# 
# - Space heating: During winter at the 1st of January.
# -- temperature of supply and return
# - Space cooling: Suring summer at 1st of July.
# -- temperature of supply and return
# - Hot water: During Summer at 1st of July and ruing winter at the 1st of January.
# - Electricity: During summer at 1st of July.
# 
# 

# <codecell>

import pandas as pd
import os, sys
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
import matplotlib.pyplot as plt
import arcpy
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <markdowncell>

# ###Variables

# <codecell>

Scenario = 'StatusQuo'
Database = r'C:\ArcGIS\Animations.gdb'
Animation = r'C:\ArcGIS\TimeAnimation'

# <markdowncell>

# Creation of appended files for a week in summer and a week in winter

# <codecell>

for r in range(4,5):
    date = pd.DataFrame(pd.date_range('1/1/2010', periods=8760, freq='H'))
    CQ_name = 'CityQuarter_'+str(r)
    locationAna = r'C:\ArcGIS\EDMdata\DataFinal\DEDM'+'\\'+Scenario+'\\'+CQ_name+'\\'
    locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+CQ_name+'\\'    
    Buildings = pd.read_csv(locationAna+'Total.csv')
    counter = Buildings.Name.count()
    # table with dynamic data already CONSOLIDATED
    Table = pd.read_csv(locationFinal+Buildings.loc[0,'Name']+'.csv')
    Table['DATE'] = date
    # Selected weeks for the year of analysis
    Weekwinter = Table[72:240] #8th January
    Weeksummer = Table[4440:4608] #1st august
    for row in range(1,counter):
        name = Buildings.loc[row,'Name']
        read0 = pd.read_csv(locationFinal+name+'.csv')
        read0['DATE'] = date
        readwinter = read0[72:240]
        readsummer = read0[4440:4608]
        Weekwinter = Weekwinter.append(readwinter,ignore_index=True)
        Weeksummer = Weeksummer.append(readsummer,ignore_index=True)
    
    #na values form building without load    
    Weekwinter.fillna(value=0,inplace=True) 
    Weeksummer.fillna(value=0,inplace=True) 
    
    Weekwinter[['DATE','NAME','Qhsf','Qwwf','tsh','trh']].to_csv(locationFinal+'Weekwinter.csv',index=False)
    Weeksummer[['DATE','NAME','Qcsf','Qwwf','tsc','trc']].to_csv(locationFinal+'Weeksummer.csv',index=False)   
    
    # put the table in the database to make the querry
    Namesummer = 'CQ'+str(r)+'SU'
    arcpy.TableToTable_conversion(locationFinal+'Weeksummer.csv',Database,Namesummer)
    arcpy.ConvertTimeField_management(Database+'\\'+Namesummer,"DATE","'Not Used'","TIME","TEXT","yyyy-MM-dd HH:mm:ss")

    Namewinter = 'CQ'+str(r)+'WIN'
    arcpy.TableToTable_conversion(locationFinal+'Weekwinter.csv',Database,Namewinter)
    arcpy.ConvertTimeField_management(Database+'\\'+Namewinter,"DATE","'Not Used'","TIME","TEXT","yyyy-MM-dd HH:mm:ss")
   
    # This part creates the time series and stores it in a folder of each one of the required fields ready to be visualized
    Season = [Namesummer,Namewinter]
    ListVarSummer = ['Qcsf','Qwwf','tsc','trc']
    ListVarwinter = ['Qhsf','Qwwf','tsh','trh']
    for N in Season:
        if N == Namesummer:
            List = ListVarSummer
            var2 = '_SU'
        else:
            List = ListVarwinter
            var2 = '_WIN'
        for var in List:
            fieldList = [[N+'.NAME','NAME'],[N+'.TIME','TIME'],[N+'.'+var,var],
                         [CQ_name+'.Name','Name'],[CQ_name+'.Shape','Shape']]
            whereClause = CQ_name+'.Name = '+N+'.NAME'
            tableList = Database+'\\'+N
            layerCQ = CQ_name+'.lyr'
            arcpy.MakeFeatureLayer_management(Database+'\\'+CQ_name,layerCQ)
            
            # make query of table
            arcpy.MakeQueryTable_management([tableList,layerCQ],"QueryTable","USE_KEY_FIELDS","#",fieldList,whereClause)
            Layer = "QueryTable"
            
            # set temporal directories
            if not os.path.exists(Animation+'\\'+CQ_name):
                os.makedirs(Animation+'\\'+CQ_name)
            arcpy.FeatureClassToFeatureClass_conversion(Layer,Animation+'\\'+CQ_name,var+var2)

# <rawcell>

# The rest is done in ArcGIS manually. Visualization!

