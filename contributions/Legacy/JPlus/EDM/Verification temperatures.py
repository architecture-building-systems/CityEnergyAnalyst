# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from __future__ import division
import sys,os
import pandas as pd
import datetime
import jdcal
import numpy as np
import math
import sympy as sp
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
import scipy
import scipy.optimize

# <codecell>

import matplotlib.pyplot as plt

# <codecell>

DATA = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\DEDM\StatusQuo\CityQuarter_3\Bau H.csv')
TOTAL = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\DEDM\StatusQuo\CityQuarter_3\Bau HT.csv')

# <codecell>

DATA['trc'].plot(); #plt.axis([0,150,0,70])
DATA['tsc'].plot(); #plt.axis([0,150,0,70])

# <codecell>

DATA['Qcsf'].plot(); #plt.axis([0,150,0,70])
DATA['Qhsf'].plot(); #plt.axis([0,150,0,70])
DATA['Qwwf'].plot(); #plt.axis([0,150,0,70])
DATA['Ealf'].plot(); #plt.axis([0,150,0,70])

# <codecell>

DATA['tsh'].plot(); #plt.axis([0,150,0,70])
DATA['trh'].plot(); #plt.axis([0,150,0,70])

# <codecell>

print TOTAL

# <markdowncell>

# Variables

# <codecell>

#FOR HYDRONIC SYSTEMS
nh = 0.33
tsh0 = TOTALS.tsh0[0]
trh0 = TOTALS.trh0[0]
tsh0 = tsh0 + 273
trh0 = trh0 + 273
Qh0 = Qhsmax = DATA['Qhsf'].max()
tair0 = 20+273
mCw0 = Qh0/(tsh0-trh0) 
LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
k1 = 1/mCw0
def fh(x): 
    Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
    return Eq
rows = DATA.Qhsf.count()
for row in range(rows):
    if DATA.loc[row,'Qhsf'] != 0:
        k2 = DATA.loc[row,'Qhsf']*k1
        tair = DATA.loc[row,'tair']+ 273
        DATA.loc[row,'trh'] = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        DATA.loc[row,'tsh'] = DATA.loc[row,'trh'] + k2

# <codecell>

k2,tsh0-273,trh0-273

# <codecell>

DATA['tsh'].plot(); plt.axis([0,150,0,70])
DATA['trh'].plot(); plt.axis([0,150,0,70])

# <codecell>

DATA['Qhsf'].plot(); #plt.axis([0,150,0,3000000])

# <codecell>

# Nominal conditions
Af = 2200
tair0 = 20
Floors =1
tmean_max = tair0 + 9.6                             # according ot EN 1264, simplifying to +9 k inernal surfaces
q0 = Qh0/Af                                            
S0 = 10                                                #drop of temperature of supplied water at nominal conditions
#trh0 = tsh0 - S0
#deltaH0 = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
U0 = q0/((tmean_max-tair0)**1.1)
#U0 = Qh0/(deltaH0*Af)
deltaH0 = (Qh0/(U0*Af))

if S0/deltaH0 <= 0.5: #temperature drop of water should be in this range
    deltaV0 = deltaH0 + S0/2 
else:
    deltaV0 = deltaH0 + S0/2+(S0**2/(12*deltaH0))

tsh0 = deltaV0 + tair0
trh0 = tsh0 - S0

# Floor slab prototype
sins = 0.07
Ru = sins/0.15+0.17+0.1
R0 = 0.1+0.0093+0.045/1 # su = 0.045 it is the tickness of the slab    
# CONSTANT FLOW CONDITIONS
tu = 13 # temperature in the basement
if Floors ==1:
    mCw0 = Af*q0/(S0)*(1+R0/Ru+(tair-tu)/(q0*Ru))
else:
    Af1 = Af/Floors
    mCw0 = Af1*q0/(S0)*(1+R0/Ru+(tair-tu)/(Qh0*Ru/Af1))+((Af-Af1)*q0/(S0*4190)*(1+R0/Ru))

