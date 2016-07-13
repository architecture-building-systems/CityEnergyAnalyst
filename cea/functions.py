# -*- coding: utf-8 -*-
from __future__ import division

import math
import os

import numpy as np
import pandas as pd
import scipy
import scipy.optimize as sopt

import storagetank_mixed as sto_m

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Shanshan Hsieh", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def calc_mainuse(uses_df, uses):
    databaseclean = uses_df[uses].transpose()
    array_min = np.array(
        databaseclean[
            databaseclean[:] > 0].idxmin(
            skipna=True), dtype='S10')
    array_max = np.array(
        databaseclean[
            databaseclean[:] > 0].idxmax(
            skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_min, array_max))
    return mainuse


def calc_comparison(array_min, array_max):
    # do this to avoid that the selection of values
    # be based on the DEPO. for buildings qih heated spaces
    if array_max == 'PARKING':
        if array_min != 'PARKING':
            array_max = array_min
    return array_max


def calc_category(x, y):
    if 0 < x <= 1920:
        # Database['Qh'] = Database.ADMIN.value * Model.
        result = '1'
    elif x > 1920 and x <= 1970:
        result = '2'
    elif x > 1970 and x <= 1980:
        result = '3'
    elif x > 1980 and x <= 2000:
        result = '4'
    elif x > 2000 and x <= 2020:
        result = '5'
    elif x > 2020:
        result = '6'

    if 0 < y <= 1920:
        result = '7'
    elif 1920 < y <= 1970:
        result = '8'
    elif 1970 < y <= 1980:
        result = '9'
    elif 1980 < y <= 2000:
        result = '10'
    elif 2000 < y <= 2020:
        result = '11'
    elif y > 2020:
        result = '12'

    return result


def check_temp_file(T_ext,tH,tC, tmax):
    if tH == 0:
        tH = T_ext
    if tC == 0:
        tC = tmax+1
    return tH, tC


def Calc_Tm(Htr_3, Htr_1, tm_t0, Cm, Htr_em, Im_tot, Htr_ms, I_st, Htr_w, te_t, I_ia, IHC_nd, Hve, Htr_is):
    tm_t = (tm_t0 * ((Cm / 3600) - 0.5 * (Htr_3 + Htr_em)) + Im_tot) / ((Cm / 3600) + 0.5 * (Htr_3 + Htr_em))
    tm = (tm_t + tm_t0) / 2
    ts = (Htr_ms * tm + I_st + Htr_w * te_t + Htr_1 * (te_t + (I_ia + IHC_nd) / Hve)) / (Htr_ms + Htr_w + Htr_1)
    ta = (Htr_is * ts + Hve * te_t + I_ia + IHC_nd) / (Htr_is + Hve)
    top = 0.31 * ta + 0.69 * ts
    return tm, ts, ta, top


def calc_Htr(Hve, Htr_is, Htr_ms, Htr_w):
    Htr_1 = 1 / (1 / Hve + 1 / Htr_is)
    Htr_2 = Htr_1 + Htr_w
    Htr_3 = 1 / (1 / Htr_2 + 1 / Htr_ms)
    return Htr_1, Htr_2, Htr_3


def calc_Qem_ls(SystemH, SystemC):
    """model of losses in the emission and control system for space heating and cooling.
    correction factor for the heating and cooling setpoints. extracted from SIA 2044 (replacing EN 15243)"""
    tHC_corr = [0, 0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 'T4' or 'T1':
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 'T2':
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 'T3':  # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1  # regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2

    if SystemC == 'T4':
        tHC_corr[1] = 0 - 1.2
    elif SystemC == 'T5':
        tHC_corr[1] = - 0.4 - 1.2
    elif SystemC == 'T3':  # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 - 1  # regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + - 1.2

    return list(tHC_corr)


def Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd,Hve,Htr_2):
    return I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve) + te_t))/Htr_2



def calc_TL(SystemH, SystemC, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3,
            I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr, IC_max,IH_max, Flag):
    # assumptions
    if Losses:
        #Losses due to emission and control of systems
        tintH_set = tintH_set + tHset_corr
        tintC_set = tintC_set + tCset_corr
    
    # measure if this an uncomfortable hour
    uncomfort = 0    
    # Case 0 or 1 
    IHC_nd = IC_nd_ac = IH_nd_ac = 0
    Im_tot = Calc_Im_tot(I_m, Htr_em, te_t, Htr_3, I_st, Htr_w, Htr_1, I_ia, IHC_nd, Hve, Htr_2)
    tm, ts, tair_case0, top_case0 = Calc_Tm(Htr_3, Htr_1, tm_t0, Cm, Htr_em, Im_tot, Htr_ms, I_st, Htr_w, te_t, I_ia,
                                            IHC_nd, Hve, Htr_is)

    if tintH_set <= tair_case0 <= tintC_set:
        ta = tair_case0
        top = top_case0
        IH_nd_ac = 0
        IC_nd_ac = 0
    else:
        if tair_case0 > tintC_set:
            tair_set = tintC_set
        else:
            tair_set = tintH_set
        # Case 2 
        IHC_nd =  IHC_nd_10 = 10*Af
        Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd_10,Hve,Htr_2)
        tm, ts, tair10, top10 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_10,Hve,Htr_is)


        IHC_nd_un =  IHC_nd_10*(tair_set - tair_case0)/(tair10-tair_case0) #- I_TABS
        if  IC_max < IHC_nd_un < IH_max:
            ta = tair_set
            top = 0.31*ta+0.69*ts
            IHC_nd_ac = IHC_nd_un
        else:
            if IHC_nd_un > 0:
                IHC_nd_ac = IH_max
            else:
                IHC_nd_ac = IC_max
            # Case 3 when the maxiFmum power is exceeded
            Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd_ac,Hve,Htr_2)
            tm, ts, ta ,top = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_ac,Hve,Htr_is)
            uncomfort = 1

        if IHC_nd_un > 0:
            if  Flag == True:
                IH_nd_ac = 0
            else:
                IH_nd_ac = IHC_nd_ac
        else:
            if Flag == True:
                IC_nd_ac = IHC_nd_ac
            else:
                IC_nd_ac = 0

    if SystemC == "T0":
       IC_nd_ac = 0
    if SystemH == "T0":
       IH_nd_ac = 0
    return tm, ta, IH_nd_ac, IC_nd_ac,uncomfort, top, Im_tot


