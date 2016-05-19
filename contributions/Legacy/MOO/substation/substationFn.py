# -*- coding: utf-8 -*-
"""
============================
substation model
============================
by J. Fonseca
"""

from __future__ import division
from math import exp, log
import numpy as np

def calc_DH_supply(t_0,t_1):
    tmax = max(t_0,t_1)
    return tmax

def calc_DC_supply(t_0,t_1):
    if t_0 == 0:
        t_0 = 1E6
    if t_1 > 0:
        tmin = min(t_0,t_1)  
    else:
        tmin = t_0    
    return tmin

def calc_substation_cooling(Q, thi, tho, tci, ch, ch_0, Qnom, thi_0, tci_0, tho_0,gv):

    #nominal conditions network side    
    cc_0 = ch_0*(thi_0-tho_0)/((thi_0-tci_0)*0.9)
    tco_0 = Qnom/cc_0+tci_0
    dTm_0 = calc_dTm_HEX(thi_0,tho_0,tci_0,tco_0,'cool')
    #Area heat excahnge and UA_heating    
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom,dTm_0,gv.U_cool)
    tco, cc = np.vectorize(calc_HEX_cooling)(Q, UA_cooling, thi, tho, tci, ch)
    
    return tco, cc, Area_HEX_cooling


def calc_HEX_cooling(Q, UA,thi,tho,tci,ch):
    if ch>0:  
        eff = [0.1,0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0]-eff[1])/eff[0])>tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = ch*(thi-tho)/((thi-tci)*eff[0])
            if cmin < ch:
                cc = cmin
                cmax = ch
            else:
                cc = cmin
                cmax = cc
                cmin = ch 
            cr =  cmin/cmax
            NTU = UA/cmin
            eff[1] =  calc_plate_HEX(NTU,cr)
            cmin = ch*(thi-tho)/((thi-tci)*eff[1])          
            tco = tci+eff[1]*cmin*(thi-tci)/cc 
            Flag = True
        cc = Q/abs(tci-tco)
        tco = tco-273
    else:
        tco = 0
        cc = 0
    return tco, cc/1000


def calc_HEX_mix(Q1,Q2, t1,m1,t2, m2):
    if Q1 >0 or Q2>0:
        tavg = (t1*m1+t2*m2)/(m1+m2)
    else:
        tavg = 0
    return tavg


def calc_substation_heating(Q,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv):
    #nominal conditions network side    
    ch_0 = cc_0*(tco_0-tci_0)/((thi_0-tci_0)*0.9)
    tho_0 = thi_0-Qnom/ch_0
    dTm_0 = calc_dTm_HEX(thi_0,tho_0,tci_0,tco_0,'heat')
    #Area heat excahnge and UA_heating    
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom,dTm_0,gv.U_heat)
    tho, ch = np.vectorize(calc_HEX_heating)(Q, UA_heating,thi,tco,tci,cc)
    return tho, ch, Area_HEX_heating


def calc_HEX_heating(Q, UA,thi,tco,tci,cc):
    if Q>0:  
        eff = [0.1,0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0]-eff[1])/eff[0])>tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = cc*(tco-tci)/((thi-tci)*eff[0])
            if cmin < cc:
                ch = cmin
                cmax = cc
            else:
                ch = cmin
                cmax = cmin
                cmin = cc 
            cr =  cmin/cmax
            NTU = UA/cmin 
            eff[1] =  calc_shell_HEX(NTU,cr)
            cmin = cc*(tco-tci)/((thi-tci)*eff[1])            
            tho = thi-eff[1]*cmin*(thi-tci)/ch  
            Flag = True
        
        tho = tho-273 
    else:
        tho = 0
        ch = 0
    return tho, ch/1000

def calc_shell_HEX(NTU,cr):
    eff = 2*((1+cr+(1+cr**2)**(1/2))*((1+exp(-(NTU)*(1+cr**2)))/(1-exp(-(NTU)*(1+cr**2)))))**-1
    return eff


def calc_plate_HEX(NTU,cr):
    eff = 1-exp((1/cr)*(NTU**0.22)*(exp(-cr*(NTU)**0.78)-1))
    return eff


def calc_dTm_HEX(thi,tho,tci,tco, flag):
    dT1 = thi-tco
    dT2 = tho-tci
    if flag == 'heat':
        dTm = (dT1-dT2)/log(dT1/dT2)
    else:
        dTm = (dT2-dT1)/log(dT2/dT1)
    return dTm

def calc_area_HEX(Qnom,dTm_0, U):
    area = Qnom/(dTm_0*U) #Qnom in W
    UA = U*area
    return area, UA