nh = 0.27
tsh0 = tsh0 + 273
trh0 = trh0 + 273
Qh0 = Qhsmax = DATA['Qhsf'].max()
tair0 = 20+273
LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
k1 = 1/mCw0
def fh(x): 
    Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
    return Eq
rows = DATA.Qhsf.count()
for row in range(rows):
    if DATA.loc[row,'Qhsf'] != 0:
        Q = DATA.loc[row,'Qhsf']
        k2 = DATA.loc[row,'Qhsf']*k1
        tair = DATA.loc[row,'tair']+ 273
        DATA.loc[row,'trh'] = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        DATA.loc[row,'tsh'] = DATA.loc[row,'trh'] + k2
        DATA.loc[row,'sup'] = (Q/(U0*Af))**(1/1.1)+ DATA.loc[row,'tair']

# <codecell>


# <codecell>

trh0,DATA['trh'].max(),tsh0,DATA['tsh'].max(),mCw0,S/2

# <codecell>

DATA['tsh'].plot();  plt.axis([8600,8760,0,40])
DATA['trh'].plot(); plt.axis([8600,8760,0,40])
DATA['sup'].plot(); plt.axis([8600,8760,0,40])

# <markdowncell>

# Try for cooling tabss

# <codecell>

#assuming a maximum relative humidity of 60% and 26C
# the dew point temperature is 18 degrees
tair0 = 22
tair0 = tair0 + 273
Qc0 = Qcsmax = DATA['Qcsf'].max()
qc0 = Qc0/(Af*0.5)   # 50% of the area available for heat exchange = to size of panels
tmean_min = dewP = 18
deltaC_N = 8
Sc0 = 2              # rise of temperature of supplied water at nominal conditions
delta_in_des = deltaC_N + Sc0/2
U0 = qc0/deltaC_N

tsc0 = tair0 - 273 - delta_in_des
if tsc0 <= dewP:
    tsc0 = dewP - 1
trc0 = tsc0  + Sc0

tsc0 = tsc0 + 273
trc0 = trc0 + 273

tmean_min = (tsc0+trc0)/2 # for design conditions difference room and cooling medium    
mCw0 = (qc0*Af*0.5)/(trc0-tsc0)
LMRT = (trc0-tsc0)/scipy.log((tsc0-tair0)/(trc0-tair0))
kC0 = qc0*(Af*0.5)/(LMRT)
k1 = 1/mCw0
def fc(x): 
    Eq = mCw0*k2-kC0*(k2/(scipy.log((x-k2-tair)/(x-tair))))
    return Eq
rows = DATA.Qcsf.count()
DATA.tsc = DATA.trc = 0
DATA['surfaceC']=0
for row in range(rows):
    if DATA.loc[row,'Qcsf'] != 0 and DATA.loc[row,'tair']==(tair0-273):
        Q = DATA.loc[row,'Qcsf']
        q = Q/(Af*0.5)
        k2 = Q*k1
        tair = DATA.loc[row,'tair'] + 273
        DATA.loc[row,'trc'] = scipy.optimize.newton(fc, trc0, maxiter=100,tol=0.01) - 273 
        DATA.loc[row,'tsc'] = DATA.loc[row,'trc'] - k2
        DATA.loc[row,'surfaceC'] = DATA.loc[row,'tair'] - (q/U0)

# <codecell>

tsc0-273

# <codecell>

DATA['tsc'].plot();       plt.axis([4050,4400,5,40])
DATA['trc'].plot();       plt.axis([4050,4400,5,40])
DATA['surfaceC'].plot();  plt.axis([4250,4400,5,40])
DATA['tair'].plot();  plt.axis([4250,4400,5,40])

# <codecell>

DATA['Qcsf'].plot();       plt.axis([4050,4400,5,1000000])

# <markdowncell>

# Ither try for heating tabs

# <codecell>

# Nominal conditions
Af = 2200
tair0 = 20
Floors =1
tmean_max = tair0 + 9.6                         # according ot EN 1264, simplifying to +9 k inernal surfaces
q0 = Qh0/Af                                            
S0 = 5                                                #drop of temperature of supplied water at nominal conditions
#trh0 = tsh0 - S0
#deltaH0 = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
U0 = q0/(tmean_max-tair0)
#U0 = Qh0/(deltaH0*Af)
deltaH0 = (Qh0/(U0*Af))

