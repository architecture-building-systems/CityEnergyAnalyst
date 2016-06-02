"""
============================
subfunctions for heat exchangers
============================

"""
from __future__ import division
from math import exp, log
import pandas as pd
import scipy.optimize as opt


def calc_HEX_heating(Q, Qnom,thi,tco,tci,cc,thi_0,tho_0,tci_0,tco_0,cc_0):
    """
    heat exchanger for heating purposes
    
    Parameters
    ----------
    Qnom: nominal load in W
    thi : in temperature hot side in K
    tci : in temperature cold side in K
    cc: thermal flow rate capacity cold side in J/KgK
    case: heating or cooling
        1 for cross flow shell and tube (heating)
        2 for cross-flow flat plate (cooling)
    Returns
    -------
    tho : out temperature hot side in C
    ch: thermal flow rate capacity hot side in kW/K (network
    """

    
    #cr2 = 0.5
    #NTU2 = kA/(cc_0)
    #P2 =   calc_plate_HEX(NTU2,cr2)
    #alfa = P2/NTU2
    #ATmax = (thi-tci)
    #def fh(x):
    #    Eq = alfa*ATmax-(0.5*((thi-tco)+(x-tci)))
    #    return Eq
    #tho = opt.newton(fh, 50, maxiter=100,tol=0.01)
    #P1 = (thi-tho)/ATmax
    #ch = alfa*kA/P1
    ch_0 = cc_0*(tco_0-tci_0)/(thi_0-tci_0)
    tho_0 = thi_0+Qnom/ch_0
    ATm_0 = calc_ATm(thi_0,tho_0,tci_0,tco_0)
    kA = Qnom/ATm_0
    # R = 0.5 # assumed initial ratio where ch < cc 
    # ch_0 = Qnom/(thi_0-tho_0) # nominal flow of hot side.
    # ch = R*cc
    # if ch <= 0.2*ch_0:
    #     ch = 0.2*ch_0
    eff = [0,0]
    counter = 0
    eff[0] = 1
    while abs((eff[0]-eff[1])/eff[0])>0.00001:
        if counter == 1:
            eff[0] = eff[1]
        #ch = cc*(tco-tci)/(thi-tci)/eff[0]
        cmin = Q/((thi-tci)*eff[0])
        if cmin < cc:
            ch = cmin
            cmax = cc
        else:
            ch = cmin
            cmax = cmin
            cmin = cc 
        #cmin = min(cc,ch[0])
        cr =  cmin/cmax
        NTU = kA/(cmin) 
        eff[1] = calc_plate_HEX(NTU,cr) #cc*(tco-tci)/(cmin*(thi-tci))
        tho = thi-eff[1]*cmin*(thi-tci)/ch
        
         
        counter = 1
        #cmin = Q/(eff*thi-tho)   
        tco = eff[1]*cmin*(thi-tci)/cc+tci

    return tho, ch, tco, eff[1]
    
def calc_shell_HEX(NTU,cmin,cr):
    eff = 2*((1+cr+(1+cr**2)**(1/2))*((1+exp(-(NTU)*(1+cr**2)))/(1-exp(-(NTU)*(1+cr**2)))))**-1
    return eff
    
def calc_plate_HEX(NTU,cr):
    eff = 1-exp((1/cr)*(NTU**0.22)*(exp(-cr*(NTU)**0.78)-1))
    #a = 1/(1-exp(-NTU))
    #b = cr/(1-exp(-cr*NTU))
    #c = 1/NTU
    #P2 = 1/(a+b-c)
    return eff

    
    
    return eff

def calc_ATm(thi,tho,tci,tco):
    AT1 = thi-tco
    AT2 = tho-tci        
    ATm = (AT1-AT2)/log(AT1/AT2)
    return ATm

dataframe =pd.read_csv('C:\ArcGIS\EDMdata\DataFinal\EDM\HEB\ZONE_4\TW10.csv')

ATmin = 5
tci_0 = 10+273
tco_0 = 50+273
thi_0 = 60+273
tho_0 = 55+273
tho = []
ch  = []

Qnom = max(dataframe.Qwwf*1000)
dataframe['ch'] = dataframe['tho']  = dataframe['thi'] = dataframe['tco']=0
dataframe['eff'] =0
for x in range(dataframe.Name.count()):
    tco = dataframe.loc[x,'tsww']+273
    tci = dataframe.loc[x,'trww']+273
    thi = 60+273
    cc = dataframe.loc[x,'mcpww']*1000
    Q = dataframe.loc[x,'Qwwf']*1000
    cc_0 = dataframe.mcphs.max()*1000
    if tco > 273:
        result = calc_HEX_heating(Q, Qnom,thi,tco,tci,cc,thi_0,tho_0,tci_0,tco_0,cc_0)
        dataframe.loc[x,'tho'] = result[0]-273
        dataframe.loc[x,'ch'] = result[1]/1000 
        dataframe.loc[x,'tco'] = result[2]-273
        dataframe.loc[x,'thi'] = thi-273
        dataframe.loc[x,'eff'] = result[3]

    else:
        dataframe.loc[x,'tho'] = 0
        dataframe.loc[x,'ch'] = 0    

dataframe.tho[2100:2250].plot(legend=True); dataframe.trww[2100:2250].plot(legend=True);
dataframe.thi[2100:2250].plot(legend=True);dataframe.tco[2100:2250].plot(legend=True)

#dataframe['Qrect'] = dataframe.mcphs*(dataframe.tshs-dataframe.trhs)
#dataframe.Qrect.plot()

dataframe.mcpww[2100:2150].plot(legend=True);dataframe.ch[2100:2150].plot(legend=True)

dataframe['Qver'] =(dataframe.thi-dataframe.tho)*dataframe.ch
dataframe.Qwwf[2100:2150].plot(legend=True);dataframe.Qver[2100:2150].plot(legend=True)

dataframe.tco[2100:2150].plot(legend=True);dataframe.tsww[2100:2150].plot(legend=True)

dataframe.Qver.sum()/dataframe.Qwwf.sum()

dataframe.eff.plot(legend=True)
dataframe.tho[2100:2150].plot(legend=True);dataframe.thi[2100:2150].plot(legend=True)
