# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ##Modules

# <codecell>

import pandas as pd
from pylab import *
import matplotlib.pyplot as plot
import os
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
import os

# <markdowncell>

# ##VARIABLES

# <codecell>

CQ_name = 'CityQuarter_3'
CQ =r'c:\ArcGIS\EDM.gdb\Communities'+'\\'+CQ_name
Building = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\DEDM\StatusQuo\CityQuarter_3\Bau A.csv')
Scenario = 'StatusQuo'
DataCQ = pd.ExcelFile('c:\ArcGIS\EDMdata\Measured'+'\\'+CQ_name+'\\'+'BuildingProperties.xls') # Location of the data of the CQ to run
CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements

# <codecell>

RadiationFile = r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'radiation'+'\\'+'RadiationYearFinal.csv'

# <codecell>

locationtemp1 = r'c:\ArcGIS\temp'
locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+CQ_name

# <markdowncell>

# ##pre-Processes

# <codecell>

AllProperties = EDM.CalcProperties(CQ, CQproperties, RadiationFile, locationtemp1)

# <codecell>

Solar = EDM.CalcIncidentRadiation(AllProperties, RadiationFile)

# <markdowncell>

# ##Only variables needeed

# <codecell>

Properties = AllProperties[['Af','Emission_heating','Emission_cooling']]

# <codecell>

Building

# <codecell>

Thermalloads = Building[['DATE','Hour','Hour2','tair_ac','IH_nd_ac','IC_nd_ac','te']]

# <markdowncell>

# find the maximum values

# <codecell>

rows = Thermalloads.IH_nd_ac.count()
for row in range(rows):
    if Thermalloads.loc[row,'IH_nd_ac'] == Thermalloads['IH_nd_ac'].max():
        print Thermalloads.loc[row,'DATE'], Thermalloads.loc[row,'Hour'], Thermalloads.loc[row,'Hour2'], Thermalloads.loc[row,'IH_nd_ac'].max(),Thermalloads.loc[row,'te'],Thermalloads.loc[row,'tair_ac']

# <codecell>

Thermalloads['IH_nd_ac'].average()

# <markdowncell>

# ##functions

# <codecell>

def calc_em_t(SystemH,SystemC):
    #references: 70 supply 50 return radiatior system #several authors
    # floor cooling/ceiling cooling 18 -22 /thermofloor.co.uk
    # floor heating 
    heating ={'Type':['Wall heating','Ceiling heating', 'Radiatior', 'Floor heating', 'Air conditioning'],'tsnominal':[,35,70,35,],'trnominal':[,15,50,15,]}
    cooling ={'Type':['Ceiling cooling','Floor cooling', 'Air conditioning'],'tsnominal':[18,18,12],'trnominal':[22,22,17]}
    
    
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Exterior':
            return ValuesRf_Table.loc[row,'ValueOUT']
        elif ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Interior':
            return ValuesRf_Table.loc[row,'ValueIN']
        else:
            return 1  
        
    return ts_0,tr_0

# <markdowncell>

# Create domestic hydronic model

# <codecell>

time = 8750

# <codecell>

Emissiontemp = calc_em_t(AllProperties.loc[0,'Emission_heating',AllProperties.loc[0,'Emission_cooling'])
ts_0 = Emissiontemp[0]
tr_0 = Emissiontemp[1]

# <codecell>

Q = U*A*(ts-ti_0

# <codecell>


# <markdowncell>

# ## Processes

