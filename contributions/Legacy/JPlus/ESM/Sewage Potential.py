# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import arcpy
import pandas as pd
import os, sys
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import ESMFunctions as ESM
import numpy as np
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("Network")

# <headingcell level=4>

# ###VARIABLES

# <codecell>

#list of inputs
Zone_of_study = 4
Scenario = 'UC' #List of scenarios to evaluate the potentials
Length_HEX_available = 120#   120:CAMP, 210:HEB  #measured from arcpmaps
locationData = r'C:\Arcgis\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)
locationFinal = r'C:\Arcgis\ESMdata\DataFinal\SW'+'\\'+Scenario+'\\'

# <codecell>

#locations
Database = r'C:\Arcgis\Network.gdb'
temporal = r'c:\Arcgis\Network.gdb\temp' #location of temptemporal2ral files inside the database
temporal2 = r'c:\Arcgis\temp' #location of temptemporal2ral files inside the database

# <headingcell level=4>

# PROCESS

# <codecell>

if Scenario == "BAU" or Scenario =="CAMP" or Scenario =="SQ":
    names = pd.read_csv(locationFinal+'\\'+"names_ingrid.csv").Name
else:
    CQ_names =  pd.read_csv(locationData+'\\'+'Total.csv')
    names = CQ_names.Name

# <codecell>

# Import files with time series of hotwater consumption, temperature, cold water consumption.
SW_ratio = 0.95 #ratio of waste water to fresh water production.
width_HEX = 0.40 # in m
Vel_flow = 3 #in m/s
min_flow = 9# in lps
tmin = 8 # tmin of extraction
h0 = 1.5 # kW/m2K # heat trasnfer coefficient/
Cp = 4.1618 # specific heat of water.
AT_HEX = 5
ATmin = 2

# <codecell>

mcpwaste = []
twaste = []
mXt = []
counter = 0
for x in names:
    building = pd.read_csv(locationData+'\\'+x+'.csv')
    m, t = np.vectorize(ESM.calc_Sewagetemperature)(building.Qwwf,building.Qww,building.tsww,building.trww,building.totwater,building.mcpww,Cp,SW_ratio)
    mcpwaste.append(m)
    twaste.append(t)
    mXt.append(m*t)
    counter = counter +1
mcpwaste_zone = np.sum(mcpwaste, axis =0) 
twaste_zone = np.sum(mXt, axis =0)/mcpwaste_zone
twaste_zone = twaste_zone.copy() - twaste_zone.copy()*0.20 # lossess in the grid

# <codecell>

reload(ESM)
Q_source, t_source, t_out, tin_e, tout_e  = np.vectorize(ESM.calc_sewageheat)(mcpwaste_zone,twaste_zone,width_HEX,Vel_flow,Cp,h0,min_flow,Length_HEX_available,tmin,AT_HEX,ATmin)
SW_gen = locationFinal+'//'+'SWP'+'.csv'
pd.DataFrame({"Qsw_kW":Q_source, "ts_C":t_source, "tout_sw_C":t_out, "tin_sw_C":twaste_zone,"tout_HP_C":tout_e, "tin_HP_C":tin_e}).to_csv(SW_gen, index=False, float_format='%.3f')

print "done!"
# <codecell>

#%matplotlib inline
#import matplotlib.pyplot as plt
#
## <codecell>
#
#plt.plot(mcpwaste_zone/4.18)
#
## <codecell>
#
#plt.plot(t_source[900:1000])
#plt.plot(twaste_zone[900:1000])
#plt.plot(tout_e[900:1000])
#plt.plot(tin_e[900:1000])
#
## <codecell>
#
#plt.plot(t_source[10:12]), plt.legend("t_source")
#plt.plot(twaste_zone[10:12]), plt.legend("t_s")
#plt.plot(tout_e[10:12]), plt.legend("t_source")
#plt.plot(tin_e[10:12]), plt.legend("t_source")
#
## <codecell>
#
#plt.plot(t_source), plt.legend("t_source")
#
## <codecell>
#
##FORGET THIS: THIS WAS DONE FOR THE PAPER OF RESILIENCE TO GET ALL DATA TOGETHER INTO ENERGY PRO
#
#CQ_names =  pd.read_csv(locationData+'\\'+'Total.csv')
#names = CQ_names.Name
#Qh = []
#Qc = []
#Ef = []
#for x in names[5:6]:
#    building = pd.read_csv(locationData+'\\'+x+'.csv')
#    Q = building.Qwwf+building.Qhpf+building.Qhsf
#    Qh.append(Q)
#    Qf = building.Qcdataf+building.Qcsf+building.Qcpf+building.Qcicef
#    Qc.append(Qf)
#    E = building.Ef
#    Ef.append(E)
#Qh_zone = np.sum(Qh, axis =0)/1000 
#Qc_zone = np.sum(Qc, axis =0)/1000 
#Ef_zone = np.sum(Ef, axis =0)/1000 
#
## <codecell>
#
#date = pd.DataFrame(pd.date_range('1/1/2015', periods=8760, freq='H'))
#out = locationData+'\\'+'Series.csv'
#pd.DataFrame({"#":range(1,8761),"Date":date[0], "HD1 [MW]":Qh_zone,"Date1":date[0], "CD1 [MW]":Qc_zone,"Date2":date[0],  "ED1 [MW]":Ef_zone}).to_csv(out, index=False)
#
## <codecell>
#
#names[:4]
#
## <codecell>


