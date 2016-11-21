# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7. Diversity factors
# 
# 
# The objective of this script is to determine diversity factor of zones per energy vector
#     

# <codecell>

import pandas as pd
import os, sys
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import numpy as np

# <markdowncell>

# ###VARIABLES

# <codecell>

#list of inputs
database = r'c:\ArcGIS\EDM.gdb'
temporal1 = r'c:\ArcGIS\temp' # location of temporal files out of the database
Scenarios = ['SQ','BAU','UC','CAMP','HEB'] #List of scenarios to evaluate the potentials
locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM'
Zone_of_study = 4

# <codecell>

for scenario in Scenarios:  
    locationData = locationFinal+'\\'+scenario+'\\'+"ZONE_"+str(Zone_of_study)
    CQ_names =  pd.read_csv(locationData+'\\'+'Total.csv')
    names = CQ_names.Name
    Qh = []
    Qc = []
    Ef = []
    for x in names:
        building = pd.read_csv(locationData+'\\'+x+'.csv')
        Q = building.Qwwf+building.Qhpf+building.Qhsf
        Qf = building.Qcdataf+building.Qcsf+building.Qcpf+building.Qcicef
        E = building.Ef
        Qc.append(Qf), Qh.append(Q), Ef.append(E)        
    Qh_zone = np.sum(Qh, axis =0).max()/sum([x.max() for x in Qh])
    Qc_zone = np.sum(Qc, axis =0).max()/sum([x.max() for x in Qc])
    Ef_zone = np.sum(Ef, axis =0).max()/sum([x.max() for x in Ef])
    out = locationData+'\\'+'Diversity.csv'    
    pd.DataFrame({"DF_Qh":Qh_zone,"DF_Qc":Qc_zone,"DF_E":Ef_zone},index=[0]).to_csv(out, index=False, float_format='%3f')

# <codecell>


# <headingcell level=3>

# Do this for anergy networks DF

# <codecell>

#Create file with factors
for scenario in Scenarios:        
    Factors = pd.DataFrame({"ID":range(number_zones)}) #to match arcgis zoning names 
    Factors['DF_Qh'] = 0
    if scenario== 'SQ':
        r1= 1
        r2= number_zones+1
    else:
        r1= Zone_of_study
        r2 = Zone_of_study+1
    
    for r in range(r1,r2):
        if r != Zone_of_study:
            location = database+'\\'+'Surroundings'+"\\"+"ZONE"+str(r)
            locationfinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM\Surroundings'+'\\'+'Zone_'+str(r)
        else:
            location = database+'\\'+scenario+"\\"+scenario+"ZONE"+str(r)
            locationfinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+scenario+'\\'+"Zone_"+str(r)

        OutTable = 'table3.dbf'
        arcpy.TableToTable_conversion(location, temporal1, OutTable)
        List = dbf2df(temporal1+'\\'+OutTable)
        buildings = List.Name.count()
        
        for row in range (buildings):
            Name = List.loc[row,'Name']
            Data = pd.read_csv(locationfinal+'\\'+Name+'.csv')
            if row ==0:
                SeriesAVG = Data.copy()
                SeriesAVG['Qhf'] = Data['Qhsf']+Data['Qwwf']+Data['Qhpf']
                SeriesAVG['Qcf'] = Data['Qcsf']+Data['Qcdataf']+Data['Qcicef']+Data['Qcpf']
            else:
                SeriesAVG['Qhf'] = SeriesAVG['Qhf']+Data['Qhsf']+Data['Qwwf']+Data['Qhpf']
                SeriesAVG['Qcf'] = SeriesAVG['Qcf']+Data['Qcsf']+Data['Qcdataf']+Data['Qcicef']+Data['Qcpf']
        
        EmaxsysQh= (SeriesAVG['Qhf']).max()
        storage = 0
        for x in range(8760):
            surplus = SeriesAVG.loc[x,'Qhf']- 0.8*SeriesAVG.loc[x,'Qcf']
            if surplus <= 0:
                storage = storage + (-surplus)
                SeriesAVG.loc[x,'Qhf'] = 0
            elif surplus > 0:
                SeriesAVG.loc[x,'Qhf'] = surplus - storage
                if SeriesAVG.loc[x,'Qhf'] <= 0:
                    storage = -SeriesAVG.loc[x,'Qhf']
                    SeriesAVG.loc[x,'Qhf'] = 0
                if SeriesAVG.loc[x,'Qhf'] > 0:
                    storage = 0
                    
        #EmaxsysQhc = (SeriesAVG['Qhf']-SeriesAVG['Qcf']).max()
        EmaxsysQhc = (SeriesAVG['Qhf']).max()
        
        Factors.loc[r-1,'DF_Qh'] = EmaxsysQhc/EmaxsysQh
        Factors.loc[r-1,'ID'] = str(r)    
    Factors.to_excel(r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+scenario+'\\'+'Diversity_anergy.xls')

# <codecell>

Factors.to_excel(r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+scenario+'\\'+'Diversity_anergy.xls')

# <codecell>

EmaxsysQh

# <codecell>

EmaxsysQhc - EmaxsysQh

# <codecell>

EmaxsysQh

# <codecell>

EmaxsysQhc

# <codecell>

EmaxsysQhc - EmaxsysQh

# <codecell>