def calc_Qdis_ls(tair, text, Qhs, Qcs, tsh, trh, tsc,trc, Qhs_max, Qcs_max,D,Y, SystemH,SystemC, Bf, Lv):
    """calculates distribution losses based on ISO 15316"""
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-text)
    if SystemH != 'T0' and Qhs > 0:
        Qhs_d_ls = ((tsh + trh)/2-tamb)*(Qhs/Qhs_max)*(Lv*Y) 
    else:
        Qhs_d_ls = 0
    if SystemC != 'T0' and Qcs < 0:
        Qcs_d_ls = ((tsc + trc)/2-tamb)*(Qcs/Qcs_max)*(Lv*Y)
    else:
        Qcs_d_ls = 0
        
    return Qhs_d_ls,Qcs_d_ls


def calc_RAD(Qh,tair,Qh0,tair0, tsh0,trh0,nh):
    if Qh > 0:
        tair = tair+ 273
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

        k2 = Qh*k1
        result = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        trh = result.real
        tsh = trh + k2

        # Control system check
        #min_AT = 10 # Its equal to 10% of the mass flowrate
        #trh_min = tair + 5 - 273
        #tsh_min = trh_min + min_AT
        #AT = (tsh - trh)
        #if AT < min_AT:
        #    if (trh <= trh_min or tsh <= tsh_min):
        #        trh = trh_min
        ##        tsh = tsh_min
        #    if  tsh > tsh_min:
        #        trh = tsh - min_AT
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh,trh,mCw

def calc_TABSH(Qh,tair,Qh0,tair0, tsh0,trh0,nh):
    if Qh > 0:
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
        k2 = Qh*k1
        tair = tair + 273
        result = sopt.newton(fh, trh0, maxiter=1000,tol=0.1) - 273 
        trh = result.real
        tsh = trh + k2

        # Control system check
        #min_AT = 2 # Its equal to 10% of the mass flowrate
        #trh_min = tair + 1 - 273
        #tsh_min = trh_min + min_AT
        #AT = (tsh - trh)
        #if AT < min_AT:
        #    if trh <= trh_min or tsh <= tsh_min:
        #        trh = trh_min
        #        tsh = tsh_min
        #    if tsh > tsh_min:
        #        trh = tsh - min_AT           
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return  tsh,trh, mCw
    
def calc_qv_req(ve,people,Af,gv,hour_day,hour_year,limit_inf_season,limit_sup_season):

    infiltration_occupied = gv.hf*gv.NACH_inf_occ #m3/h.m2
    infiltration_non_occupied = gv.hf*gv.NACH_inf_non_occ #m3/h.m2
    if people >0:
        q_req = (ve+(infiltration_occupied*Af))/3600 #m3/s
    else:
        if (21 < hour_day or hour_day < 7) and (limit_inf_season < hour_year <limit_sup_season): 
            q_req = (ve*1.3+(infiltration_non_occupied*Af))/3600 # free cooling
        else:
            q_req = (ve+(infiltration_non_occupied*Af))/3600 #
    return q_req #m3/s

def calc_mixed_schedule(tsd, list_uses, schedules, building_uses):
    # weighted average of schedules
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use
    occ = np.zeros(8760)
    el = np.zeros(8760)
    dhw = np.zeros(8760)
    pro = np.zeros(8760)
    num_profiles = len(list_uses)
    for num in range(num_profiles):
        current_share_of_use = building_uses[list_uses[num]]
        occ = np.vectorize(calc_average)(occ, schedules[num][0], current_share_of_use)
        el = np.vectorize(calc_average)(el, schedules[num][1], current_share_of_use)
        dhw = np.vectorize(calc_average)(dhw, schedules[num][2], current_share_of_use)
        pro = np.vectorize(calc_average)(pro, schedules[num][3], current_share_of_use)

    tsd['occ'] = occ
    tsd['el'] = el
    tsd['dhw'] = dhw
    tsd['pro'] = pro
    return tsd


