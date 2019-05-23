from __future__ import division
import numpy as np
import pandas as pd

from extract_demand_outputs import calc_w_from_rh
import cea.osmose.exergy_calculation as calc_Ex
import cea.osmose.auxiliary_functions as aux


def set_up_ex_df(results):

    # get boundary conditions
    T_ref_C = results['T_ext']
    w_ref_gperkg = results['w_ext']
    w_ref_sat_gperkg = aux.calc_w_ss_from_T(T_ref_C) * 1000
    results['rh_RA'] = 0.6 # humidity set point
    w_RA_gperkg = np.vectorize(calc_w_from_rh)(results['rh_RA'] * 100, results['T_RA'])  # g/kg d.a.

    ## minimum exergy requirement
    # exergy of sensible heat transfer
    Ex_Qc_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_bui'], results['T_RA'], T_ref_C)
    # exergy of moist air
    ex_air_in = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['T_ext'], results['w_ext'], T_ref_C,
                                                              w_ref_sat_gperkg)
    ex_air_out = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['T_RA'], w_RA_gperkg, T_ref_C, w_ref_sat_gperkg)
    Ex_air_kWh = results['m_ve_min'] * (ex_air_out - ex_air_in)
    # exergy of water
    m_w_RA_kg = np.vectorize(calc_m_w_in_air)(results['M_dryair'], w_RA_gperkg)
    m_w_removed_kgpers = np.vectorize(m_w_removed_min)(results['m_ve_min'], results['w_ext'], w_RA_gperkg,
                                                       results['m_w_occ'], m_w_RA_kg)
    T_water_C = results['T_ext']
    rh_ref = results['rh_ext']
    ex_w_in_kJperkg = np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_RA'], T_ref_C, rh_ref)
    ex_w_out_kJperkg = np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_RA'], T_ref_C, rh_ref)
    Ex_w_kWh = m_w_removed_kgpers * ex_w_out_kJperkg - (results['m_w_occ'] / 1000) * ex_w_in_kJperkg
    # total
    Ex_tot_kWh = Ex_Qc_kWh + Ex_air_kWh + Ex_w_kWh

    ## exergy destruction at building interface


    # ex_df
    ex_df = pd.DataFrame()
    ex_df['Ex_Qc'] = Ex_Qc_kWh
    ex_df['Ex_air'] = Ex_air_kWh.values
    ex_df['Ex_water'] = Ex_w_kWh.values

    return ex_df


def calc_qc_loads(results, humidity_df, heat_df):

    results['m_w_oau_removed'] = humidity_df['m_w_oau_removed']
    results['m_w_lcu_removed'] = humidity_df['m_w_lcu_removed']
    results['m_w_tot_removed'] = humidity_df['m_w_oau_removed'] + humidity_df['m_w_lcu_removed']

    results['q_lcu_sen_load'] = heat_df['q_lcu_sen']
    results['q_oau_sen_load'] = heat_df['q_oau_sen']

    h_fg = 2501  # kJ/kg
    results['q_tot_sen_load'] = heat_df['q_scu_sen'] + heat_df['q_lcu_sen'] + heat_df['q_oau_sen']
    results['q_tot_lat_load'] = results['m_w_tot_removed']* h_fg
    results['q_tot_load'] = results['q_tot_sen_load'] + results['q_tot_lat_load']

    # h_fg = 2501 / 1000  # kJ/kg
    # h_T_RA_w_RA = np.vectorize(calc_h_from_T_w)(results['T_RA'], hu_store_df['w'])
    # results['w_RA'] = 10.29 #hu_store_df['w']
    # # OAU
    # # sen
    # OAU_h_T_SA_w_RA = np.vectorize(calc_h_from_T_w)(operation_df['T_SA'], results['w_RA'])
    # results['q_oau_sen_load'] = air_flow_df['OAU_in'] * (h_T_RA_w_RA - OAU_h_T_SA_w_RA)
    # # lat
    # OAU_w_SA = operation_df['w_SA']
    # OAU_m_w_removed = air_flow_df['OAU_in']*(results['w_RA'] - OAU_w_SA)/1000  # kg/hr
    # results['m_w_removed_oau'] = OAU_m_w_removed  # kJ/s = kW
    # # RAU
    # RAU_T_SA = 10.27
    # RAU_w_SA = calc_w_ss_from_T(RAU_T_SA)  #
    # RAU_w_RA = results['w_oau_out'] * 1000 / results['m_oau_out']  # g/kg
    # m_RAU = results['w_lcu'] / ((RAU_w_RA - RAU_w_SA) / 1000)
    # # sen
    # RAU_h_T_SA_w_RA = np.vectorize(calc_h_from_T_w)(RAU_T_SA, results['w_RA'])
    # results['q_rau_sen_load'] = m_RAU * (h_T_RA_w_RA - RAU_h_T_SA_w_RA)
    # # lat
    # RAU_m_w_removed = m_RAU * (results['w_RA'] - RAU_w_SA)/1000 # kg/hr
    # results['m_w_removed_rau'] = RAU_m_w_removed

    return results


def calc_m_w_in_air(M_air_room_kg, w_RA_gperkg):
    m_w_RA_kg = M_air_room_kg * w_RA_gperkg / 1000
    return m_w_RA_kg


def m_w_removed_min(m_ve_min, w_ext, w_RA, m_w_occ, m_w_RA_kg):
    m_w_air_in_kg = m_ve_min * w_ext / 1000
    m_w_air_out_kg = m_ve_min * w_RA / 1000
    m_w_occ_kg = m_w_occ
    m_w_removed_min_kg = m_w_air_in_kg - m_w_air_out_kg + m_w_occ_kg
    return m_w_removed_min_kg