if S0/deltaH0 <= 0.5: #temperature drop of water should be in this range
    deltaV0 = deltaH0 + S0/2 
else:
    deltaV0 = deltaH0 + S0/2+(S0**2/(12*deltaH0))

tsh0 = deltaV0 + tair0
trh0 = tsh0 - S0
mCw0 = Af*q0/S0
rows = DATA.Qhsf.count()
DATA['surface']=0
for row in range(rows):
    if DATA.loc[row,'Qhsf'] != 0: 
        Q = DATA.loc[row,'Qhsf']
        deltaH = Q/(U0*Af)
        S = 2*(deltaV0-deltaH) 
        if S/deltaH <= 0.5: #temperature drop of water should be in this range
           S = 2*(deltaV0-deltaH)
           DATA.loc[row,'tsh'] = deltaH + DATA.loc[row,'tair'] + S/2
           DATA.loc[row,'trh'] = DATA.loc[row,'tsh'] - Q/mCw0
           DATA.loc[row,'sup'] = (Q/(U0*Af))**(1/1.1)+ DATA.loc[row,'tair'] # to see temperatures of the floor
        else:
           S = 3*(deltaH)*(sqrt(1+((4*(deltaV0-deltaH))/(3*deltaH)))-1)
           DATA.loc[row,'tsh'] = deltaH + DATA.loc[row,'tair'] + S/2 #+(S**2/(12*deltaH))
           DATA.loc[row,'trh'] = DATA.loc[row,'tsh'] - Q/mCw0
           DATA.loc[row,'surface'] = (Q/(U0*Af))**(1/1.1)+ DATA.loc[row,'tair'] # to see temp of the floor
            
# FLOW CONSIDERING LOSSES Floor slab prototype
sins = 0.07
Ru = sins/0.15+0.17+0.1
R0 = 0.1+0.0093+0.045/1 # su = 0.045 it is the tickness of the slab    
# CONSTANT FLOW CONDITIONS
tu = 13 # temperature in the basement
if Floors ==1:
    mCw0 = Af*q0/(S0)*(1+R0/Ru+(tair-tu)/(q0*Ru))
else:
    Af1 = Af/Floors
    mCw0 = Af1*q0/(S0)*(1+R0/Ru+(tair-tu)/(Qh0*Ru/Af1))+((Af-Af1)*q0/(S0*4190)*(1+R0/Ru))            

# <codecell>

DATA['tsh'].plot();  plt.axis([8500,8760,0,40])
DATA['trh'].plot(); plt.axis([8500,8760,0,40])
DATA['sup'].plot(); plt.axis([8500,8760,0,40])

# <codecell>

trh0,DATA['trh'].max(),tsh0,DATA['tsh'].max(),mCw0,S/2

# <markdowncell>

# ##THis one is selected

# <codecell>

nh = 0.025
Af = 2200
tair0 = 20
Floors =1
Qh0 = Qhsmax = DATA['Qhsf'].max()
tmean_max = tair0 + 9.6                         # according ot EN 1264, simplifying to +9 k inernal surfaces
q0 = Qh0/Af                                            
S0 = 5                                             #drop of temperature of supplied water at nominal conditions
U0 = q0/(tmean_max-tair0)
deltaH0 = (Qh0/(U0*Af))

if S0/deltaH0 <= 0.5: #temperature drop of water should be in this range
    deltaV0 = deltaH0 + S0/2 
else:
    deltaV0 = deltaH0 + S0/2+(S0**2/(12*deltaH0))

tsh0 = deltaV0 + tair0
trh0 = tsh0 - S0
tsh0 = tsh0 + 273
trh0 = trh0 + 273
tair0 = tair0 + 273
mCw0 = q0*Af/(tsh0-trh0)
LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
qh0 = 8.92*(tmean_max+273-tair0)**1.1
kH0 = qh0*Af/(LMRT**(1+nh))
k1 = 1/mCw0
def fh(x): 
    Eq = mCw0*k2-kH0*(k2/(scipy.log((x+k2-tair)/(x-tair))))**(1+nh)
    return Eq