def get_internal_loads(tsd, prop_internal_loads, prop_architecture, Af):
    tsd['Ealf'] = tsd.el.values * (prop_internal_loads.El_Wm2 + prop_internal_loads.Ea_Wm2) * Af  # in W
    tsd['Edataf'] = tsd.el.values * prop_internal_loads.Ed_Wm2 * Af  # in W
    tsd['Eprof'] = tsd.pro.values * prop_internal_loads.Epro_Wm2 * Af  # in W
    tsd['Eref'] = tsd.el.values * prop_internal_loads.Ere_Wm2 * Af  # in W
    tsd['Qcrefri'] = (tsd['Eref'] * 4)  # where 4 is the COP of the refrigeration unit   # in W
    tsd['Qcdata'] = (tsd['Edataf'] * 0.9)  # where 0.9 is assumed of heat dissipation # in W
    tsd['vww'] = tsd.dhw.values * prop_internal_loads.Vww_lpd * prop_architecture.Occ_m2p ** -1 * Af / 24000  # m3/h
    tsd['vw'] = tsd.dhw.values * prop_internal_loads.Vw_lpd * prop_architecture.Occ_m2p ** -1 * Af / 24000  # m3/h

    return tsd

def get_occupancy(tsd, prop_architecture, Af):
    tsd['people'] = tsd.occ.values * (prop_architecture.Occ_m2p) ** -1 * Af  # in people
    return tsd

def get_internal_comfort(tsd, prop_comfort, limit_inf_season, limit_sup_season, weekday):
    def get_hsetpoint(a, b, Thset, Thsetback, weekday):
        if (b < limit_inf_season or b >= limit_sup_season):
            if a >0:
                if weekday >= 5: #system is off on the weekend
                    return -30 #huge so the system will be off
                else:
                    return Thset
            else:
                return Thsetback
        else:
            return -30 #huge so the system will be off
    def get_csetpoint(a, b, Tcset, Tcsetback, weekday):
        if limit_inf_season <= b < limit_sup_season:
            if a > 0:
                if weekday >= 5: #system is off on the weekend
                    return 50 # huge so the system will be off
                else:
                    return Tcset
            else:
                return Tcsetback
        else:
            return 50 # huge so the system will be off

    tsd['ve'] = tsd['people'] * prop_comfort.Ve_lps * 3.6  # in m3/h
    tsd['ta_hs_set'] = np.vectorize(get_hsetpoint)(tsd['people'], range(8760), prop_comfort.Ths_set_C, prop_comfort.Ths_setb_C,weekday)
    tsd['ta_cs_set'] = np.vectorize(get_csetpoint)(tsd['people'], range(8760), prop_comfort.Tcs_set_C, prop_comfort.Tcs_setb_C,weekday)

    return tsd


def calc_capacity_heating_cooling_system(Af, prop_HVAC):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    IC_max = -prop_HVAC.Qcsmax_Wm2 * Af
    IH_max = prop_HVAC.Qhsmax_Wm2 * Af
    return IC_max, IH_max


def calc_comp_heat_gains_sensible(tsd, Am, Atot, Htr_w):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    tsd['I_ia'] = 0.5 * tsd['I_int_sen']
    tsd['I_m'] = (Am / Atot) * (tsd['I_ia'] + tsd['I_sol'])
    tsd['I_st'] = (1 - (Am / Atot) - (Htr_w / (9.1 * Atot))) * (tsd['I_ia'] + tsd['I_sol'])
    return tsd


def calc_loads_electrical(Aef, Ealf, Eauxf, Edataf, Eprof):
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


def calc_heat_gains_internal_latent(people, X_ghp, sys_e_cooling, sys_e_heating):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
        w_int = people * X_ghp / (1000 * 3600)  # kg/kg.s
    else:
        w_int = 0

    return w_int


def calc_heat_gains_internal_sensible(people, Qs_Wp, Eal_nove, Eprof, Qcdata, Qcrefri):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    I_int_sen = people * Qs_Wp + 0.9 * (Eal_nove + Eprof) + Qcdata - Qcrefri  # here 0.9 is assumed
    return I_int_sen


