# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #  Analytical Energy Demand Model (A-EDM)
# ###INTRODUCTION
# 
# This Routine calculates the thermal, Cooling and electrical hourly demand in buildings
# the model is developed under the standard EN 13790:2007, 'SIMPLIFIED HOURLY MODEL' for heating and cooling loads,
# Whereas Electrical loads are assumed to be distributed during the year according to the Standard SIA 2024 for different categories of use.
# 
# it calculates the next values in MWh/year and dynamics:
# 
# - Qhsf: final space heating consumption
# - Qcsf: final space cooling consumption
# - Qwwf: final space cooling consumption
# - Ealf: final electricity consumption due to appliances and lighting

# <markdowncell>

# ##MODULES

# <codecell>

import pandas as pd
import os, sys
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
import numpy as np

# <markdowncell>

# ##VARIABLES

# <codecell>

case_study = 'ArcGIS' #ArcGIS for inducity and Zernez for Zernez

# <codecell>

Scenario = 'SQ'; Zone_of_study = 1
Zone_calc = 1
Zone = 'Zone_'+str(Zone_calc)

# <codecell>

# do this if no difference between server room and cooling room loads has to be done
Servers=0
Coolingroom=0

# <codecell>

WeatherData = pd.ExcelFile('C:\Zernez\EDMdata\Weatherdata\Temp_Design.xls')
Temp = pd.ExcelFile.parse(WeatherData, 'Values_hour',convert_float=True)
Seasonhours = [3216,6192] # hours of start and end of cooling season
T_ext = np.array(Temp.te)
RH_ext = np.array(Temp.RH)
# the maximum and minimum outside temperatures
T_ext_max = T_ext.max()
T_ext_min = T_ext.min()

# <codecell>

# it lasts 10 sec to load!
Schedules = pd.ExcelFile('C:\Zernez\EDMdata\Statistical\Archetypes_schedules.xls')
Profiles_names = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU','EDU','CR','HEALTH','SPORT',
            'SWIM','PUBLIC','SUPER','ICE','HOT']
Profiles= list(range(len(Profiles_names)))
rows = len(Profiles_names)
for row in range(rows):
    Profiles[row] = pd.ExcelFile.parse(Schedules, Profiles_names[row],convert_float=True)
    Profiles[row]['tintH_set'],Profiles[row]['tintC_set']  = np.vectorize(EDM.calc_fill_local_Text)(T_ext,Profiles[row]['tintH_set'].copy(),
                                                                                                    Profiles[row]['tintC_set'].copy(),T_ext_max)
if Servers == 0:
    Profiles[1] = Profiles[0]
if Coolingroom == 0:
    Profiles[10] = Profiles[15]

# <codecell>

locationtemp1 = r'c:\Zernez\temp'

# <codecell>

