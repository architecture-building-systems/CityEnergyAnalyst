"""
=========================================
Sensible Heat Storage - Fully Mixed tank
=========================================
File history and credits:
S. Hsieh script development          20.04.16

This algorithm describes the energy conversion process of a fully mixed sensible heat storage tank (water based).
Calculation refers to E+ documentation.

Input variables: V (tank size), U_tank (tank Insulation Property), AR (tank Aspect Ratio)
Output variables: Qww_ls_st(sensible heat loss from storage tank), Tww_st(storage tank temperature)
"""

import numpy as np
from scipy.integrate import odeint
import math
import cea.globalvar

gv = cea.globalvar.GlobalVariables()

def calc_Qww_ls_st(Tww_st, Tww_setpoint, tair, Bf, te, V, Qww, Qww_ls_r, Qww_ls_nr, Utank, AR ):
    """
    This algorithm calculates the heat flows within a fully mixed water storage tank.
    Heat flows include sensible heat loss to the environment (ql), heat charged into the tank (qc), and heat discharged from the tank (qd).

    Parameters
    ----------
    :param Tww_st_0: Initial tank temperature in C
    :param V: dhw tank size in m3
    :param Qww: dhw demand in W
    :param Qww_ls_r: recoverable loss in distribution in W
    :param Qww_ls_nr: non-recoverable loss in distribution in W
    :param Utank: dhw tank insulation heat transfer coefficient in W/m2-K, value taken from SIA 385. global variable.
    :param AR: # tank height aspect ratio, H=(4*V*AR^2/pi)^(1/3), value taken from commercial tank geometry (jenni.ch). global variable.

    Returns
    -------
    :return ql: storage sensible heat loss in W.
    :return qd: heat discharged from the tank in W.
    :return qc: heat charged into the tank in W.
    """
    tamb = tair - Bf * (tair - te)         # Calculate tamb in basement according to EN

    h = (4*V*AR**2/math.pi)**(1.0/3.0)     # tank height in m, derived from tank Aspect Ratio(AR)
    r = (V/(math.pi*h))**(1.0/2.0)         # tank radius in m, assuming tank shape is cylinder
    Atank = 2*math.pi*r**2 + 2*math.pi*r*h      # tank surface area in m2.
    ql = Utank*Atank*(Tww_st - tamb)
    qd = Qww + Qww_ls_r + Qww_ls_nr
    if Qww <= 0:
        qc = 0
    else:
        qc = qd + ql + gv.Pwater*V*gv.Cpw*(Tww_setpoint-Tww_st)/3.6
    return ql, qd, qc


def ode(y, t, ql, qd, qc, Pwater, Cpw, Vtank):
    """
    This algorithm describe the energy balance of the dhw tank with a differential equation.

    Parameters
    ----------
    :param y: storage sensible temperature in K.
    :param t: time steps.
    :param ql: storage tank sensible heat loss in W.
    :param qd: heat discharged from the tank in W.
    :param qc: heat charged into the tank in W.

    Returns
    -------
    :return dydt: change in temperature at each time step.
    """
    dydt = (qc-ql-qd)/(Pwater*Vtank*Cpw)
    return dydt

def solve_ode_storage(Tww_st_0,ql,qd,qc,Pwater,Cpw,Vtank):
    """
    This algorithm solves the differential equation, ode.
    """
    t = np.linspace(0,1,2)
    y = odeint(ode, Tww_st_0, t, args = (ql, qd, qc, Pwater, Cpw, Vtank))
    return y[1]


