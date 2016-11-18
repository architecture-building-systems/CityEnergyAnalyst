# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# This rutine creates a table with the Minergie values to evaluate the performance of building envelope, systems and applainces.it also creates a list PEF and CO2 factors

# <codecell>

import pandas as pd
import os, sys
import arcpy
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
reload(EDM)

# <codecell>

Zone_of_study = 4
Zone_calc = 4
number_of_zones = 20
database = r'c:\ArcGIS\EDM.gdb'
Scenarios = ['SQ','BAU','HEB','CAMP','UC']

# <codecell>

locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM'
locationtemp1 = r'c:\ArcGIS\temp'

# <markdowncell>

# ##Process

# <markdowncell>

# First create the minergie data

# <codecell>

for x in Scenarios:
    # import data with the type of uses
    Data0 = database+'\\'+x+'\\'+x+'AREA'
    OutTable = 'SQAREA.dbf'
    arcpy.TableToTable_conversion(Data0, locationtemp1, OutTable)
    Data1 = dbf2df(locationtemp1+'\\'+OutTable)
    # select the prevailing type of use of the building Type
    Data2 = EDM.MainUse(Data1)
    Data2['Qhs_lim']= 0
    Data2['Typecode']= 0
    Data2['Ealaux_lim']= 0
    counter = Data2.Name.count()
    for row in range(counter):
        Uses = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU','EDU','CR','HEALTH','SPORT','SWIM','PUBLIC','SUPER','ICE','HOT']
        Qhli = [65,65,60,95,95,60,50,55,65,70,50,80,70,70,95,50,75,55]
        Eli = [25.5,4380,40.2,56.4,66.9,2,39.8,12,17,19.69,5.7,40.2,14.4,40.6,25.72,38.76,26.7,16]
        AQhli = [85,85,70,75,75,70,65,65,65,70,65,80,70,90,75,50,70,65]
        At_Ae = [1.2,1.5,1.8,1.5,1.5,2,1,1.3,1.7,1.2,1,0.8,2.4,2.5,1.2,1,2.4,1.3]
        for use in range(18):
            if Data2.loc[row,'Type'] == Uses[use]:
                Data2.loc[row,'Qhs_lim'] = 0.9*(Qhli[use]+AQhli[use]*At_Ae[use])*0.277778 #from MJ/m2 to kWh/m2
                Data2.loc[row,'Typecode'] = use+1
                Data2.loc[row,'Eli'] = Eli[use]
    Data2.to_excel(locationFinal+'\\'+x+'\\'+'Minergie.xls',cols ={'Name','Qhs_lim','Typecode','Eli'})

# <markdowncell>

# Create factors and export results of primary energy and emissions status Quo

# <codecell>

x = 'SQ'
# import data with the infrastructure type
Data0 = database+'\\'+x+'\\'+x+'INFR'
OutTable = 'SQINFR.dbf'
arcpy.TableToTable_conversion(Data0, locationtemp1, OutTable)
Data = dbf2df(locationtemp1+'\\'+OutTable)
# import data with loads
Data0 = r'c:\ArcGIS\Statistical Zoning.gdb'+'\\'+'Anchorloads'+'\\'+'BuildingsArea_1'
OutTable = 'SQloads.dbf'
arcpy.TableToTable_conversion(Data0, locationtemp1, OutTable)
Loads = dbf2df(locationtemp1+'\\'+OutTable)
# create join of values
Jointables = pd.merge(Data,Loads, on ='Name')
# import excel file with factors
Factors = pd.read_excel(r'C:\ArcGIS\EDMdata\Statistical\Codes_infr.xls','Sheet1')

# <codecell>

Jointables['Qhs_type'] = Jointables['Qhs_type'].apply(int)
Jointables['Qhs_type'] = Jointables['Qhs_type'].apply(str)
Jointables['Qhs_carrie']= Jointables['Qhs_carrie'].apply(int)
Jointables['Qhs_carrie']= Jointables['Qhs_carrie'].apply(str)
Jointables['Code2_Qh'] = Jointables['Qhs_type']+ Jointables['Qhs_carrie']
Jointables['Qcs_type'] = Jointables['Qcs_type'].apply(int)
Jointables['Qcs_type'] = Jointables['Qcs_type'].apply(str)
Jointables['Qcs_carrie']= Jointables['Qcs_carrie'].apply(int)
Jointables['Qcs_carrie']= Jointables['Qcs_carrie'].apply(str)
Jointables['Code2_Qc'] = Jointables['Qcs_type']+ Jointables['Qcs_carrie']

#initialize the vector of primary energy (non-renewable with the factors of electricity
Jointables['EP'] = Jointables['E']*2.63
Jointables['GHG'] = Jointables['E']*0.0413

# <codecell>

#create real values
counter1 = Factors.Code.count()
counter2 = Jointables.Name.count()
for x in range(counter1):
    for y in range(counter2):
        if str(Factors.loc[x,'Code']) == Jointables.loc[y,'Code2_Qh']:
            #include 0.010 kWh/kWhth= % of auxiliary electricity per each thermal generated
            Jointables.loc[y,'EP'] = Jointables.loc[y,'EP']+Factors.loc[x,'Qhs_Ep']*Jointables.loc[y,'Qh']+(0.01*2.63*Jointables.loc[y,'Qh'])
            Jointables.loc[y,'GHG'] = Jointables.loc[y,'GHG']+Factors.loc[x,'Qhs_CO2']*Jointables.loc[y,'Qh']+(0.01*0.0413*Jointables.loc[y,'Qh'])
        
        if str(Factors.loc[x,'Code']) == Jointables.loc[y,'Code2_Qc']: 
            #include 0.010 kWh/kWhth= % of auxiliary electricity per each thermal generated
            Jointables.loc[y,'EP'] = Jointables.loc[y,'EP']+Factors.loc[x,'Qcs_Ep']*Jointables.loc[y,'Qc']+(0.01*2.63*Jointables.loc[y,'Qc'])
            Jointables.loc[y,'GHG'] = Jointables.loc[y,'GHG']+Factors.loc[x,'Qcs_CO2']*Jointables.loc[y,'Qc']+(0.01*0.0413*Jointables.loc[y,'Qc'])

#create scenario where all buildings are connected to a network of cooling and heating from the lake
Jointables['EP_lake'] = (Jointables['E']*2.63)+(0.897*Jointables['Qh'])+(0.15614*Jointables['Qc'])+(0.01*2.63*Jointables['Qc'])
Jointables['GHG_lake'] = (Jointables['E']*0.0413)+(0.015*Jointables['Qh'])+(0.0024*Jointables['Qc'])+(0.01*0.0413*Jointables['Qc'])            
            
            # Change units of CO2 from kgto ton.
# MJ to GJ
Jointables['EP'] = Jointables['EP']*3.6
Jointables['GHG'] = Jointables['GHG']*3.6
Jointables['EP_lake'] = Jointables['EP_lake']*3.6
Jointables['GHG_lake'] = Jointables['GHG_lake']*3.6

# <codecell>

Jointables.to_excel(locationFinal+'\\'+'SQ'+'\\'+'EP_GHG.xls',sheet_name='Values',cols={'Name','EP','GHG','EP_lake','GHG_lake'})