if Zone_calc != Zone_of_study:
    CQ = r'c:\Zernez\EDM.gdb'+'\\'+'Surroundings'+'\\'+Zone
    DataCQ = pd.ExcelFile('c:\Zernez\EDMdata\DataFinal\SEDM'+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run
    CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements
    RadiationFile = 'c:\Zernez\EDMdata\DataFinal\RM'+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Radiation_faces'+'\\'+'RadiationYearFinal.csv'
    locationFinal = r'c:\Zernez\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+'Surroundings'+'\\'+Zone
else:
    RadiationFile = 'c:\Zernez\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+Zone+'\\'+'Radiation_faces'+'\\'+'RadiationYearFinal.csv'
    CQ = r'c:\Zernez\EDM.gdb'+'\\'+Scenario+'\\'+Scenario+Zone
    DataCQ = pd.ExcelFile('c:\Zernez\EDMdata\DataFinal\SEDM'+'\\'+Scenario+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run    
    CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements
    locationFinal = r'c:\Zernez\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+Zone
if Scenario == "SQ":
    DataCQ = pd.ExcelFile('c:\Zernez\EDMdata\Measured'+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run    
    CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements    

# <markdowncell>

# ##PROCESS

# <markdowncell>

# Calculate properties of buildings such as areas and thermal transmittance coefficients

# <codecell>

# it lasts 5 sec to load!
AllProperties = EDM.CalcProperties(CQ, CQproperties, RadiationFile, locationtemp1)

# <markdowncell>

# Incident radiation in areas exposed to solar radiation

# <codecell>

# it lasts 22 sec to load!
Solar = EDM.CalcIncidentRadiation(AllProperties, RadiationFile)

# <markdowncell>

# ###2. Calculation of NET-Thermal loads - Simplified hourly dynamic method - EN 13790:2007: It includes determination of losses of emission and control and distribution, EN15316:2008

# <codecell>

#constant variables
# CONSTANT VALUES
g_gl = 0.9*0.75 # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows to be double glazing (0.75)
F_f = 0.3 # Frame area faction coefficient
Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1
D = 20 #in mm the diameter of the pipe to calculate losses
hf = 3 # average height per floor in m
Pwater = 998 # water density kg/m3
PaCa = 1200  # Air constant J/m3K 
Cpw= 4.184 # heat capacity of water in kJ/kgK
Flowtap = 0.036 # in m3/min ==  12 l/min during 3 min every tap opening 
# constants
deltaP_l = 0.1 #delta of pressure
fsr = 0.3 # factor for pressure calculation
#constant values for HVAC
nrec_N = 0.75  #possilbe recovery
C1 = 0.054 # assumed a flat plate heat exchanger
Vmax = 3 # maximum estimated flow i m3/s
Pair = 1.2 #kg/m3
Cpv = 1.859 # in KJ/kgK specific heat capacity of water vapor
Cpa = 1.008 # in KJ/kgK specific heat capacity of air
lvapor = 2257 #kJ/kg

# <codecell>

buildings = AllProperties.Name.count()
for building in range(buildings):
    result = EDM.CalcThermalLoads(building, AllProperties.ix[building], Solar.ix[building], locationFinal, Profiles,Profiles_names,
                                  T_ext,Seasonhours,T_ext_max, RH_ext, T_ext_min,g_gl,F_f,Bf,D,hf,Pwater,PaCa,Cpw, Flowtap,
                                  deltaP_l, fsr,nrec_N,C1,Vmax,Pair,Cpv,Cpa,lvapor, servers=0,coolingroom=0)
    print 'complete building '+ str(building) + 'of '+ str(buildings)

# <codecell>

name = AllProperties.Name[0]
dataframe = pd.read_csv(locationFinal+'\\'+name+'T'+'.csv')
for x in AllProperties.Name[1:]:
    dataframe2 = pd.read_csv(locationFinal+'\\'+x+'T'+'.csv')
    dataframe = dataframe.append(dataframe2,ignore_index=True)
dataframe.to_csv(locationFinal+'\\'+'Total.csv')

# <codecell>

%reset

# <codecell>

for x in range(5,21):
    Zone = 'ZONE_'+str(x)
    if x != Zone_of_study:
        CQ = r'c:\ArcGIS\EDM.gdb'+'\\'+'Surroundings'+'\\'+Zone
        DataCQ = pd.ExcelFile('c:\ArcGIS\EDMdata\DataFinal\SEDM'+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run
        CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements
        RadiationFile = 'c:\ArcGIS\EDMdata\DataFinal\RM'+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Radiation_faces'+'\\'+'RadiationYearFinal.csv'
        locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+'Surroundings'+'\\'+Zone
    else:
        RadiationFile = 'c:\ArcGIS\EDMdata\DataFinal\RM'+'\\'+Scenario+'\\'+Zone+'\\'+'Radiation_faces'+'\\'+'RadiationYearFinal.csv'
        CQ = r'c:\ArcGIS\EDM.gdb'+'\\'+Scenario+'\\'+Scenario+Zone
        DataCQ = pd.ExcelFile('c:\ArcGIS\EDMdata\DataFinal\SEDM'+'\\'+Scenario+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run    
        CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements
        locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+Zone
    
    
    AllProperties = EDM.CalcProperties(CQ, CQproperties, RadiationFile, locationtemp1)
    Solar = EDM.CalcIncidentRadiation(AllProperties, RadiationFile)
    
    for building in range(AllProperties.Name.count()):
        result = EDM.CalcThermalLoads(building, AllProperties.ix[building], Solar.ix[building], locationFinal, Profiles,Profiles_names,
                                      T_ext,Seasonhours,T_ext_max, RH_ext, T_ext_min,g_gl,F_f,Bf,D,hf,Pwater,PaCa,Cpw, Flowtap,
                                      deltaP_l, fsr,nrec_N,C1,Vmax,Pair,Cpv,Cpa,lvapor, servers=0,coolingroom=0)
    print 'complete'
    
    name = AllProperties.Name[0]
    dataframe = pd.read_csv(locationFinal+'\\'+name+'T'+'.csv')
    for x in AllProperties.Name[1:]:
        dataframe2 = pd.read_csv(locationFinal+'\\'+x+'T'+'.csv')
        dataframe = dataframe.append(dataframe2,ignore_index=True)
    dataframe.to_csv(locationFinal+'\\'+'Total.csv')

# <codecell>


