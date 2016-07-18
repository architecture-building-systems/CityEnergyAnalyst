# -*- coding: utf-8 -*-
"""
=========================================
Electrical demand
=========================================

"""
__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


import numpy as np

def calc_E_totals(Aef, Ealf, Eauxf, Edataf, Eprof):
    # TODO: Documentation
    # FIXME: is input `Ealf` ever non-zero for Aef <= 0? (also check the other values)
    # Refactored from CalcThermalLoads
    if Aef > 0:
        Ealf_0 = Ealf.max()

        # compute totals electrical loads in MWh
        Ealf_tot = Ealf.sum() / 1e6
        Eauxf_tot = Eauxf.sum() / 1e6
        Epro_tot = Eprof.sum() / 1e6
        Edata_tot = Edataf.sum() / 1e6
    else:
        Ealf_tot = Eauxf_tot = Ealf_0 = 0
        Epro_tot = Edata_tot = 0
        Ealf = np.zeros(8760)
        Eprof = np.zeros(8760)
        Edataf = np.zeros(8760)
    return Ealf, Ealf_0, Ealf_tot, Eauxf_tot, Edataf, Edata_tot, Eprof, Epro_tot


def calc_Ea(schedule, Ea_Wm2, Af):
    Eaf = schedule * Ea_Wm2 * Af  # in W
    return Eaf

def calc_El(schedule , El_Wm2, Af):
    Elf = schedule * El_Wm2 * Af  # in W
    return Elf

def calc_Epro(schedule , Epro_Wm2, Af):
    Eprof = schedule  * Epro_Wm2 * Af  # in W
    return Eprof

def calc_Edata(schedule , Ed_Wm2, Af):
    Edataf = schedule  * Ed_Wm2 * Af  # in W
    return Edataf

def calc_Eref(schedule , Ere_Wm2, Af):
    Eref = schedule * Ere_Wm2 * Af  # in W
    return Eref

def calc_Eaux(Af, Ll, Lw, Mww, Qcsf, Qcsf_0, Qhsf, Qhsf_0, Qww, Qwwf, Qwwf_0, Tcs_re, Tcs_sup,
                  Ths_re, Ths_sup, Vw, Year, fforma, gv, nf_ag, nfp, qv_req, sys_e_cooling,
                  sys_e_heating, Ehs_lat_aux):


    Eaux_cs = np.zeros(8760)
    Eaux_ve = np.zeros(8760)
    Eaux_fw = np.zeros(8760)
    Eaux_hs = np.zeros(8760)
    Imax = 2 * (Ll + Lw / 2 + gv.hf + (nf_ag * nfp) + 10) * fforma
    deltaP_des = Imax * gv.deltaP_l * (1 + gv.fsr)
    if Year >= 2000:
        b = 1
    else:
        b = 1.2
    Eaux_ww = np.vectorize(calc_Eaux_ww)(Qww, Qwwf, Qwwf_0, Imax, deltaP_des, b, Mww)
    if sys_e_heating != "T0":
        Eaux_hs = np.vectorize(calc_Eaux_hs_dis)(Qhsf, Qhsf_0, Imax, deltaP_des, b, Ths_sup, Ths_re, gv.Cpw)
    if sys_e_cooling != "T0":
        Eaux_cs = np.vectorize(calc_Eaux_cs_dis)(Qcsf, Qcsf_0, Imax, deltaP_des, b, Tcs_sup, Tcs_re, gv.Cpw)
    if nf_ag > 5:  # up to 5th floor no pumping needs
        Eaux_fw = calc_Eaux_fw(Vw, nf_ag, gv)
    if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
        Eaux_ve = np.vectorize(calc_Eaux_ve)(Qhsf, Qcsf, gv.Pfan, qv_req, sys_e_heating, sys_e_cooling, Af)

    Eauxf = Eaux_hs + Eaux_cs + Eaux_ve + Eaux_ww + Eaux_fw + Ehs_lat_aux

    return Eauxf, Eaux_hs, Eaux_cs, Eaux_ve, Eaux_ww, Eaux_fw

