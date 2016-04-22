
import numpy as np
from scipy.integrate import odeint
import math


def calc_Qww_ls_st(Tww_st_0, tair, Bf, te, V, Qww, Qww_ls_r, Qww_ls_nr, Utank, AR ):

    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-te)

    h= (4*V*AR**2/math.pi)**(1/3)  # tank height in m, derived from tank AR
    r= (V/(math.pi*h))*(1/2) # tank radius in m, assuming tank shape is cylinder

    Atank= 2*math.pi*r**2+2*math.pi*r*h      #tank surface area in m2.
    ql= Utank*Atank*(Tww_st_0-tamb)              #storage sensible heat loss in W.
    qd= Qww + Qww_ls_r + Qww_ls_nr           #discharing of storage in W, including DHW usage and distribution losses.
    qc= qd + ql                              #charging of storage in W.
    return ql, qd, qc


def ode(y,t,(ql,qd,qc,Pwater,Cpw,Vtank)):
            dydt= (qc-ql-qd)/(Pwater*Vtank*Cpw)
            return dydt

def solve_ode_storage(Tww_st_0,ql,qd,qc,Pwater,Cpw,Vtank):
            t=np.linspace(0,1,2)
            y=odeint(ode,Tww_st_0,t,arg = (ql,qd,qc,Pwater,Cpw,Vtank))
            return y[1]

#Qww_ls_st = np.zeros(8760)
#Tww_st = np.zeros(8760)

#for k in range(8760):
 #   Qww_ls_st[k], Qs = np.vectorize(calc_Qww_ls_st)(gv.Cpw, gv.Pwater, Tww_st_0, Ta, gv.Bf, te, vsource)
  #  Tww_st[k] = solve_ode_storage(Tww_st_0, Qww_ls_st[k], Qww, Qs, gv.Pwater, gv.Cpw)
   # Tww_st_0 = Tww_st[k]

def calc_V_dhwtank(vww, vww_0):    # Calculate the storage size according to summation of peak demand in m^3.
    peakdraw = vww_0
    i = np.argmax(vww)
    j = i
    k = i
    # summation of withdraw volume the peak demand period
    while vww_0 - 0.1 * vww_0 <= vww[j - 1] <= vww_0 + 0.1 * vww_0:
        peakdraw = peakdraw + vww[j - 1]
        j = j - 1
        while vww_0 - 0.1 * vww_0 <= vww[k + 1] <= vww_0 + 0.1 * vww_0:
            peakdraw = peakdraw + vww[k + 1]
            k = k + 1
    V_dhwtank = peakdraw
    return V_dhwtank