def calc_temperatures_emission_systems(Qcsf, Qcsf_0, Qhsf, Qhsf_0, Ta, Ta_re_cs, Ta_re_hs, Ta_sup_cs, Ta_sup_hs,
                                       Tcs_re_0, Tcs_sup_0, Ths_re_0, Ths_sup_0, gv, ma_sup_cs, ma_sup_hs,
                                       sys_e_cooling, sys_e_heating, ta_hs_set, w_re, w_sup):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    Ths_sup = np.zeros(8760)  # in C
    Ths_re = np.zeros(8760)  # in C
    Tcs_re = np.zeros(8760)  # in C
    Tcs_sup = np.zeros(8760)  # in C
    mcphs = np.zeros(8760)  # in KW/C
    mcpcs = np.zeros(8760)  # in KW/C
    Ta_0 = ta_hs_set.max()
    if sys_e_heating == 'T1' or sys_e_heating == 'T2':  # radiators
        nh = 0.3
        Ths_sup, Ths_re, mcphs = np.vectorize(calc_RAD)(Qhsf, Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0, nh)
    if sys_e_heating == 'T3':  # air conditioning
        tasup = Ta_sup_hs + 273
        tare = Ta_re_hs + 273
        index = np.where(Qhsf == Qhsf_0)
        ma_sup_0 = ma_sup_hs[index[0][0]]
        Ta_sup_0 = Ta_sup_hs[index[0][0]] + 273
        Ta_re_0 = Ta_re_hs[index[0][0]] + 273
        tsh0 = Ths_sup_0 + 273
        trh0 = Ths_re_0 + 273
        mCw0 = Qhsf_0 / (tsh0 - trh0)

        # log mean temperature at nominal conditions
        TD10 = Ta_sup_0 - trh0
        TD20 = Ta_re_0 - tsh0
        LMRT0 = (TD10 - TD20) / scipy.log(TD20 / TD10)
        UA0 = Qhsf_0 / LMRT0

        Ths_sup, Ths_re, mcphs = np.vectorize(calc_Hcoil2)(Qhsf, tasup, tare, Qhsf_0, Ta_re_0, Ta_sup_0,
                                                           tsh0, trh0, w_re, w_sup, ma_sup_0, ma_sup_hs,
                                                           gv.Cpa, LMRT0, UA0, mCw0, Qhsf)
    if sys_e_heating == 'T4':  # floor heating
        nh = 0.2
        Ths_sup, Ths_re, mcphs = np.vectorize(calc_TABSH)(Qhsf, Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0, nh)
    if sys_e_cooling == 'T3':
        # Initialize temperatures
        tasup = Ta_sup_cs + 273
        tare = Ta_re_cs + 273
        index = np.where(Qcsf == Qcsf_0)
        ma_sup_0 = ma_sup_cs[index[0][0]] + 273
        Ta_sup_0 = Ta_sup_cs[index[0][0]] + 273
        Ta_re_0 = Ta_re_cs[index[0][0]] + 273
        tsc0 = Tcs_sup_0 + 273
        trc0 = Tcs_re_0 + 273
        mCw0 = Qcsf_0 / (tsc0 - trc0)

        # log mean temperature at nominal conditions
        TD10 = Ta_sup_0 - trc0
        TD20 = Ta_re_0 - tsc0
        LMRT0 = (TD20 - TD10) / scipy.log(TD20 / TD10)
        UA0 = Qcsf_0 / LMRT0

        # Make loop
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(calc_Ccoil2)(Qcsf, tasup, tare, Qcsf_0, Ta_re_0, Ta_sup_0,
                                                           tsc0, trc0, w_re, w_sup, ma_sup_0, ma_sup_cs, gv.Cpa,
                                                           LMRT0, UA0, mCw0, Qcsf)
        # 1. Calculate water consumption
    return Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs


