# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #  Deterministic Energy Demand Model 
# ###INTRODUCTION
# 
# This Routine calculates the thermal, Cooling and electrical hourly dem in buildings
# the model is developed under the standard EN 13790:2007, 'SIMPLIFIED HOURLY MODEL' for heating and cooling loads,
# Whereas Electrical loads are assumed to be distributed during the year according to the Standard SIA 2024 for different categories of use.
# 
# ### The Input
# 
# - DataradiationLocation= A .csv dataradiation file from the Chapter 1. Radiation Model.
# - TimeSeries = a .excell to compute the profiles of occupancy.
# - Buildings - a.shp (multi-polygon) file or database describing the properties of the community to analyze
#             in the case of measured data, it is more easy to receive this file from Excell.
# - *Requierements
# 
# ###The Output
# 
# 
# ###Requierements
# 
# For every building of the Community Analyzed an excelfile containing:
# 
# - U values from Roof, Walls, Basement, and Windows,
# - Type and location of Shading. (Louvers, Rollo, Venetian Blinds, Courtain), (Interior, Exterior)
# - Windows/Wall ratio, 
# - Type of construction(Light, Heavy,Medium)
# 
# 

# <markdowncell>

# ##MODULES

# <codecell>

import pandas as pd
from pylab import *
import matplotlib as plt
import numpy as np

# <codecell>

import arcpy

# <codecell>