rows = DATA.Qhsf.count()
for row in range(rows):
    if DATA.loc[row,'Qhsf'] != 0:
        Q = DATA.loc[row,'Qhsf']
        q =Q/Af
        k2 = Q*k1
        tair = DATA.loc[row,'tair'] + 273
        DATA.loc[row,'trh'] = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        DATA.loc[row,'tsh'] = DATA.loc[row,'trh'] + k2
        DATA.loc[row,'sup'] = (q/U0)**(1/1.1)+ DATA.loc[row,'tair']
        
#FLOW CONSIDERING LOSSES Floor slab prototype
sins = 0.07
Ru = sins/0.15+0.17+0.1
R0 = 0.1+0.0093+0.045/1 # su = 0.045 it is the tickness of the slab    
# CONSTANT FLOW CONDITIONS
tu = 13 # temperature in the basement
if Floors ==1:
    mCw0 = Af*q0/(S0)*(1+R0/Ru+(tair-tu)/(q0*Ru))
else:
    Af1 = Af/Floors
    mCw0 = Af1*q0/(S0)*(1+R0/Ru+(tair-tu)/(Qh0*Ru/Af1))+((Af-Af1)*q0/(S0*4190)*(1+R0/Ru))            

# <codecell>

DATA['tsh'].plot();  #plt.axis([8500,8760,0,50])
DATA['trh'].plot(); #plt.axis([8500,8760,0,50])
DATA['sup'].plot(); #plt.axis([8500,8760,0,40])

# <codecell>

trh0-273,DATA['trh'].min(),tsh0-273,DATA['tsh'].max(),DATA['sup'].max(),mCw0,S/2,kH0,qh0

# <codecell>

DATA['trh'].max().real

# <markdowncell>

# ##TRY FOR HVAC SYSTEM:

# <codecell>

#Variables
WeatherData = pd.ExcelFile('C:\ArcGIS\EDMdata\Weatherdata\Temp_2010_2011.xls')
Temp = pd.ExcelFile.parse(WeatherData, 'Values_hour')
SystemH = 'Air conditioning'
SystemC = 'Air conditioning'
DATA = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\DEDM\StatusQuo\CityQuarter_3\Bau 14.csv')
Schedules = pd.ExcelFile('C:\ArcGIS\EDMdata\Statistical\Schedules.xls')
ADMIN = pd.ExcelFile.parse(Schedules, 'ADMIN')

# <codecell>

Temp['mh_air'] = 0
Temp['mc_air'] = 0
Temp['tsc_air'] = 0
Temp['tsh_air'] = 0
Temp['tsc_air_1'] = 0
Temp['tsh_air_1'] = 0
Temp['RH5'] = 0
DATA['Qlat'] = 0
Temp['deltaT'] = 0
Temp['w5'] = 0
Temp['t5'] = 0
Temp['w3'] = 0
Temp['w1'] = 0
Temp['t3'] = 0   
DATA['Qlat'] = 0
DATA['Qhum'] = 0
DATA['Qdhum'] = 0
DATA['Qslcf'] = 0
DATA['Qcsf_coil'] = 0
DATA['Qhsf_coil'] = 0
Af = 29362.9839