def results_to_csv(GFA_m2, Af, Ealf, Ealf_0, Ealf_tot, Eauxf, Eauxf_tot, Edata, Edata_tot, Epro, Epro_tot, Name, Occupancy,
                   Occupants, Qcdata, Qcrefri, Qcs, Qcsf, Qcsf_0, Qhs, Qhsf, Qhsf_0, Qww, Qww_ls_st, Qwwf, Qwwf_0,
                   Tcs_re, Tcs_re_0, Tcs_sup, Tcs_sup_0, Ths_re, Ths_re_0, Ths_sup, Ths_sup_0, Tww_re, Tww_st,
                   Tww_sup_0, Waterconsumption, locationFinal, mcpcs, mcphs, mcpww, path_temporary_folder,
                   sys_e_cooling, sys_e_heating, waterpeak, date):
    # TODO: Document
    # Refactored from CalcThermalLoads

    # compute totals heating loads loads in MW
    if sys_e_heating != 'T0':
        Qhsf_tot = Qhsf.sum() / 1000000
        Qhs_tot = Qhs.sum() / 1000000
        Qwwf_tot = Qwwf.sum() / 1000000
        Qww_tot = Qww.sum() / 1000000
    else:
        Qhsf_tot = Qhs_tot = Qwwf_tot = Qww_tot = 0

    # compute totals cooling loads in MW
    if sys_e_cooling != 'T0':
        Qcs_tot = -Qcs.sum() / 1000000
        Qcsf_tot = -Qcsf.sum() / 1000000
        Qcrefri_tot = Qcrefri.sum() / 1000000
        Qcdata_tot = Qcdata.sum() / 1000000
    else:
        Qcs_tot = Qcsf_tot = Qcdata_tot = Qcrefri_tot = 0

    # print series all in kW, mcp in kW/h, cooling loads shown as positive, water consumption m3/h,
    # temperature in Degrees celcious
    pd.DataFrame(
        {'DATE': date, 'Name': Name, 'Ealf_kWh': Ealf / 1000, 'Eauxf_kWh': Eauxf / 1000, 'Qwwf_kWh': Qwwf / 1000,
         'Qww_kWh': Qww / 1000, 'Qww_tankloss_kWh': Qww_ls_st / 1000, 'Qhs_kWh': Qhs / 1000,
         'Qhsf_kWh': Qhsf / 1000,
         'Qcs_kWh': -1 * Qcs / 1000, 'Qcsf_kWh': -1 * Qcsf / 1000, 'occ_pax': Occupancy, 'Vw_m3': Waterconsumption,
         'Tshs_C': Ths_sup, 'Trhs_C': Ths_re, 'mcphs_kWC': mcphs, 'mcpww_kWC': mcpww/1000, 'Tscs_C': Tcs_sup,
         'Trcs_C': Tcs_re, 'mcpcs_kWC': mcpcs, 'Qcdataf_kWh': Qcdata / 1000, 'Tsww_C': Tww_sup_0, 'Trww_C': Tww_re,
         'Tww_tank_C': Tww_st, 'Ef_kWh': (Ealf + Eauxf + Epro) / 1000, 'Epro_kWh': Epro / 1000,
         'Qcref_kWh': Qcrefri / 1000,
         'Edataf_kWh': Edata / 1000, 'QHf_kWh': (Qwwf + Qhsf) / 1000,
         'QCf_kWh': (-1 * Qcsf + Qcdata + Qcrefri) / 1000}).to_csv(locationFinal + '\\' + Name + '.csv',
                                                                   index=False, float_format='%.2f')
    # print peaks in kW and totals in MWh, temperature peaks in C
    totals = pd.DataFrame(
        {'Name': Name, 'GFA_m2':GFA_m2,'Af_m2': Af, 'occ_pax': Occupants, 'Qwwf0_kW': Qwwf_0 / 1000, 'Ealf0_kW': Ealf_0 / 1000,
         'Qhsf0_kW': Qhsf_0 / 1000, 'Qcsf0_kW': -Qcsf_0 / 1000, 'Vw0_m3': waterpeak, 'Tshs0_C': Ths_sup_0,
         'Trhs0_C': Ths_re_0, 'mcphs0_kWC': mcphs.max(), 'Tscs0_C': Tcs_sup_0, 'Qcdataf_MWhyr': Qcdata_tot,
         'Qcref_MWhyr': Qcrefri_tot, 'Trcs0_C': Tcs_re_0, 'mcpcs0_kWC': mcpcs.max(), 'Qwwf_MWhyr': Qwwf_tot,
         'Qww_MWhyr': Qww_tot, 'Qhsf_MWhyr': Qhsf_tot, 'Qhs_MWhyr': Qhs_tot, 'Qcsf_MWhyr': Qcsf_tot,
         'Qcs_MWhyr': Qcs_tot,
         'Ealf_MWhyr': Ealf_tot, 'Eauxf_MWhyr': Eauxf_tot, 'Eprof_MWhyr': Epro_tot, 'Edataf_MWhyr': Edata_tot,
         'Tsww0_C': Tww_sup_0, 'Vw_m3yr': Waterconsumption.sum(),
         'Ef_MWhyr': (Ealf_tot + Eauxf_tot + Epro_tot + Edata_tot), 'QHf_MWhyr': (Qwwf_tot + Qhsf_tot),
         'QCf_MWhyr': (Qcsf_tot + Qcdata_tot + Qcrefri_tot)}, index=[0])
    totals.to_csv(os.path.join(path_temporary_folder, '%sT.csv' % Name), index=False, float_format='%.2f')


def calc_pumping_systems_aux_loads(Af, Ll, Lw, Mww, Qcsf, Qcsf_0, Qhsf, Qhsf_0, Qww, Qwwf, Qwwf_0, Tcs_re, Tcs_sup,
                                   Ths_re, Ths_sup, Vw, Year, fforma, gv, nf_ag, nfp, qv_req, sys_e_cooling,
                                   sys_e_heating):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

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

    return Eaux_cs, Eaux_fw, Eaux_hs, Eaux_ve, Eaux_ww


def calc_dhw_heating_demand(Af, Lcww_dis, Lsww_dis, Lvww_c, Lvww_dis, T_ext, Ta, Tww_re, Tww_sup_0, Y, gv, vw, vww):
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

    Vww = vww * Af / 1000  ## consumption of hot water in m3/hour
    Vw = vw * Af / 1000  ## consumption of fresh water in m3/h = cold water + hot water
    Mww = Vww * gv.Pwater / 3600  # in kg/s
    # Mw = Vw*Pwater/3600 # in kg/s
    # 2. Calculate hot water demand
    mcpww = Mww * gv.Cpw * 1000 # W/K
    Qww = mcpww * (Tww_sup_0 - Tww_re)  # heating for dhw in W
    # 3. losses distribution of domestic hot water recoverable and not recoverable
    Qww_0 = Qww.max()
    Vol_ls = Lsww_dis * (gv.D / 1000) ** (2 / 4) * math.pi
    Qww_ls_r = np.vectorize(calc_Qww_ls_r)(Ta, Qww, Lsww_dis, Lcww_dis, Y[1], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                           gv.Cpw, gv.Pwater, gv)
    Qww_ls_nr = np.vectorize(calc_Qww_ls_nr)(Ta, Qww, Lvww_dis, Lvww_c, Y[0], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0,
                                             gv.Cpw, gv.Pwater, gv.Bf, T_ext, gv)
    # fully mixed storage tank sensible heat loss calculation
    Qww_ls_st = np.zeros(8760)
    Tww_st = np.zeros(8760)
    Qd = np.zeros(8760)
    Qwwf = np.zeros(8760)
    Vww_0 = Vww.max()             # peak dhw demand in m3/hour, also used for dhw tank sizing.
    Tww_st_0 = gv.Tww_setpoint    # initial tank temperature in C
    # calculate heat loss and temperature in dhw tank
    for k in range(8760):
        Qww_ls_st[k], Qd[k], Qwwf[k] = sto_m.calc_Qww_ls_st(Tww_st_0, gv.Tww_setpoint, Ta[k], gv.Bf, T_ext[k], Vww_0,
                                                            Qww[k], Qww_ls_r[k], Qww_ls_nr[k], gv.U_dhwtank, gv.AR, gv)
        Tww_st[k] = sto_m.solve_ode_storage(Tww_st_0, Qww_ls_st[k], Qd[k], Qwwf[k], gv.Pwater, gv.Cpw, Vww_0)
        Tww_st_0 = Tww_st[k]
    Qwwf_0 = Qwwf.max()
    mcpwwf = Qwwf/abs(Tww_st-Tww_re)
    return Mww, Qww, Qww_ls_st, Qwwf, Qwwf_0, Tww_st, Vw, Vww, mcpwwf