import sys, os
sys.path.append("C:\Users\Jimeno Fonseca\Documents\Console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 

# <markdowncell>

# ##VARIABLES

# <codecell>

# Set of constants according to EN 13790
pa_ca = 1200  # Air constant J/m3K
his = 3.45 #heat transfer coefficient between air and the surfacein W/(m2K)
hms = 9.1 # Heat transfer coeddicient between nodes m and s in W/m2K
g_gl = 0.9*0.75 # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows to be double glazing (0.75)
F_f = 0.3 # Frame area faction coefficient
Fr = 0.5 #Thermal Radiation to the sky
delta_t_er = 11 # Difference between external air and the apparent sky temperature
e =  0.85 # emissivity for thermal radiation of the external surface considering Glazed part of windows.
S = 0.0000000567  # Stefan-Boltzmann constant in W/(m2K4)
hr = 4 * e* S*(delta_t_er+273)**3 # external radiative coeficcien in Wm2K
Rse = 0.04 # Surface thermal resistance # reduction factor of solar transmittance when shading is operating for a more precise idea do the analysis per Building.
# Set of estimated constants
Z = 3 # height of basement for every building in m
Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1

# <codecell>

CQ =r'c:\ArcGIS\EDM.gdb\Communities\CityQuarter_3'
CQ_name = 'CityQuarter_3'
DataCQ = pd.ExcelFile('c:\ArcGIS\EDMdata\Measured'+'\\'+CQ_name+'\\'+'BuildingProperties.xls') # Location of the data of the CQ to run
CQProperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements

# <codecell>

WeatherData = pd.ExcelFile('C:\ArcGIS\EDMdata\Weatherdata\Temp_2009_20102.xls') # Location of temperature data
Temperature_Sh = pd.ExcelFile.parse(WeatherData, 'Values') # properties of buildings, Table with all requierements

# <codecell>

Schedules = pd.ExcelFile('C:\ArcGIS\EDMdata\Statistical\Schedules.xls')
ADMIN = pd.ExcelFile.parse(Schedules, 'ADMIN') 
INDUS = pd.ExcelFile.parse(Schedules, 'INDUS') 
REST = pd.ExcelFile.parse(Schedules, 'INDUS') 

# <codecell>

DataradiationLocation = r'c:\ArcGIS\temp'+'\\'+CQ_name+'\\'+'radiation'+'\\'+'RadiationYear.csv'

# <codecell>

temporal1 = r'c:\ArcGIS\temp'

# <markdowncell>

# ##FUNCTIONS

# <markdowncell>

# Mass area and coefficients of internal mass capacity according to values of  SIA 2024

# <codecell>

def CmFunction (x): 
    if x == 'Medium':
        return 165000
    elif x == 'Heavy':
        return 300000
    elif x == 'Light':
        return 110000
    else:
        return 165000

# <codecell>

def AmFunction (x): 
    if x == 'Medium':
        return 2.5
    elif x == 'Heavy':
        return 3.2
    elif x == 'Light':
        return 2.5
    else:
        return 2.5

# <markdowncell>

# It calculates the rediction factor of shading due to type of shading

# <codecell>

def Calc_Rf_sh (ShadingPosition,ShadingType):
    d ={'Type':['Louvres','Rollo', 'Venetian Blinds', 'Courtain'],'ValueIN':[0.2,0.2,0.3,0.77],'ValueOUT':[0.08,0.08,0.15,0.57]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Exterior':
            return ValuesRf_Table.loc[row,'ValueOUT']
        elif ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 'Interior':
            return ValuesRf_Table.loc[row,'ValueIN']
        else:
            return 1

# <markdowncell>

# Shading Factors

# <codecell>

def calc_Fhor(angle,Sh,Idir,Iglo):
    if angle < Sh:
        if Iglo == 0:
            return 0
        else:
            return 1 - Idir / Iglo
    else:
        return 1

# <codecell>

def calc_Fsh_gl(Iwindows,Aw, g_gl,Rf_sh):
    if Iwindows/Aw > 300:
        Fsh_with = 1
        return ((1-Fsh_with)*g_gl+Fsh_with*g_gl*Rf_sh)/g_gl
    else:
        return 1

# <markdowncell>

# 3.4 Definition of profile of occupancy

# <codecell>

def calc_Type(ADMIN, INDUS, REST, AllProperties, i):
    ADMIN['Ve'] = AllProperties.loc[i,'ADMIN'] * ADMIN['Ve'] + AllProperties.loc[i,'REST'] * REST['Ve'] + AllProperties.loc[i,'INDUS'] * INDUS['Ve']
    ADMIN['I_int']= AllProperties.loc[i,'ADMIN'] * ADMIN['I_int'] + AllProperties.loc[i,'REST'] * REST['I_int'] + AllProperties.loc[i,'INDUS'] * INDUS['I_int']
    if AllProperties.loc[i,'ADMIN'] >= 0.6:
        ADMIN['tintH_set'] = ADMIN['tintH_set']
        ADMIN['tintC_set'] = ADMIN['tintC_set']
    elif AllProperties.loc[i,'REST']>=0.6:
        ADMIN['tintH_set'] = REST['tintH_set']
        ADMIN['tintC_set'] = REST['tintC_set']
    elif AllProperties.loc[i,'INDUS']>=0.6:
        ADMIN['tintH_set'] = INDUS['tintH_set']        
        ADMIN['tintC_set'] = INDUS['tintC_set']       
    
    return ADMIN

# <markdowncell>

# Hourly thermal transmission coefficients

# <codecell>

def calc_Htr(Hve, Htr_is, Htr_ms, Htr_w):
    Htr_1 = 1/(1/Hve+1/Htr_is)
    Htr_2 = Htr_1+Htr_w
    Htr_3 = 1/(1/Htr_2+1/Htr_ms)
    Coefficients = [Htr_1,Htr_2,Htr_3]
    return Coefficients

# <markdowncell>

# Calculation Heating and Cooling loads

# <codecell>

def calc_TL(tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3, I_st, Hve, Htr_w, I_ia, I_m, Cm, Ac, IC, IH):
    # Case 1 IHC_nd = 0
    IHC_nd = 0
    IC_nd_ac = 0
    IH_nd_ac = 0
    Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2
    tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
    tm = (tm_t+tm_t0)/2
    ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)  
    tair0 = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
    top0 = 0.3*tair0+0.7*ts
    if tintH_set <= tair0 <= tintC_set:
        tair_ac = tair0 
        top_ac = top0
        IHC_nd_ac = 0
        IH_nd_ac = IHC_nd_ac
        IC_nd_ac = IHC_nd_ac
    else:
        if tair0 > tintC_set and tair0 > tintH_set:
            tair_set = tintC_set
        elif tair0 < tintH_set and tair0 < tintC_set:
            tair_set = tintH_set
        
        # Case 2 IHC_nd = 10 * Ac  
        IHC_nd = IHC_nd_10 = 10*Ac
        Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2
        tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
        tm = (tm_t+tm_t0)/2
        ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)  
        tair10 = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
        top10 = 0.3*tair10+0.7*ts
        IHC_nd_un =  IHC_nd_10*(tair_set - tair0)/(tair10-tair0)
        IC_max = IC*Ac
        IH_max = IH*Ac
        if  IC_max < IHC_nd_un < IH_max:
            tair_ac = tair_set 
            top_ac = 0.3*tair_ac+0.7*te_t
            IHC_nd_ac = IHC_nd_un 
        else:
            if IHC_nd_un > 0:
                IHC_nd_ac = IH_max
            else:
                IHC_nd_ac = IC_max
            # Case 3 when the maximum power is exceeded
            Im_tot = I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd_ac)/Hve)+ te_t))/Htr_2
            tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
            tm = (tm_t+tm_t0)/2
            ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd_ac)/Hve))/(Htr_ms+Htr_w+Htr_1)  
            tair_ac = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
            top_ac = 0.3*tair_ac+0.7*ts
    # Results
        if IHC_nd_ac >0:
            IH_nd_ac = IHC_nd_ac
        else:
            IC_nd_ac = IHC_nd_ac
    
    Results = [tm_t, tair_ac ,top_ac, IH_nd_ac, IC_nd_ac]
    return Results