Num_hours = DATA.tair.count()
nrec_N = 0.75 
C1 = 0.054 # assumed a flat plate heat exchanger
Vmax = 3 # maximum estimated flow.
Pair = 998 #kg/m3
Seasonhours = [3216,6192]
lv = 2257 #kJ/kg
Cpa_w3 = 1.007 #in kJ/kgK
for j in range(Num_hours):
    if ADMIN.loc[j,'People'] > 0:  # during operation times only for the first itme step
        # Air temperature one step before including gain from fan as
        # as it is hourly it is assumed that the initial need of power takes just a small
        #amount of time in relation to the performance of the whole hour
        tset = DATA.loc[j,'tair']
        # OUTSIDE AIR
        RH1 = Temp.loc[j,'RH']
        t1 = Temp.loc[j,'te']
        w1 = calc_w(t1,RH1) #kg/kg
        h1 = calc_h(t1,w1)
        # AFTER HEAT RECOVERY
        qv_req = ADMIN.loc[j,'Ve']*Af/3600 # in m3/s
        qv = qv_req*0.8*1.04*1.02*1.2     # in m3/s corrected taking into acocunt leakage
        Veff = Vmax*qv/qv_req              
        nrec = nrec_N-C1*(Veff-2)   #$ heat exchanger coefficient
        # EXHAUST DUCT 
        if ADMIN.loc[j-1,'People'] == 0:
            t5_1 = tset + tset*0.2 #increase in temperature form the last step in the extracted air
            # initial state
            if RH1 >= 70:
                RH5_1 = 70
            elif 30 < RH1 < 70:
                RH5_1 = RH1
            else:
                RH5_1 = 30
            w5_1 =  calc_w(t5_1,RH5_1)
            t2 = t1 + nrec*(t5_1-t1)
            w2 = w1 + nrec*(w5_1-w1)
        elif ADMIN.loc[j-1,'People'] > 0:
            t5_1 = DATA.loc[j-1,'tair'] + DATA.loc[j-1,'tair']*0.2
            RH5_1 = Temp.loc[j-1,'RH5']
            w5_1 =  calc_w(t5_1,RH5_1)
            # AFTER AHU
            t2 = t1 + nrec*(t5_1-t1)
            w2 = w1 + nrec*(w5_1-w1)
        #production of humidity:
        Qlat = ADMIN.loc[j,'w_int']*(Af/(1000*3600)*lv)*3.6 #in kJ
        
        # ASSUMPTION  the HVAc does not alter the humidity content at the first step
        if Seasonhours[0] <= j+1 <= Seasonhours[1] and SystemC == 'Air conditioning' and DATA.loc[j,'Qcsf']>0: # this is cooling season
            Qs = DATA.loc[j,'Qcsf']*3.6 #in kJ
            w3 = w2
            t3 = 17      #which is the supply temperature?
            t5 = tset
            h5 = calc_h(t5,w3)
            h3 = calc_h(t3,w3)
            m = max(Qs/(h5-h3),(Pair*qv_req)) #kg/s # from the point of view of internal loads
            #VERIFICATION WITH HUMIDITY
            t5 = Qs/(m*Cpa_w3)+t3
            w5 = (m*w3+Qlat/lv)/m
            if w5 > calc_w(t5,70):
                #dehumidification
                w3 = max(min(calc_w(t5,70)-w5+w2,calc_w(t3,100)),0)
                Qdhum = 0.83*qv_req*3600*(w2-w3)*1000 #in Wh
            elif w5 < calc_w(t5,30):
                # Humidification
                w3 = calc_w(t5,30)- w5 + w2
                Qhum = 0.83*qv_req*3600*(calc_w(t5,30)- w5)*1000 # in Wh
            else:
                w3 = min(w2,calc_w(t3,100))
                Qhum = 0
                Qdhum = 0
                
            t5  = Qs/(m*Cpa_w3)+t3
            w5 = (m*w3+Qlat/lv)/m
            h5 = calc_h(t5,w5)
            h3 = calc_h(t3,w3)
            RH5 = calc_RH(w5,t5)
            m = max(Qs/(h5-h3),(Pair*qv_req))
            Temp.loc[j,'mc_air'] = m
            Temp.loc[j,'tsc_air'] = t3
            Temp.loc[j,'tsc_air_1'] = t2
            Temp.loc[j,'RH5'] = RH5
            Temp.loc[j,'w5'] = w5
            Temp.loc[j,'t5'] = t5
            Temp.loc[j,'w3'] = w3
            Temp.loc[j,'t3'] = t3
            DATA.loc[j,'Qcsf_coil'] = m*abs(h3-h2)/3.6 # in Wh
            
        elif SystemH == 'Air conditioning' and DATA.loc[j,'Qhsf']>0:
            Qs = DATA.loc[j,'Qhsf']*3.6
            w3 = w2
            t3 = tset # taking into account that the fan adds heat
            t5 = tset + tset*0.2
            h5 = calc_h(t5,w3)
            h3 = calc_h(t3,w3)
            m = max(Qs/(h5-h3),(Pair*qv_req)) # from the point of view of internal loads
            #VERIFICATION WITH HUMIDITY
            t5 = Qs/(m*Cpa_w3)+t3
            w5 = (m*w3+Qlat/lv)/m
            if  w5 < calc_w(t5,30):
                #Humidification
                w3 = calc_w(t5,30) - w5 + w2
                Qhum = 0.83*qv_req*3600*(calc_w(t5,30) - w5)*1000 # in Watts
            elif w5 > calc_w(t5_1,70) and w5 < calc_w(26,70): #dew point
                #heaitng with no dehumidification
                deltaT = calc_t(w5,70) - t5
                w3 = w2
            elif w5 > calc_w(26,70):
                #Dehumidification
                w3 = max(min(min(calc_w(26,70)-w5+w2,calc_w(t3,100)),calc_w(t5,70)-w5+w2),0)
                Qdhum = 0.83*qv_req*3600*(w2-w3)*1000 #in Watts
            else:
                # No mositure control necessary
                w3=w2
                Qhum = 0
                Qdhum = 0
                deltaT =0
            
            h2 = calc_h(t2,w2)
            h3 = calc_h(t3,w3)
            t5  = Qs/(m*Cpa_w3)+t3
            w5 = (m*w3+Qlat/lv)/m
            h5 = calc_h(t5,w5)
            RH5 = calc_RH(w5,t5)
            m = max(Qs/(h5-h3),(Pair*qv_req))
            Temp.loc[j,'mh_air'] = m
            Temp.loc[j,'tsh_air'] = t3
            Temp.loc[j,'tsh_air_1'] = t2
            Temp.loc[j,'deltaT'] = deltaT
            DATA.loc[j,'Qhsf_coil'] = m*abs(h3-h2)/3.6 # in Wh
        
        Temp.loc[j,'RH5'] = RH5
        Temp.loc[j,'w5'] = w5
        Temp.loc[j,'t5'] = t5
        Temp.loc[j,'w3'] = w3
        Temp.loc[j,'t3'] = t3 
        Temp.loc[j,'w1'] = w1
        DATA.loc[j,'Qlat'] = Qlat/3.6 #in Wh
        DATA.loc[j,'Qhum'] = Qhum
        DATA.loc[j,'Qdhum'] = Qdhum
                    
            #NOW IT IS POSSIBLE TO CALCULATE THE LOADS AT THE WATER DISTRIBUTION SYSTEM WITH A VARIABLE FLOW OF AIR
            # LETS TRY THE EQUATION OF HEAT EXCHANGER TO KNOW THE TEMPERATURES. E WUALA
            # PERHAPS IT IS NECESSARY TO HAVE JUST ONE CONSTANT INPUT OR OUTPUT OF COOLING WATER E WALA
                

