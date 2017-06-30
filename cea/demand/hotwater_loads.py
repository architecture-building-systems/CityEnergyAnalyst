"""
Hotwater load (it also calculates fresh water needs)
"""

from __future__ import division
import numpy as np
import scipy
from math import pi
from cea.technologies import storagetank as sto_m

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_mww(schedule, water_lpd, Pwater):
    """
    Algorithm to calculate the hourly mass flow rate of water

    :param schedule: hourly DHW demand profile [person/d.h]
    :param water_lpd: water emand per person per day in [L/person/day]
    :param Pwater: water density [kg/m3]
    """

    if schedule > 0:

        volume =  schedule * water_lpd/ 1000 # m3/h
        massflow = volume * Pwater/3600  # in kg/s

    else:
        volume = 0
        massflow = 0

    return massflow, volume

# final hot water demand calculation

def calc_Qwwf(Af, Lcww_dis, Lsww_dis, Lvww_c, Lvww_dis, T_ext, Ta, Tww_re, Tww_sup_0, Y, gv, occupancy_densities,
              schedules, bpr):
    # Refactored from CalcThermalLoads
    """
    This function calculates the distribution heat loss and final energy consumption of domestic hot water.
    Final energy consumption of dhw includes dhw demand, sensible heat loss in hot water storage tank, and heat loss in the distribution network.
    :param Af: Conditioned floor area in m2.
    :param Lcww_dis: Length of dhw usage circulation pipeline in m.
    :param Lsww_dis: Length of dhw usage distribution pipeline in m.
    :param Lvww_c: Length of dhw heating circulation pipeline in m.
    :param Lvww_dis: Length of dhw heating distribution pipeline in m.
    :param T_ext: Ambient temperature in C.
    :param Ta: Room temperature in C.
    :param Tww_re: Domestic hot water tank return temperature in C, this temperature is the ground water temperature, set according to norm.
    :param Tww_sup_0: Domestic hot water suppply set point temperature.
    :param vw: specific fresh water consumption in m3/hr*m2.
    :param vww: specific domestic hot water consumption in m3/hr*m2.
    :return:

    """

    # calc end-use demand
    Vww = schedules['Vww'] * bpr.internal_loads['Vww_lpd'] * bpr.rc_model['Af'] / 1000   # m3/h
    Vw = schedules['Vw'] * bpr.internal_loads['Vw_lpd'] * bpr.rc_model['Af'] / 1000      # m3/h
    mww = Vww * gv.Pwater /3600 # kg/s

    Qww = np.vectorize(calc_Qww)(mww, Tww_sup_0, Tww_re, gv.Cpw)
    Qww_0 = Qww.max()

    # distribution and circulation losses
    Vol_ls = Lsww_dis * (gv.D / 1000) ** (2 / 4) * pi # volume per meter of pipe
    Qww_dis_ls_r = np.vectorize(calc_Qww_dis_ls_r)(Ta, Qww, Lsww_dis, Lcww_dis, Y[1], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                           gv.Cpw, gv.Pwater, gv)
    Qww_dis_ls_nr = np.vectorize(calc_Qww_dis_ls_nr)(Ta, Qww, Lvww_dis, Lvww_c, Y[0], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                             gv.Cpw, gv.Pwater, gv.Bf, T_ext, gv)
    # storage losses
    Qww_st_ls, Tww_st, Qwwf = calc_Qww_st_ls(T_ext, Ta, Qww, Vww, Qww_dis_ls_r, Qww_dis_ls_nr, gv)

    # final demand
    Qwwf_0 = Qwwf.max()
    mcpwwf = Qwwf / abs(Tww_st - Tww_re)

    return mww, Qww, Qww_st_ls, Qwwf, Qwwf_0, Tww_st, Vww, Vw, mcpwwf

# end-use hot water demand calculation

def calc_Qww(mww, Tww_sup_0, Tww_re, Cpw):
    mcpww = mww * Cpw * 1000  # W/K
    Qww = mcpww * (Tww_sup_0 - Tww_re)  # heating for dhw in W
    return Qww

# losess hot water demand calculation

def calc_Qww_dis_ls_r(Tair, Qww, lsww_dis, lcww_dis, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, gv):
    if Qww > 0:
        # Calculate tamb in basement according to EN
        tamb = Tair

        # Circulation circuit losses
        circ_ls = (twws - tamb) * Y * lcww_dis * (Qww / Qww_0)

        # Distribtution circuit losses
        dis_ls = calc_disls(tamb, Qww, Flowtap, V, twws, lsww_dis, Pwater, Cpw, Y, gv)

        Qww_d_ls_r = circ_ls + dis_ls
    else:
        Qww_d_ls_r = 0
    return Qww_d_ls_r


def calc_Qww_dis_ls_nr(tair, Qww, Lvww_dis, Lvww_c, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, Bf, te, gv):
    if Qww > 0:
        # Calculate tamb in basement according to EN
        tamb = tair - Bf * (tair - te)

        # CIRUCLATION LOSSES
        d_circ_ls = (twws - tamb) * Y * (Lvww_c) * (Qww / Qww_0)

        # DISTRIBUTION LOSSEs
        d_dis_ls = calc_disls(tamb, Qww, Flowtap, V, twws, Lvww_dis, Pwater, Cpw, Y, gv)
        Qww_d_ls_nr = d_dis_ls + d_circ_ls
    else:
        Qww_d_ls_nr = 0
    return Qww_d_ls_nr


def calc_disls(tamb, hotw, Flowtap, V, twws, Lsww_dis, p, cpw, Y, gv):
    if hotw > 0:
        t = 3600 / ((hotw / 1000) / Flowtap)
        if t > 3600: t = 3600
        q = (twws - tamb) * Y
        try:
            exponential = scipy.exp(-(q * Lsww_dis * t) / (p * cpw * V * (twws - tamb) * 1000))
        except ZeroDivisionError:
            gv.log('twws: %(twws).2f, tamb: %(tamb).2f, p: %(p).2f, cpw: %(cpw).2f, V: %(V).2f',
                   twws=twws, tamb=tamb, p=p, cpw=cpw, V=V)
            exponential = scipy.exp(-(q * Lsww_dis * t) / (p * cpw * V * (twws - tamb) * 1000))
        tamb = tamb + (twws - tamb) * exponential
        losses = (twws - tamb) * V * cpw * p / 1000 * 278
    else:
        losses = 0
    return losses


def calc_Qww_st_ls(T_ext, Ta, Qww, Vww, Qww_dis_ls_r, Qww_dis_ls_nr, gv):
    Qwwf = np.zeros(8760)
    Qww_st_ls = np.zeros(8760)
    Tww_st = np.zeros(8760)
    Qd = np.zeros(8760)
    Vww_0 = Vww.max()
    Tww_st_0 = gv.Tww_setpoint

    if Vww_0 > 0:
        for k in range(8760):
            Qww_st_ls[k], Qd[k], Qwwf[k] = sto_m.calc_Qww_ls_st(Ta[k], T_ext[k], Tww_st_0, Vww_0, Qww[k], Qww_dis_ls_r[k],
                                                                Qww_dis_ls_nr[k], gv)
            Tww_st[k] = sto_m.solve_ode_storage(Tww_st_0, Qww_st_ls[k], Qd[k], Qwwf[k], Vww_0, gv)
            Tww_st_0 = Tww_st[k]
    else:
        for k in range(8760):
            Tww_st[k] = np.nan
    return Qww_st_ls, Tww_st, Qwwf