# <markdowncell>

# ##PROCESS

# <markdowncell>

# Import RadiationFile and Properties of the shapefiles

# <codecell>

Radiation_Shading = pd.read_csv(DataradiationLocation)

# <codecell>

OutTable = 'CQshape3.dbf'
arcpy.TableToTable_conversion(CQ, temporal1, OutTable)
CQShape_properties = dbf2df(temporal1+'\\'+OutTable, )

# <markdowncell>

# ###Areas

# <markdowncell>

# 1.1 Vertical Areas above ground 

# <codecell>

Radiation_Shading['Awall'] = Radiation_Shading['Shape_Leng']*Radiation_Shading['Freeheight']*Radiation_Shading['FactorShade'] #get the area of each wall in the buildings

# <codecell>

PivotTable = pd.pivot_table(Radiation_Shading,rows='Name_1',values='Awall',aggfunc=np.sum) #get the area of walls in the whole buildings
PivotTable2 = pd.DataFrame(PivotTable)

# <codecell>

CQproperties2 = pd.merge(PivotTable2,CQProperties, left_index=True,right_on='Name')
CQproperties2['Aw'] = CQproperties2['Awall']*CQproperties2['fwindow'] # Finally get the Area of windows 
CQproperties2['Aop_sup'] = CQproperties2['Awall'] - CQproperties2['Aw'] #....and Opaque areas

# <markdowncell>

# 1.2 Vertical Areas Below ground

# <codecell>

# Join both properties files (Shape and areas)
AllProperties = pd.merge(CQproperties2,CQShape_properties,on='Name')

# <codecell>

AllProperties['Aop_bel'] = Z*AllProperties['Shape_Leng']+AllProperties['Shape_Area']   # Opague areas in m2 below ground including floor

# <markdowncell>

# 1.3 Total Area, Energy area and and Thermal Mass area

# <codecell>

AllProperties['Atot'] = AllProperties['Aop_sup']+AllProperties['Aop_bel']+AllProperties['Aw']+AllProperties['Shape_Area'] # Total area of the building envelope m2, it is considered the roof to be flat
AllProperties['Af'] = AllProperties['Shape_Area']*AllProperties['Floors_x']*AllProperties['Hs_x']
AllProperties['Am'] = AllProperties.Construction.apply(lambda x:AmFunction(x))*AllProperties['Af'] # Effective mass area in m2

# <markdowncell>

# ###Solar Radiation Load in windoes

# <markdowncell>

# 4.1. Import Radiation table and compute the Irradiation in W in every building's surface

# <codecell>

Radiation_Shading2 = pd.read_csv(DataradiationLocation)
Columns = 8761
for Column in range(1, Columns):
    Radiation_Shading2['T'+str(Column)] = Radiation_Shading2['T'+str(Column)]*Radiation_Shading2['Shape_Leng']*Radiation_Shading2['Freeheight']*Radiation_Shading2['FactorShade'] #transform all the points of solar radiation into Wh

# <markdowncell>

# 4.2. Do pivot table to sum up the irradiation in every surface to the building and merge the result with the table allProperties

# <codecell>

PivotTable3 = pd.pivot_table(Radiation_Shading2,rows='Name_1',margins='Add all row')
RadiationLoad = pd.DataFrame(PivotTable3)

# <codecell>

Solar = AllProperties.merge(RadiationLoad, left_on='Name',right_index=True)

# <markdowncell>

# 4.3 final step multiply the total irradiation in the building per the percentage of Window/wall area to get the result

# <codecell>