# <codecell>

tsc0 = 7; trc0 = 15 # temperatures for operation at nomial capacity of the coil
Ca = 1.007 #kJ/kg.K
Cw = 4.18 #kJ/kg.K
Qc0 = DATA.Qcsf_coil.max()
mCw0 = Qc0/(trc0-tsc0)

Num_hours = DATA.tair.count()
for j in range(Num_hours):
    if DATA.loc[j,'Qcsf_coil'] == DATA.Qcsf_coil.max():
        ti_1_0 = Temp.loc[j,'tsc_air_1']
        ti_0 = Temp.loc[j,'tsc_air']
        mCa0 = Temp.loc[j,'mc_air']*Ca/3.6
        
tsc0 = tsc0 + 273
trc0 = trc0 + 273
ti_1_0 = ti_1_0+273
ti_0 = ti_0+273
LMRT0 = ((ti_1_0-trc0)-(ti_0-tsc0))/scipy.log((ti_1_0-trc0)/(ti_0-tsc0))
UA0 = Qc0/LMRT0

def fc(x): 
        Eq = Q - UA0*((ti_1-ti-k2))/scipy.log((ti_1-x)/(ti-x+k2))
        return Eq

tair0 = 22 + 273
for j in range(Num_hours):
    if DATA.loc[j,'Qcsf_coil'] >0 and (DATA.loc[j,'tair'] == (tair0-273)or DATA.loc[j,'tair'] == 30):
        mCa = Temp.loc[j,'mc_air']*Ca/3.6
        k1 = 1/mCw0 - 1/mCa   
        Q = DATA.loc[j,'Qcsf_coil']
        ti = Temp.loc[j,'tsc_air'] + 273
        ti_1 = Temp.loc[j,'tsc_air_1'] + 273
        DATA.loc[j,'trc'] = ti + Q*k1/(1-scipy.exp(UA0*k1))-273
        k2 = Q/mCw0
        #DATA.loc[j,'trc'] = scipy.optimize.newton(fc, trc0, maxiter=100,tol=0.01) - 273
        DATA.loc[j,'tsc'] = DATA.loc[j,'trc'] - k2
        COUNTER = j    

