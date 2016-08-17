# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #10. Grey emissions
# 
# This routine calculates the grey emissions for all buildings in the geodatabase
# it is based on the geometry of the buildings and standard properties of walls, windows, floors etc..
# it includes aall the vectors of grey energy related to building services, excavations, structure etc..

# <markdowncell>

# ####MODULES

# <codecell>

from __future__ import division
import arcpy
from arcpy import sa
import sys,os
import pandas as pd
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM

# <markdowncell>

# ####VARIABLES

# <codecell>

database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
Scenario = 'SQ' # BAU2030, CAMP2030, HEB2030, UC_2030 or Statusquo
Zone = 'ZONE_4' # BAU_2030, CAMP_2030, HEB_2030, UC_2030 or Cityquarter_3, without "_" for the total district or Area
locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\GEM'+'\\'+Scenario+'\\'+Zone #GEM is the grey emissions model
Yearcalc = 2050 # year to calculate at this moment if still emissions due o grey energy are consumed 

# <codecell>

Statistical_database = pd.ExcelFile('c:\ArcGIS\EDMdata\Statistical\Archetypes_properties.xls')
Model = pd.ExcelFile.parse(Statistical_database, 'Grey')

# <codecell>

locationtemp1 = r'c:\ArcGIS\temp'

# <markdowncell>

# ###PROCESS

# <codecell>

# Confirm directory to save results
if not os.path.exists(locationFinal):
    os.makedirs(locationFinal)
# Create the table or database of the CQ to generate the values
CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
OutTable = 'Database.dbf'
arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
Database = dbf2df(locationtemp1+'\\'+OutTable)

# <markdowncell>

# ### Calculation Grey Energy

# <codecell>