def calc_HVAC(SystemH, SystemC, people, RH1, t1, tair, qv_req, Flag, Qsen, t5_1, wint,gv):
    # State No. 5 # indoor air set point
    t5 = tair + 1 # accounding for an increase in temperature
    if Qsen != 0:
        #sensiblea nd latennt loads
        Qsen = Qsen*0.001 # transform in kJ/s
        # Properties of heat recovery and required air incl. Leakage
        qv = qv_req*1.0184     # in m3/s corrected taking into acocunt leakage
        Veff = gv.Vmax*qv/qv_req        #max velocity effective      
        nrec = gv.nrec_N-gv.C1*(Veff-2)   # heat exchanger coefficient

        # State No. 1
        w1 = calc_w(t1,RH1) #kg/kg    

        # State No. 2
        t2 = t1 + nrec*(t5_1-t1)
        w2 = min(w1,calc_w(t2,100))

        # State No. 3
        # Assuming thath AHU do not modify the air humidity
        w3 = w2  
        if Qsen > 0:  #if heating
            t3 = 30 # in C
        elif Qsen < 0: # if cooling
            t3 = 16 #in C

        # mass of the system
        h_t5_w3 =  calc_h(t5,w3)
        h_t3_w3 = calc_h(t3,w3)
        m1 = max(Qsen/((t3-t5)*gv.Cpa),(gv.Pair*qv)) #kg/s # from the point of view of internal loads
        w5 = (wint+w3*m1)/m1

        #room supply moisture content:
        liminf= calc_w(t5,30)
        limsup = calc_w(t5,70)
        if Qsen > 0:  #if heating
            w3, Qhum , Qdhum = calc_w3_heating_case(t5,w2,w5,t3,t5_1,m1,gv.lvapor,liminf,limsup)
        elif Qsen < 0: # if cooling
            w3, Qhum , Qdhum = calc_w3_cooling_case(w2,t3,w5,liminf,limsup,m1,gv.lvapor)

        # State of Supply
        ws = w3
        ts = t3 - 0.5 # minus the expected delta T rise temperature in the ducts

        # the new mass flow rate
        h_t5_w3 =  calc_h(t5,w3)
        h_ts_ws = calc_h(t3,ws)
        m = max(Qsen/((ts-t2)*gv.Cpa),(gv.Pair*qv)) #kg/s # from the point of view of internal loads

        # Total loads
        h_t2_w2 = calc_h(t2,w2)
        Qtot = m*(h_t3_w3-h_t2_w2)*1000 # in watts
        
        # Adiabatic humidifier - computation of electrical auxiliary loads
        if Qhum >0:
            Ehum_aux = 15/3600*m # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012
        else:
            Ehum_aux =0
            
        if Qsen > 0:
            Qhs_sen = Qtot - Qhum
            ma_hs = m
            ts_hs = ts
            tr_hs = t2
            Qcs_sen = 0
            ma_cs = 0
            ts_cs = 0
            tr_cs =  0          
        elif Qsen < 0:
            Qcs_sen = Qtot - Qdhum
            ma_hs = 0
            ts_hs = 0
            tr_hs = 0
            ma_cs = m
            ts_cs = ts
            tr_cs = t2  
            Qhs_sen = 0
    else: 
        Qhum = 0
        Qdhum = 0
        Qtot = 0
        Qhs_sen = 0
        Qcs_sen = 0
        w1 = w2 = w3 = w5 = t2 = t3 = ts = m = 0
        Ehum_aux = 0
        #Edhum_aux = 0
        ma_hs = ts_hs = tr_hs = ts_cs = tr_cs = ma_cs =  0
    
    return Qhs_sen, Qcs_sen, Qhum, Qdhum, Ehum_aux, ma_hs, ma_cs, ts_hs, ts_cs, tr_hs, tr_cs, w2 , w3, t5

