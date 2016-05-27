# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from __future__ import division
import arcpy
from arcpy import sa
import sys,os
import pandas as pd
import datetime
import jdcal
import math
import scipy
import numpy as np
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")
import matplotlib.pyplot as plt

# <codecell>

def calc_TABSH(tabsh,temps6,Qh0,tair0,tsh0,trh0):
    temps6['tsh'] = 0
    temps6['trh'] = 0
    nh = 0.2
    tair0 = tair0 + 273
    tsh0 = tsh0 + 273
    trh0 = trh0 + 273
    mCw0 = Qh0/(tsh0-trh0) 
    #minimum
    LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
    k1 = 1/mCw0
    def fh(x): 
        Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
        return Eq
    rows = 8760
    for row in range(rows):
        if tabsh.loc[row,'Qhsf'] > 0:
            Q = tabsh.loc[row,'Qhsf']
            k2 = Q*k1
            tair = temps6.loc[row,'tair'] + 273
            result = scipy.optimize.newton(fh, trh0, maxiter=1000,tol=0.1) - 273 
            temps6.loc[row,'trh'] = result.real
            temps6.loc[row,'tsh'] = temps6.loc[row,'trh'] + k2
                
                # Control system check
            min_AT = 3 # Its equal to 10% of the mass flowrate
            trh_min = tair + 1 -273
            tsh_min = trh_min + min_AT
            AT = (temps6.loc[row,'tsh'] - temps6.loc[row,'trh'])
            tsh = temps6.loc[row,'tsh']
            trh = temps6.loc[row,'trh']
            if Q > 0 and trh <= trh_min or tsh <= tsh_min:
                temps6.loc[row,'trh'] = trh_min
                temps6.loc[row,'tsh'] = tsh_min
                temps6.loc[row,'mcphs'] = tabsh.loc[row,'Qhsf']/min_AT/1000
            else:
                if Q > 0 and AT < min_AT and tsh > tsh_min:
                    temps6.loc[row,'trh'] = temps6.loc[row,'tsh'] - min_AT
                    temps6.loc[row,'mcphs'] = tabsh.loc[row,'Qhsf']/min_AT/1000         
    return  temps6.copy(), mCw0, tsh0, trh0

# <codecell>

Qh0 = 9016.283 #Wh
tair0 = 21
Af = 4*0.85*150
tsh0 = 41.5 
trh0 = 33.9
temps6 = pd.read_csv("C:\ArcGIS\EDMdata\DataFinal\DEDM\BAU\ZONE_3\AA03.csv")
temp = calc_TABSH(temps6,temps6,Qh0,tair0,tsh0,trh0)
result = temp[0]

# <codecell>

%matplotlib inline
ts = result[["DATE","tsh","trh","Qhsf"]]
ts.plot() ; plt.axis([7500,7600, 0, 9000])

# <codecell>

%matplotlib inline
ts = result[["DATE","tsh","trh"]]
ts.plot() ; plt.axis([7500,7600, 0, 100])

# <codecell>

            # Control system check
            min_AT = 3 # Its equal to 10% of the mass flowrate
            trh_min = tair + 1 -273
            tsh_min = trh_min + min_AT
            AT = (temps6.loc[row,'tsh'] - temps6.loc[row,'trh'])
            tsh = temps6.loc[row,'tsh']
            trh = temps6.loc[row,'trh']
            if Q > 0 and trh <= trh_min or tsh <= tsh_min:
                temps6.loc[row,'trh'] = trh_min
                temps6.loc[row,'tsh'] = tsh_min
                temps6.loc[row,'mcphs'] = tabsh.loc[row,'Qhsf']/min_AT
            else:
                if Q > 0 and AT < min_AT and tsh > tsh_min:
                    temps6.loc[row,'trh'] = temps6.loc[row,'tsh'] - min_AT
                    temps6.loc[row,'mcphs'] = tabsh.loc[row,'Qhsf']/min_AT 

# <codecell>