# <codecell>

LMRT0

# <codecell>

(ti_1_0-ti_0)*mCa0

# <codecell>

1/mCw0,1/mCa0

# <codecell>

tsc0 = 7; trc0 = 15 # temperatures for operation at nomial capacity of the coil
Ca = 1.007 #kJ/kg.K
Cw = 4.18 #kJ/kg.K
Qc0 = DATA.Qslcf.max()
mw = Qc0*3.6/((trc0-tsc0)*Cw)
mCw0 = mw*Cw

Num_hours = DATA.tair.count()
for j in range(Num_hours):
    if DATA.loc[j,'Qslcf'] == DATA.Qslcf.max():
        ti_1_0 = Temp.loc[j,'tsc_air_1']
        ti_0 = Temp.loc[j,'tsc_air']
        mCa0 = Temp.loc[j,'mc_air']*Ca/3.6

tsc0 = tsc0 + 273
trc0 = trc0 + 273
ti_1_0 = ti_1_0+273
ti_0 = ti_0+273
LMRT0 = ((ti_1_0-trc0)-(ti_0-tsc0))/scipy.log((ti_1_0-trc0)/(ti_0-tsc0))
UA0 = 0.5*Qc0/LMRT0

def fc(x): 
        Eq = Q - UA0*((ti_1-ti-k2))/scipy.log((ti_1-x)/(ti-x+k2))
        return Eq

tair0 = 22 + 273
for j in range(Num_hours):
    if DATA.loc[j,'Qcsf'] > 0 and (DATA.loc[j,'tair'] == (tair0-273)or DATA.loc[j,'tair'] == 30):
        mCa = Temp.loc[j,'mc_air']*Ca
        Q = -DATA.loc[j,'Qcsf']
        ti = Temp.loc[j,'tsc_air'] + 273
        ti_1 = Temp.loc[j,'tsc_air_1'] + 273
        k1 = 1/mCa- 1/mCw0 
        k2 = Q/mCw0
        DATA.loc[j,'trc'] = scipy.optimize.newton(fc, trc0, maxiter=100,tol=0.01) - 273
        DATA.loc[j,'tsc'] = DATA.loc[j,'trc'] + k2
        COUNTER = j   

# <codecell>

tair0 = 22
tsc0 = 7
trc0 = 12

tair0 = tair0 + 273
tsc0 = tsc0 + 273
trc0 = trc0 + 273
Qc0 = DATA.Qcsf.max()
mCw0 = Qc0/(trc0-tsc0)
Num_hours = DATA.tair.count()
for j in range(Num_hours):
    if DATA.loc[j,'Qcsf'] == DATA.Qcsf.max():
        ti_1_0 = Temp.loc[j,'tsc_air_1'] + 273
        ti_0 = Temp.loc[j,'tsc_air'] + 273

LMRT0 = (trc0-tsc0)/scipy.log((tsc0-ti_0)/(trc0-ti_0))
UA0 = Qc0/LMRT0
def fh(x): 
    Eq = mCw0*k2-UA0*(k2/(scipy.log((x-k2-ti)/(x-ti))))
    #Eq = mCw0*k2-UA0*(ti-ti_1+k2)/scipy.log((ti-k2-x)/(ti_1-x))
    return Eq
    