def calc_w3_heating_case(t5,w2,w5,t3,t5_1,m,lvapor,liminf,limsup):
    Qhum = 0
    Qdhum = 0
    if w5 < liminf:
        # humidification
        w3 = liminf - w5 + w2
        Qhum = lvapor*m*(w3 - w2)*1000 # in Watts
    elif w5 < limsup and w5  < calc_w(35,70):
        # heating and no dehumidification
        #delta_HVAC = calc_t(w5,70)-t5
        w3 = w2
    elif w5 > limsup:
        # dehumidification
        w3 = max(min(min(calc_w(35,70)-w5+w2,calc_w(t3,100)),limsup-w5+w2),0)
        Qdhum = lvapor*m*(w3 - w2)*1000 # in Watts
    else:
        # no moisture control
        w3 = w2
    return w3, Qhum , Qdhum 

def calc_w3_cooling_case(w2,t3,w5, liminf,limsup,m,lvapor):
    Qhum = 0
    Qdhum = 0
    if w5 > limsup:
        #dehumidification
        w3 = max(min(limsup-w5+w2,calc_w(t3,100)),0)
        Qdhum = lvapor*m*(w3 - w2)*1000 # in Watts
    elif w5 < liminf:
        # humidification
        w3 = liminf-w5+w2
        Qhum = lvapor*m*(w3 - w2)*1000 # in Watts
    else:
        w3 = min(w2,calc_w(t3,100))
    return w3, Qhum , Qdhum

def calc_w(t,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    Ps = 610.78*math.exp(t/(t+238.3)*17.2694)
    Pv = RH/100*Ps
    w = 0.62*Pv/(Pa-Pv)
    return w

def calc_h(t,w): # enthalpyh of most air in kJ/kg
    if 0 < t < 60:
        h = (1.007*t-0.026)+w*(2501+1.84*t)    
    elif -100 < t <= 0:
        h = (1.005*t)+w*(2501+1.84*t)
   # else:
    #    h = (1.007*t-0.026)+w*(2501+1.84*t) 
    return h

def calc_RH(w,t): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(x/100*610.78*scipy.exp(t/(t+238.3*17.2694)))-1)-0.62
        return Eq
    result = sopt.newton(Ps, 50, maxiter=100,tol=0.01)
    RH = result.real
    return RH

def calc_t(w,RH): # tempeature in C
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(RH/100*610.78*scipy.exp(x/(x+238.3*17.2694)))-1)-0.62
        return Eq
    result = sopt.newton(Ps, 19, maxiter=100,tol=0.01)
    t = result.real
    return t


def calc_Hcoil2(Qh, tasup, tare, Qh0, tare_0, tasup_0, tsh0, trh0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qhsf):
    if Qh > 0 and ma >0:
        AUa = UA0*(ma/ma0)**0.77
        NTUc= AUa/(ma*Cpa*1000)
        ec =  1 - scipy.exp(-NTUc)
        tc = (tare-tasup + tasup*ec)/ec #contact temperature of coil
        
        #minimum
        LMRT = (tsh0-trh0)/scipy.log((tsh0-tc)/(trh0-tc))
        k1 = 1/mCw0
        def fh(x): 
            Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tc)/(x-tc))*LMRT))
            return Eq
        k2 = Qh*k1
        result = sopt.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        trh = result.real
        tsh = trh + k2
        
        # Control system check - close to optimal flow
        #min_AT = 10 # Its equal to 10% of the mass flowrate
        #tsh_min = tasup + min_AT -273  # to consider coolest source possible
        #trh_min = tasup - 273
        #if trh < trh_min or tsh < tsh_min:
        #    trh = trh_min
        #    tsh = tsh_min
            
        mcphs = Qhsf/(tsh-trh)/1000  
    else:
        tsh = trh =  mcphs =0
    return tsh, trh,  mcphs

def calc_Ccoil2(Qc, tasup, tare, Qc0, tare_0, tasup_0, tsc0, trc0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qcsf):
    #Water cooling coil for temperature control
    if Qc < 0 and ma >0:
        AUa = UA0*(ma/ma0)**0.77
        NTUc= AUa/(ma*Cpa*1000)
        ec =  1 - scipy.exp(-NTUc)
        tc = (tare-tasup + tasup*ec)/ec  #contact temperature of coil
        
        def fh(x):
            TD1 = tc - (k2 + x)
            TD2 = tc - x
            LMRT = (TD2-TD1)/scipy.log(TD2/TD1)
            Eq = mCw0*k2-Qc0*(LMRT/LMRT0)
            return Eq
        
        k2 = -Qc/mCw0
        result = sopt.newton(fh, trc0, maxiter=100,tol=0.01) - 273
        tsc = result.real
        trc =  tsc + k2 
        
        # Control system check - close to optimal flow
        min_AT = 5 # Its equal to 10% of the mass flowrate
        tsc_min = 7 # to consider coolest source possible
        trc_max = 17
        tsc_max = 12
        AT =  tsc - trc
        if AT < min_AT:
            if tsc < tsc_min:
                tsc = tsc_min
                trc = tsc_min + min_AT
            if tsc > tsc_max:
                tsc = tsc_max
                trc = tsc_max + min_AT
            else:
                trc = tsc + min_AT
        elif tsc > tsc_max or trc > trc_max or tsc < tsc_min:
            trc = trc_max
            tsc = tsc_max
            
        mcpcs = Qcsf/(tsc-trc)/1000
    else:
        tsc = trc = mcpcs = 0
    return tsc, trc, mcpcs 