lists = ['GE','GGHG'] # list with values to calculate
Model['Code'] = Model.Factor + Model.Code2 
DatabaseUnpivoted = pd.melt(Database, id_vars=('Name','Shape_Area','Hs','Floors'))
#melt table to get all individual values
for value in lists:
    DatabaseUnpivoted['CODE'] = value+DatabaseUnpivoted.variable
    #Now both Database with the new codification is merged or joined to the values of the Statistical model
    DatabaseModelMerge = pd.merge(DatabaseUnpivoted, Model, left_on='CODE', right_on='Code')
    DatabaseModelMerge['ServicesF'] = DatabaseModelMerge.value * DatabaseModelMerge.Services
    DatabaseModelMerge['Wall_ext_agF'] = DatabaseModelMerge.value * DatabaseModelMerge.Wall_ext_ag
    DatabaseModelMerge['Wall_ext_bgF'] = DatabaseModelMerge.value * DatabaseModelMerge.Wall_ext_bg
    DatabaseModelMerge['Floor_intF'] = DatabaseModelMerge.value * DatabaseModelMerge.Floor_int
    DatabaseModelMerge['Wall_int_supF'] = DatabaseModelMerge.value * DatabaseModelMerge.Wall_int_nosup
    DatabaseModelMerge['Wall_int_nosupF'] = DatabaseModelMerge.value * DatabaseModelMerge.Wall_int_nosup
    DatabaseModelMerge['RoofF'] = DatabaseModelMerge.value * DatabaseModelMerge.Roof
    DatabaseModelMerge['Floor_gF'] = DatabaseModelMerge.value * DatabaseModelMerge.Floor_g
    DatabaseModelMerge['Win_extF'] = DatabaseModelMerge.value * DatabaseModelMerge.Win_ext
    DatabaseModelMerge['ExcavationF'] = DatabaseModelMerge.value * DatabaseModelMerge.Excavation
    
    Services = pd.pivot_table(DatabaseModelMerge, values='ServicesF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Wall_ext_ag = pd.pivot_table(DatabaseModelMerge, values='Wall_ext_agF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Wall_ext_bg = pd.pivot_table(DatabaseModelMerge, values='Wall_ext_bgF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Floor_int = pd.pivot_table(DatabaseModelMerge, values='Floor_intF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Wall_int_sup = pd.pivot_table(DatabaseModelMerge, values='Wall_int_supF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Wall_int_nosup = pd.pivot_table(DatabaseModelMerge, values='Wall_int_nosupF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Roof = pd.pivot_table(DatabaseModelMerge, values='RoofF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Floor_g = pd.pivot_table(DatabaseModelMerge, values='Floor_gF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Win_ext = pd.pivot_table(DatabaseModelMerge, values='Win_extF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Excavation = pd.pivot_table(DatabaseModelMerge, values='ExcavationF', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    
    # create frame with all the data nessesary for the calculation process and reset index
    data = pd.DataFrame({'Services': Services['All'],'Wall_ext_ag': Wall_ext_ag['All'],'Wall_ext_bg': Wall_ext_bg['All'],'Floor_int': Floor_int['All'],'Wall_int_sup': Wall_int_sup['All'],
                          'Wall_int_nosup': Wall_int_nosup['All'],'Roof': Roof['All'],'Floor_g': Floor_g['All'],'Win_ext': Win_ext['All'],
                          'Excavation': Excavation['All']})
    data['Name'] = data.index
    counter = data.Services.count()
    data.index = range(counter)
    data = pd.merge(data,Database,on='Name')
    #  restart counter to excecute operations for each building
    if value =='GE':
        serv = 236
    else:
        serv = 15
    
    counter = data.Name.count()
    data['result']= 0
    for x in range(counter):
        Z = 3 #height per floor
        FP = data.loc[x,'Shape_Area'] #floor area
        Af = FP*data.loc[x,'Hs']*data.loc[x,'Floors'] #conditioned area
        Floors = data.loc[x,'Floors']
        Yearcons = data.loc[x,'Year'] #construction year
        Yearrenov = data.loc[x,'Renovated'] #construction year
        Yearretro = data.loc[x,'Retrofit'] #construction year
        Area = data.loc[x,'Shape_Area']*Floors #conditioned area
        fw = data.loc[x,'fwindow']
        Perimeter = data.loc[x,'Shape_Leng']
        height = data.loc[x,'height']
        excavation = data.loc[x,'Excavation']
        Windows = fw*Perimeter*height*data.loc[x,'PFloor']*data.loc[x,'Win_ext']        
        Wall_int_avg = ((data.loc[x,'Wall_int_nosup']+data.loc[x,'Wall_int_sup'])/2)*1.15#factor to convert from component's area to floor area
        Walls_extbg  = data.loc[x,'Wall_ext_bg']*Perimeter*Z
        Walls_extag =  data.loc[x,'Wall_ext_ag']*(Perimeter*height*(1-fw))*data.loc[x,'PFloor']
        if data.loc[x,'PFloor'] < 1: # it means that part is a parking lot or storage in the building so internal partitions are considered and services od storage
            Walls_int = Wall_int_avg*Area*data.loc[x,'PFloor']
            Services = data.loc[x,'Services']*Af
        else:
            Walls_int = Wall_int_avg*Area
            Services = data.loc[x,'Services']*Af
        Floor =(data.loc[x,'Floor_g'])*FP #Calculation floor and roof
        Roof = (data.loc[x,'Roof'])*FP #Calculation floor and roof
        
        a = 0
        b = 0
        if Floors > 1:
            Floor_intern = (Floors-1)*FP*data.loc[x,'Floor_int']
        else:
            Floor_intern = 0
        # first it is assumed like the building was built
        construction = ((Floor+Roof)/60+(Walls_extbg+Walls_extag+Walls_int)/60 + Windows/60 + Floor_intern/60 + Services/40+excavation/60)    
        if Yearretro > Yearcons:
            Period = Yearcalc - Yearretro
            if Period > 60:
                data.loc[x,'result'] = 0
            else:
                retrofit = (Roof/60+ Walls_int/60 + Windows/60 + Services/40)
                if Yearcalc-Yearcons < 60:
                    data.loc[x,'result'] = (retrofit + construction)
        elif Yearretro > Yearrenov > Yearcons:
            Period = Yearcalc - Yearretro
            if Period > 60:
                data.loc[x,'result'] = 0
            else:
                renovated = (Roof/60+ Walls_extag/60 + Windows/60 + Services/40)
                if Yearcalc-Yearcons < 60:
                    a = 1
                elif Yearcalc-Yearretro < 60:
                    b = 1
                data.loc[x,'result'] = (b * retrofit + a*construction + renovated)
        
        elif Yearrenov > Yearcons:
            Period = Yearcalc - Yearrenov
            if Period > 60:
                data.loc[x,'result'] = 0
            else:
                renovated = (Roof/60+ Walls_extag/60 + Windows/60 + Services/40)
                if Yearcalc-Yearcons < 60:
                    data.loc[x,'result'] = (renovated + construction)
        else:
            Period = Yearcalc - Yearcons
            # if building is older thatn 60 years it already offset all its emissions.
            if Period > 60:
                data.loc[x,'result'] = 0
            else:
                data.loc[x,'result'] = construction
                
    if value == 'GE':
        final = pd.DataFrame({'Name': data['Name'],'GE': data['result']})
    else:
        final = pd.DataFrame({'Name': final['Name'],'GE': final['GE'],'GGHG': data['result']})
    
    final.to_excel(locationFinal+'\\'+'Grey.xls',sheet_name='Values',index=False)

# <codecell>


# <codecell>