Columns = 8761
for Column in range(1, Columns):
    Solar['T'+str(Column)] = Solar['T'+str(Column)]*Solar['fwindow']

# <markdowncell>

# ###Steady-state Thermal transmittance coefficients and Internal heat Capacity

# <codecell>

AllProperties ['Htr_w'] = AllProperties['Aw']*AllProperties['Uwindow']  # Thermal transmission coefficient for windows and glazing. in W/K
AllProperties ['HD'] = AllProperties['Aop_sup']*AllProperties['Uwall']+AllProperties['Shape_Area']*AllProperties['Uroof']  # Direct Thermal transmission coefficient to the external environment in W/K
AllProperties ['Hg'] = Bf*AllProperties ['Aop_bel']*AllProperties['Uground'] # stady-state Thermal transmission coeffcient to the ground. in W/K
AllProperties ['Htr_op'] = AllProperties ['Hg']+ AllProperties ['HD']
AllProperties ['Htr_ms'] = hms*AllProperties ['Am'] # Coupling conduntance 1 in W/K
AllProperties ['Htr_em'] = 1/(1/AllProperties['Htr_op']-1/ AllProperties['Htr_ms']) # Coupling conduntance 2 in W/K 
AllProperties ['Htr_is'] = his*AllProperties ['Atot']
AllProperties['Cm'] = AllProperties.Construction.apply(lambda x:CmFunction(x))*AllProperties['Af'] # Internal heat capacity in J/K

# <markdowncell>

# Create Labels in data framte to iterate

# <codecell>

Columns = ['IH_nd_ac','IC_nd_ac','Fsh_gl','Htr_1','Htr_2','Htr_3','tm_t','tair_ac','top_ac','IHC_nd_ac', 'Asol', 'I_sol']
for Label in Columns:
    ADMIN[Label] = 0
    INDUS[Label] = 0
    REST[Label] = 0
AllProperties['Qh'] = 0
AllProperties['Qc'] = 0

# <markdowncell>

# Calculation of Thermal loads

# <codecell>