def calc_Qww_ls_r(Tair,Qww, lsww_dis, lcww_dis, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, gv):
    # Calculate tamb in basement according to EN
    tamb = Tair

    # Circulation circuit losses
    circ_ls = (twws-tamb)*Y*lcww_dis*(Qww/Qww_0)

    # Distribtution circuit losses
    dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,lsww_dis,Pwater,Cpw, Y, gv)

    Qww_d_ls_r = circ_ls + dis_ls
    
    return Qww_d_ls_r

def calc_Qww_ls_nr(tair,Qww, Lvww_dis, Lvww_c, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, Bf, te, gv):
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-te)
    
    # CIRUCLATION LOSSES
    d_circ_ls = (twws-tamb)*Y*(Lvww_c)*(Qww/Qww_0)
    
    # DISTRIBUTION LOSSEs
    d_dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,Lvww_dis,Pwater,Cpw,Y, gv)
    Qww_d_ls_nr = d_dis_ls + d_circ_ls
    
    return Qww_d_ls_nr

def calc_disls(tamb,hotw,Flowtap,V,twws,Lsww_dis,p,cpw, Y, gv):
    if hotw > 0:
        t = 3600/((hotw/1000)/Flowtap)
        if t > 3600: t = 3600
        q = (twws-tamb)*Y
        try:
            exponential = scipy.exp(-(q*Lsww_dis*t)/(p*cpw*V*(twws-tamb)*1000))
        except ZeroDivisionError:
            gv.log('twws: %(twws).2f, tamb: %(tamb).2f, p: %(p).2f, cpw: %(cpw).2f, V: %(V).2f',
                   twws=twws, tamb=tamb, p=p, cpw=cpw, V=V)
            exponential = scipy.exp(-(q*Lsww_dis*t)/(p*cpw*V*(twws-tamb)*1000))
        tamb = tamb + (twws-tamb)*exponential  
        losses = (twws-tamb)*V*cpw*p/1000*278
    else:
        losses= 0
    return losses

def calc_Eaux_ww(Qww,Qwwf,Qwwf0,Imax,deltaP_des,b,qV_des):
    if Qww>0:
        # for domestichotwater 
        #the power of the pump in Watts 
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*b
        #Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        if Qwwf/Qwwf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
            Eaux_ww = Ppu_dis_hy_i*feff
        else:
            Ppu_dis_hy_i = 0.0367*Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
            Eaux_ww = Ppu_dis_hy_i*feff 
    else:
        Eaux_ww = 0.0
    return Eaux_ww #in #W

def calc_Eaux_hs_dis(Qhsf,Qhsf0,Imax,deltaP_des,b, ts,tr,cpw):  
    #the power of the pump in Watts 
    if Qhsf > 0 and (ts-tr) != 0:
        fctr = 1.05
        qV_des = Qhsf/((ts-tr)*cpw*1000)
        Phy_des = 0.2278*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        #Ppu_dis = Phy_des*feff
        if Qhsf/Qhsf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
            Eaux_hs = Ppu_dis_hy_i*feff
        else:
            Ppu_dis_hy_i = 0.0367*Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
            Eaux_hs = Ppu_dis_hy_i*feff
    else:
        Eaux_hs = 0.0
    return Eaux_hs #in #W

def calc_Eaux_cs_dis(Qcsf,Qcsf0,Imax,deltaP_des,b, ts,tr,cpw): 
#refrigerant R-22 1200 kg/m3
    # for Cooling system   
    #the power of the pump in Watts 
    if Qcsf <0 and (ts-tr) != 0:
        fctr = 1.10
        qV_des = Qcsf/((ts-tr)*cpw*1000)  # kg/s
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        #Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        if Qcsf < 0:
            if Qcsf/Qcsf0 > 0.67:
                Ppu_dis_hy_i = Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                Eaux_cs = Ppu_dis_hy_i*feff
            else:
                Ppu_dis_hy_i = 0.0367*Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                Eaux_cs = Ppu_dis_hy_i*feff 
    else:
        Eaux_cs = 0.0
    return Eaux_cs #in #W

def calc_Eaux_fw(freshw,nf,gv):
    Eaux_fw = np.zeros(8760)
    # for domesticFreshwater
    #the power of the pump in Watts Assuming the best performance of the pump of 0.6 and an accumulation tank
    for day in range(1,366):
        balance = 0
        t0 = (day-1)*24
        t24 = day*24
        for hour in range(t0,t24):
            balance = balance + freshw[hour]
        if balance >0 :
            flowday = balance/(3600) #in m3/s
            Energy_hourWh = (gv.hf*(nf-5))/0.6*gv.Pwater*gv.gr*(flowday/gv.hoursop)/gv.effi
            for t in range(1,gv.hoursop+1):
                time = t0 + 11 + t
                Eaux_fw[time] = Energy_hourWh
    return Eaux_fw

def calc_Eaux_ve(Qhsf,Qcsf,P_ve, qve, SystemH, SystemC, Af):
    if SystemH == 'T3':
        if Qhsf >0: 
            Eve_aux = P_ve*qve*3600
        else: 
            Eve_aux = 0.0
    elif SystemC == 'T3':
        if Qcsf <0:
            Eve_aux = P_ve*qve*3600
        else:
            Eve_aux = 0.0
    else:
        Eve_aux = 0.0
        
    return Eve_aux