def calc_Eaux_hs_dis(Qhsf, Qhsf0, Imax, deltaP_des, b, ts, tr, cpw):
    # the power of the pump in Watts
    if Qhsf > 0 and (ts - tr) != 0:
        fctr = 1.05
        qV_des = Qhsf / ((ts - tr) * cpw * 1000)
        Phy_des = 0.2278 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * fctr * b
        # Ppu_dis = Phy_des*feff
        if Qhsf / Qhsf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
            Eaux_hs = Ppu_dis_hy_i * feff
        else:
            Ppu_dis_hy_i = 0.0367 * Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
            Eaux_hs = Ppu_dis_hy_i * feff
    else:
        Eaux_hs = 0.0
    return Eaux_hs  # in #W


def calc_Eaux_cs_dis(Qcsf, Qcsf0, Imax, deltaP_des, b, ts, tr, cpw):
    # refrigerant R-22 1200 kg/m3
    # for Cooling system
    # the power of the pump in Watts
    if Qcsf < 0 and (ts - tr) != 0:
        fctr = 1.10
        qV_des = Qcsf / ((ts - tr) * cpw * 1000)  # kg/s
        Phy_des = 0.2778 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * fctr * b
        # Ppu_dis = Phy_des*feff
        # the power of the pump in Watts
        if Qcsf < 0:
            if Qcsf / Qcsf0 > 0.67:
                Ppu_dis_hy_i = Phy_des
                feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
                Eaux_cs = Ppu_dis_hy_i * feff
            else:
                Ppu_dis_hy_i = 0.0367 * Phy_des
                feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
                Eaux_cs = Ppu_dis_hy_i * feff
    else:
        Eaux_cs = 0.0
    return Eaux_cs  # in #W


def calc_Eaux_ve(Qhsf, Qcsf, P_ve, qve, SystemH, SystemC):
    if SystemH == 'T3':
        if Qhsf > 0:
            Eve_aux = P_ve * qve * 3600
        else:
            Eve_aux = 0.0
    elif SystemC == 'T3':
        if Qcsf < 0:
            Eve_aux = P_ve * qve * 3600
        else:
            Eve_aux = 0.0
    else:
        Eve_aux = 0.0

    return Eve_aux


def calc_Eaux_ww(Qww, Qwwf, Qwwf0, Imax, deltaP_des, b, qV_des):
    if Qww > 0:
        # for domestichotwater
        # the power of the pump in Watts
        Phy_des = 0.2778 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * b
        # Ppu_dis = Phy_des*feff
        # the power of the pump in Watts
        if Qwwf / Qwwf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * b
            Eaux_ww = Ppu_dis_hy_i * feff
        else:
            Ppu_dis_hy_i = 0.0367 * Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * b
            Eaux_ww = Ppu_dis_hy_i * feff
    else:
        Eaux_ww = 0.0
    return Eaux_ww  # in #W


def calc_Eaux_fw(freshw, nf, gv):
    Eaux_fw = np.zeros(8760)
    # for domesticFreshwater
    # the power of the pump in Watts Assuming the best performance of the pump of 0.6 and an accumulation tank
    for day in range(1, 366):
        balance = 0
        t0 = (day - 1) * 24
        t24 = day * 24
        for hour in range(t0, t24):
            balance = balance + freshw[hour]
        if balance > 0:
            flowday = balance / (3600)  # in m3/s
            Energy_hourWh = (gv.hf * (nf - 5)) / 0.6 * gv.Pwater * gv.gr * (flowday / gv.hoursop) / gv.effi
            for t in range(1, gv.hoursop + 1):
                time = t0 + 11 + t
                Eaux_fw[time] = Energy_hourWh
    return Eaux_fw
