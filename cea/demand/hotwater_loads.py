"""
=========================================
Hotwater load (it also calculates fresh water needs)
=========================================

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
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"



"""
=========================================
water demand calculation
=========================================
"""

def calc_mww(schedule, Vww_lpd, Occ_m2p, Af, Pwater):
    """
    Algorithm to calculate the hourly mass flow rate of domestic hot water

    Parameters
    ----------
    schedule: hourly DHW demand profile [1/h]
    Vww_lpd: DHW demand per person per day in [L/person/day]
    Occ_m2p: Occupant density in [m2/person]
    Af: Total floor area per building [m2]
    Pwater: water density [kg/m3]

    Returns
    -------

    """
    vww = schedule* Vww_lpd * (Occ_m2p ** -1) * Af / 1000 # m3/h
    mww = vww * Pwater / 3600  # in kg/s

    return mww, vww


def calc_mw(schedule, Vw_lpd, Occ_m2p, Af, Pwater):
    vw = schedule * Vw_lpd * (Occ_m2p ** -1) * Af / 1000 # m3/h
    mw = vw * Pwater / 3600  # in kg/s

    return mw, vw


"""
=========================================
final hot water demand calculation
=========================================
"""


def calc_Qwwf(Af, Lcww_dis, Lsww_dis, Lvww_c, Lvww_dis, T_ext, Ta, Tww_re, Tww_sup_0, Y, gv, Vww_lpd, Vw_lpd, Occ_m2p,
              list_uses, schedules, building_uses):
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
    # calc schedule of use:
    schedule = calc_Qww_schedule(list_uses, schedules, building_uses)

    # end-use demand
    mww, Vww =  np.vectorize(calc_mww)(schedule, Vww_lpd, Occ_m2p, Af, gv.Pwater)
    mw, Vw = np.vectorize(calc_mww)(schedule, Vw_lpd, Occ_m2p, Af, gv.Pwater)
    Qww = np.vectorize(calc_Qww)(mww, Tww_sup_0, Tww_re, gv.Cpw)
    Qww_0 = Qww.max()
    # distribution and circulation losses
    Vol_ls = Lsww_dis * (gv.D / 1000) ** (2 / 4) * pi #volume per meter of pipe
    Qww_dis_ls_r = np.vectorize(calc_Qww_dis_ls_r)(Ta, Qww, Lsww_dis, Lcww_dis, Y[1], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                           gv.Cpw, gv.Pwater, gv)
    Qww_dis_ls_nr = np.vectorize(calc_Qww_dis_ls_nr)(Ta, Qww, Lvww_dis, Lvww_c, Y[0], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                             gv.Cpw, gv.Pwater, gv.Bf, T_ext, gv)
    # storage losses
    Qww_st_ls, Tww_st, Qwwf = calc_Qww_st_ls(Vww, gv.Tww_setpoint, Ta, gv.Bf, gv.Pwater, gv.Cpw, Qww_dis_ls_r,
                                                     Qww_dis_ls_nr, gv.U_dhwtank, gv.AR, gv, T_ext, Qww)

    # final demand
    Qwwf_0 = Qwwf.max()
    mcpwwf = Qwwf / abs(Tww_st - Tww_re)

    return mww, Qww, Qww_st_ls, Qwwf, Qwwf_0, Tww_st, Vww, Vw, mcpwwf

"""
=========================================
end-use hot water demand calculation
=========================================
"""

def calc_Qww_schedule(list_uses, schedules, building_uses):
    """
    Algoithm to calculate the schedule of Qww use

    Parameters
    ----------
    list_uses
    schedules
    building_uses

    Returns
    -------

    """

    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    dhw = np.zeros(8760)
    num_profiles = len(list_uses)
    for num in range(num_profiles):
        current_share_of_use = building_uses[list_uses[num]]
        dhw = np.vectorize(calc_average)(dhw, schedules[num][2], current_share_of_use)

    return dhw


def calc_Qww(mww, Tww_sup_0, Tww_re, Cpw):
    mcpww = mww * Cpw * 1000  # W/K
    Qww = mcpww * (Tww_sup_0 - Tww_re)  # heating for dhw in W
    return Qww

"""
=========================================
losess hot water demand calculation
=========================================
"""

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


def calc_Qww_st_ls(Vww, Tww_setpoint, Ta, Bf, Pwater, Cpw, Qww_dis_ls_r, Qww_dis_ls_nr, U_dhwtank, AR, gv, T_ext, Qww):
    Qwwf = np.zeros(8760)
    Qww_st_ls = np.zeros(8760)
    Tww_st = np.zeros(8760)
    Qd = np.zeros(8760)
    Vww_0 = Vww.max()
    Tww_st_0 = Tww_setpoint
    for k in range(8760):
        Qww_st_ls[k], Qd[k], Qwwf[k] = sto_m.calc_Qww_ls_st(Tww_st_0, Tww_setpoint, Ta[k], Bf, T_ext[k], Vww_0,
                                                            Qww[k], Qww_dis_ls_r[k], Qww_dis_ls_nr[k], U_dhwtank, AR,
                                                            gv)
        Tww_st[k] = sto_m.solve_ode_storage(Tww_st_0, Qww_st_ls[k], Qd[k], Qwwf[k], Pwater, Cpw, Vww_0)
        Tww_st_0 = Tww_st[k]

    return Qww_st_ls, Tww_st, Qwwf

