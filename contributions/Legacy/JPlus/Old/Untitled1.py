# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from __future__ import division
import scipy
from scipy.optimize import brentq
import numpy as np

# <codecell>






SystemH ='Radiator'

# <codecell>

#Equation desccribing the phenomena HEATING SYSTEM after Girardin et al and model of TRNSYS 361 - constant flow temperature
if SystemH == 'Air conditioning':
    delta_ta = 3.5 #target temperature of supply for air conditioning systems difference
    mCa0 = Q0/delta_ta
    zero = 1
else:
    mCa0 = 1
    zero =0
UA0 = Q0/(tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
tm0 = (tsh0+trh0)/2
mCw0 = Q0/(tsh0-trh0)
k1 = 1/mCw0-1/mCa0*zero
k2 = Q0*k1
k3 = UA0*k1
k4 = Q/mCw0

# <codecell>

mCa0 = 1
zero =0
Q0 = 376334
Q = 376334
tsh0 = 35+273
trh0 = 15+273
tair0 = 22+273
tm0 = (tsh0+trh0)/2
nh = 0.33
tair = 22
d = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
delta = d.real
UA0 = Q0/delta
mCw0 = Q0/(tsh0-trh0)
def f(x):
    k1 = 1/mCw0-1/mCa0*zero
    k2 = Q0*k1
    k3 = UA0/mCw0
    k4 = Q/mCw0
    Eq = tair + -x + k4/(1-scipy.exp(k3*((x+k4/2)/tm0)**nh))
    return Eq

# <codecell>


# <codecell>

r = scipy.optimize.newton(f, 300).real
r

# <codecell>

s = r + k4
s

# <markdowncell>

# option 2

# <codecell>

Q0 = 376334
Q = 376134
k4 = Q/mCw0
def f(x): 
    d = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
    delta0 = d.real
    Eq = mCw0*(k4)-Q0*(k4/(scipy.log((x+k4-tair)/(x-tair))*delta0))**1.33
    return Eq

# <codecell>

r = scipy.optimize.newton(f, 300)

# <codecell>

r-273

# <codecell>

s = r + k4
s-273

# <markdowncell>

# Option 3

# <codecell>

tsh0 = 7+273
trh0 = 12+273
tair0 = 24+273
nh = 0.33
tair = 24+273
delta_ta = 3.5 #target temperature of supply for air conditioning systems difference
mCw0 = Q0/(tsh0-trh0)
mCa0 = Q0/delta_ta
Q0 = -80071
Q = -80071
k4 = Q*(1/mCw0-1/mCa0)
def f(x): 
    d = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
    delta0 = d.real
    Eq = (mCw0)*(k4)-Q0*(k4/(scipy.log((x+k4-tair)/(x-tair))*delta0))**1.3
    return Eq

# <codecell>

r = scipy.optimize.newton(f, trh0)
r-273

# <codecell>

math.pi

# <codecell>

s = r - k4
s-273

# <codecell>

Q0 = -80071
Q = -80071
tsc0 = 7+273
trc0 = 12+273
tair0 = 24+273
nh = 0.33
tair = 24+273
mCa0 = Q0/(delta_ta)
zero = 1
Freduction = 0.5

#Equation desccribing the phenomena COOLING SYSTEM after Girardin et al and model of TRNSYS 361 - constant flow temperature
UA0 = Freduction*Q0/(trc0-tsc0)/scipy.log((tair0-tsc0)/(tair0-trc0)) # 0.5 states for part of the area of heat excahnge not available in air conditioning
mCw0 = Q0/(trc0-tsc0) 
k2 = 1/mCw0 - 1/mCa0*zero
k1 = Q*k2
k3 = UA0*k2   
def fc(x):
    Eq = tair-x+(k1*k2)/(1-scipy.exp(k3))
    return Eq

# <codecell>

r = scipy.optimize.newton(f, 250)
r-273

# <codecell>

import pandas as pd
CQ_name = 'CityQuarter_3'
Scenario = 'StatusQuo'
locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+CQ_name
Occupancy = pd.read_csv(locationFinal+'\\'+'Bau 14'+'.csv',index_col='Unnamed: 0')

# <codecell>

# FOR COOLING SYSTEM
#Inputs
tsc0 = 16
trc0 = 20
tsc0 = tsc0 + 273
trc0 = trc0 + 273
tair0 = 22+273
tair = 22+273
Q0 = -40538
Q = -40538
delta_ta = 3.5 #target temperature of supply for air conditioning systems difference
nh =0.24
zero = 1
#Equation desccribing the phenomena COOLING SYSTEM after Girardin et al and model of TRNSYS 361 - constant flow temperature
mCw0 = Q0/(tsc0-trc0) 
k1 = 1/mCw0 
k2 = Q*k1
def fc(x): 
    d = (tsc0-trc0)/scipy.log((tsc0-tair0)/(trc0-tair0))
    delta0 = d.real
    Eq = (mCw0)*(k2)-Q0*(k2/(scipy.log((x+k2-tair)/(x-tair))*delta0))**(1.24)
    return Eq

# <codecell>

result =  scipy.optimize.newton_krylov(fc, 200) 
result.real-273

# <codecell>

s = result.real + k2
s-273

# <codecell>

rows = Occupancy.Qhsf.count()
for row in range(rows):
    if  Occupancy.loc[row,'Qhsf'] > Q0:
        k2 = Occupancy.loc[row,'Qhsf']*k1
        tair = Occupancy.loc[row,'tair']+ 273
        result =  scipy.optimize.newton_krylov(fc, 300)  
        Occupancy.loc[row,'trh'] = result.real - 273 
        Occupancy.loc[row,'tsh'] = Occupancy.loc[row,'trh'] + k2

# <codecell>


# <codecell>

Occupancy.Qhsf

# <codecell>