for j in range(Num_hours):
    if DATA.loc[j,'Qcsf'] > 0 and (DATA.loc[j,'tair'] == (tair0-273) or DATA.loc[j,'tair'] == 30):
        Q = DATA.loc[j,'Qcsf']
        ti = Temp.loc[j,'tsc_air'] + 273
        ti_1 = Temp.loc[j,'tsc_air_1']+ 273
        k2 = Q/mCw0
        DATA.loc[j,'trc'] = scipy.optimize.newton(fh, tsc0, maxiter=1000,tol=0.01) - 273
        DATA.loc[j,'tsc'] = DATA.loc[j,'trc'] - k2

# <codecell>

LMRT0,k2,ti_1_0-273,ti_0-273

# <codecell>

(trc0-tsc0)*mCw0

# <codecell>

def calc_w(t,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    Ps = 610.78*scipy.exp(t/(t+238.3*17.2694))
    Pv = RH/100*Ps
    w = 0.62*Pv/(Pa-Pv)
    return w

# <codecell>

def calc_h(t,w): # enthalpyh of most air in kJ/kg
    if 0 < t < 60:
        h = (1.007*t-0.026)+w*(2501+1.84*t)    
    elif -10 < t <= 0:
       h = (1.005*t)+w*(2501+1.84*t)
    return h

# <codecell>

def calc_t(w,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(RH/100*610.78*scipy.exp(x/(x+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 19, maxiter=100,tol=0.01)
    t = result.real
    return t

# <codecell>

def calc_RH(w,t): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(x/100*610.78*scipy.exp(t/(t+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 50, maxiter=100,tol=0.01)
    RH = result.real
    return RH

# <markdowncell>

# ##Visualizations

# <codecell>

#Temp['te'].plot(); #plt.axis([8500,8760,0,25])
Temp['tsc_air'].plot();  #plt.axis([8500,8760,0,25])
Temp['tsc_air_1'].plot(); #plt.axis([8500,8760,0,25])

# <codecell>

Temp['mh_air'].plot(); #plt.axis([4500,4760,0,100000])
Temp['mc_air'].plot(); #plt.axis([4500,4760,0,100000])

# <codecell>

#DATA['tair'].plot();#plt.axis([4500,4760,0,13])
DATA['tsc'].plot();#plt.axis([4500,4760,0,16])
DATA['trc'].plot();#plt.axis([4500,4760,0,16])

# <codecell>

DATA['trc'].max(),trc0-273,tsc0-273,DATA['tsc'].max(),(15-7)*mCw0,(24.6-17)*mCa0,DATA['Qcsf_coil'].max(),tsh0-273*2,trh0-273*2

# <codecell>

#DATA['Qhsf_coil'].plot();#plt.axis([3615,3618,0,1000000])
DATA['Qhsf'].plot();#plt.axis([3615,3618,0,1000000])
DATA['Qcsf'].plot();#plt.axis([3615,3618,0,1000000])
#DATA['Qlat'].plot()#;plt.axis([3615,3618,0,1000000])
#DATA['Qhum'].plot();#plt.axis([3615,3618,0,1000000])
#DATA['Qdhum'].plot();#plt.axis([3615,3618,0,1000000])

# <codecell>

DATA['Qcsf'].plot();#plt.axis([3615,3618,0,1000000])
DATA['Qcsf_coil'].plot();#plt.axis([3615,3618,0,1000000])
#DATA['Qlat'].plot()#;plt.axis([3615,3618,0,1000000])
#DATA['Qhum'].plot();#plt.axis([3615,3618,0,1000000])
#DATA['Qdhum'].plot();#plt.axis([3615,3618,0,1000000])

# <codecell>

Temp['RH'].plot()
Temp['RH5'].plot()

# <codecell>

Temp['w1'].plot()
Temp['w5'].plot()
Temp['w3'].plot()

# <codecell>

Temp['t5'].plot()
Temp['t3'].plot()

# <codecell>