Num_Hours = ADMIN.DATE.count()
Num_Buildings = AllProperties.Name.count()
for i in range(Num_Buildings):
#i =0
    Name = AllProperties.loc[i,'Name']
    # Determination of Profile of occupancy to use
    Occupancy = calc_Type(ADMIN, INDUS, REST, AllProperties,i)
    # Determination of Hourly Thermal transmission coefficient due to Ventilation in W/K
    Occupancy['Hve'] =  pa_ca*Occupancy['Ve']* AllProperties.loc[i,'Af']/3600
    #Determination of Heat Flows for internal loads in W
    Occupancy['I_ia'] = 0.5*Occupancy['I_int']*AllProperties.loc[i,'Af']
    # Calculation of effecive solar area of surfaces in m2, opaque areas are not considered, reduction factor of overhangs is not included. Fov =0
    for hour in range(Num_Hours):

        # Calculation Shading factor per hour due to operation of external shadings, 1 when I > 300 W/m2
        Rf_sh = Calc_Rf_sh(AllProperties.loc[i,'Shading_position'],AllProperties.loc[i,'Shading_Type'])
        Occupancy.loc[hour,'Fsh_gl'] = calc_Fsh_gl(Solar.loc[i,'T'+str(hour+1)],AllProperties.loc[i,'Aw'], g_gl,Rf_sh)

        # Calculation of solar efective area per hour in m2  
        Occupancy.loc[hour,'Asol'] = Occupancy.loc[hour,'Fsh_gl'] * g_gl*(1-F_f)*AllProperties.loc[i,'Aw']
    
        # Calculation of Solar gains in each facade in W it is neglected the extraflow of radiation from the surface to the exterior Fr_k*Ir_k = 0 as well as gains in opaque surfaces
        Occupancy.loc[hour,'I_sol'] = Occupancy.loc[hour,'Asol']*(Solar.loc[i,'T'+str(hour+1)]/AllProperties.loc[i,'Aw'])#-Fr*Properties.loc[i,'Aw_N']*Properties.loc[i,'Uwindow']*delta_t_er*hr*Rse
        
        # Determination of Hourly thermal transmission coefficients for Determination of operation air temperatures in W/K
        Coefficients = calc_Htr(Occupancy.loc[hour,'Hve'], AllProperties.loc[i,'Htr_is'], AllProperties.loc[i,'Htr_ms'], AllProperties.loc[i,'Htr_w'])
        Occupancy.loc[hour,'Htr_1'] = Coefficients[0]
        Occupancy.loc[hour,'Htr_2'] = Coefficients[1]
        Occupancy.loc[hour,'Htr_3'] = Coefficients[2]
  
    # Determination of Heat Flows for internal heat sources
    Occupancy['I_m'] = (AllProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])*(Occupancy['I_ia']+Occupancy['I_sol'])
    Occupancy['I_st'] = (1-(ALlProperties.loc[i,'Am']/AllProperties.loc[i,'Atot'])-(AllProperties.loc[i,'Htr_w']/(9.1*AllProperties.loc[i,'Atot'])))*(Occupancy['I_ia']+Occupancy['I_sol'])
    # Seed for calculation
    Occupancy.loc[0,'tm_t'] = Occupancy.loc[0,'te']
    for j in range(1,Num_Hours):  
    # determination of Temperatures in the nodes for every Hour in C when I_HC,nd is equal to 0
        Results = calc_TL(Occupancy.loc[j-1,'tm_t'], Occupancy.loc[j,'te'], Occupancy.loc[j,'tintH_set'],Occupancy.loc[j,'tintC_set'],Properties.loc[i,'Htr_em'],Properties.loc[i,'Htr_ms'], Properties.loc[i,'Htr_is'],Occupancy.loc[j,'Htr_1'], Occupancy.loc[j,'Htr_2'], Occupancy.loc[j,'Htr_3'], Occupancy.loc[j,'I_st'], Occupancy.loc[j,'Hve'], Properties.loc[i,'Htr_w'], Occupancy.loc[j,'I_ia'], Occupancy.loc[j,'I_m'], Properties.loc[i,'Cm'], Properties.loc[i,'Ac'], Properties.loc[i,'IC_max'], Properties.loc[i,'IH_max'])
        Occupancy.loc[j,'tm_t'] = Results[0]
        Occupancy.loc[j,'tair_ac'] = Results[1]
        Occupancy.loc[j,'top_ac'] = Results[2]
        Occupancy.loc[j,'IH_nd_ac'] = Results[3]
        Occupancy.loc[j,'IC_nd_ac'] = Results[4]
    #  RESULTS
    Result_Thermalloads = pd.DataFrame(Occupancy,columns = ['IH_nd_ac','IC_nd_ac', 'top_ac','tair_ac','tm_t','te','Hour'])
    Result_Int_Ext_loads = pd.DataFrame(Occupancy,columns = ['Hour','I_sol','I_m', 'I_ia','I_st','Hour'])
    Result_Coefficients = pd.DataFrame(Occupancy,columns = ['Hve','Htr_1','Htr_2','Htr_3',])
    Total = Result_Thermalloads.sum(axis=0)/1000000
    AllProperties.loc[i,'Qh'] = Total[0] # total end use heatingload per year in MWh
    ALLProperties.loc[i,'Qc'] = -Total[1] # total end use cooling load per year in MWh
    # EXPORT LOADS
    Result_Thermalloads.to_csv('c:\ArcGIS\EDMdata\DataFinal\CityQuarter_3\TL_'+Name+'.csv')
    Result_Int_Ext_loads.to_csv('c:\ArcGIS\EDMdata\DataFinal\CityQuarter_3\IE_'+Name+'.csv')
    Result_Coefficients.to_csv('c:\ArcGIS\EDMdata\DataFinal\CityQuarter_3\CE_'+Name+'.csv')
    ALLProperties.to_csv('c:\ArcGIS\EDMdata\DataFinal\CityQuarter_3\Totals.csv')

# <markdowncell>

# #VISUALIZATION

# <markdowncell>

# Import Results to visualize Series of heating and Cooling loads

# <codecell>

Bau_2h = pd.read_csv('c:\ArcGIS\EDM\DataFinal\TL Status Quo\TL_Bau 02h.csv')
Bau_2h.plot(subplots=True, figsize = (6,20));plt.legend(loc="best");plt.axis([8740,8760,0,25000])

# <codecell>

Bau_02 = pd.read_csv('c:\ArcGIS\EDM\DataFinal\TL Status Quo\TL_Bau 02.csv')
Bau_02.plot(subplots=True, figsize = (6,20));plt.legend(loc="best");plt.axis([8740,8760,0,25000])

# <codecell>

Properties['Qh']

# <codecell>


