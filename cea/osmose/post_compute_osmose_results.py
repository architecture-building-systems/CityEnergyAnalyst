from __future__ import division
import numpy as np
import pandas as pd

from extract_demand_outputs import calc_w_from_rh
import cea.osmose.exergy_functions as calc_Ex
import cea.osmose.auxiliary_functions as aux


def set_up_ex_df(results, operation_df, electricity_df, air_flow_df):

    # get boundary conditions
    T_ref_C = results['T_ext'].values
    w_ref_gperkg = results['w_ext'].values
    w_ref_sat_gperkg = aux.calc_w_ss_from_T(T_ref_C)
    results['rh_RA'] = 0.6  # humidity set point
    w_RA_gperkg = np.vectorize(calc_w_from_rh)(results['rh_RA'] * 100, results['T_RA'])  # g/kg d.a.
    # exergy of moist air (indoor/outdoor)
    ex_air_ext = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['T_ext'], results['w_ext'], T_ref_C,
                                                               w_ref_sat_gperkg)  # kJ/kg
    ex_air_int = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['T_RA'], w_RA_gperkg, T_ref_C, w_ref_sat_gperkg)

    ## minimum exergy requirement (theoretical)
    Ex_min_Qc_kWh, Ex_min_air_kWh, Ex_min_w_kWh, rh_ref = calc_theoretical_Ex_requirement(T_ref_C, ex_air_ext,
                                                                                          ex_air_int, results,
                                                                                          w_RA_gperkg)
    ## exergy destruction at building interface
    oau_Ex_total_kWh, rau_EX_air_kWh, rau_Ex_w_kWh, scu_Ex_kWh = calc_process_Ex_requirement(T_ref_C,
                                                                                             air_flow_df,
                                                                                             ex_air_ext,
                                                                                             ex_air_int,
                                                                                             operation_df,
                                                                                             results,
                                                                                             rh_ref,
                                                                                             w_RA_gperkg,
                                                                                             w_ref_sat_gperkg)
    ## Exergy of cooling/heating utilities
    if results.filter(like='q_oau_chi').size == 0:
        oau_Ex_c_kWh = np.nan_to_num(np.vectorize(calc_Ex.calc_Ex_Qc)(results['Qc_de'], results['T_s_i_de']-273.15, T_ref_C))
        oau_Ex_h_kWh = np.nan_to_num(np.vectorize(calc_Ex.calc_Ex_Qh)(results['Qh_re'], 44.3, T_ref_C))
    else:
        oau_Ex_c_kWh = np.nan_to_num(np.vectorize(calc_Ex.calc_Ex_Qc)(results.filter(like='q_oau_chi').sum(axis=1), results['T_evap'], T_ref_C))
        oau_Ex_h_kWh = results['q_reheat'].values
    rau_Ex_c_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_coi_lcu'], 7, T_ref_C)
    scu_Ex_c_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_coi_scu'], 16, T_ref_C)

    # ex_df
    ex_df = pd.DataFrame()
    ex_df['Ex_min_Qc'] = Ex_min_Qc_kWh
    ex_df['Ex_min_air'] = Ex_min_air_kWh
    ex_df['Ex_min_water'] = Ex_min_w_kWh
    ex_df['Ex_min_total'] = ex_df.filter(like='Ex_min').sum(axis=1)
    ex_df['Ex_process_OAU'] = oau_Ex_total_kWh
    ex_df['Ex_process_RAU'] = rau_EX_air_kWh + rau_Ex_w_kWh
    ex_df['Ex_process_SCU'] = scu_Ex_kWh
    ex_df['Ex_process_total'] = ex_df.filter(like='Ex_process').sum(axis=1)
    ex_df['Ex_utility_OAU'] = oau_Ex_c_kWh + oau_Ex_h_kWh
    ex_df['Ex_utility_RAU'] = rau_Ex_c_kWh
    ex_df['Ex_utility_SCU'] = scu_Ex_c_kWh
    ex_df['Ex_utility_total'] = ex_df.filter(like='Ex_utility').sum(axis=1)
    el_total = electricity_df.sum(axis=1).values
    ex_df['eff_exergy'] = ex_df['Ex_min_total'] / el_total
    ex_df['eff_process_exergy'] = ex_df['Ex_process_total'] / el_total
    ex_df['eff_utility_exergy'] = ex_df['Ex_utility_total'] / el_total
    ex_df = ex_df.set_index(np.arange(1, ex_df.shape[0]+1, 1))
    return ex_df


# def calc_process_Ex_requirement(T_ref_C, air_flow_df, ex_air_ext, ex_air_int, operation_df, results, rh_ref,
#                                 w_RA_gperkg, w_ref_sat_gperkg):
#     # OAU
#     oau_ex_air_in = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(operation_df['T_SA'], operation_df['w_SA'], T_ref_C,
#                                                                   w_ref_sat_gperkg)
#     oau_Ex_air_kWh = np.nan_to_num((air_flow_df['OAU_in'] * (oau_ex_air_in - ex_air_ext)).values)
#     oau_ex_w_cond_kJperkg = np.nan_to_num(np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_chw'], T_ref_C, rh_ref))
#     oau_Ex_w_kWh = np.nan_to_num(results['m_w_coil_cond'].values * oau_ex_w_cond_kJperkg)
#     # RAU
#     rau_T_SA = 10.27
#     rau_w_SA = aux.calc_w_ss_from_T(rau_T_SA)
#     rau_ex_air_in = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(rau_T_SA, rau_w_SA, T_ref_C, w_ref_sat_gperkg)
#     m_RAU_kgpers = results['w_lcu'] * 1000 / (w_RA_gperkg - rau_w_SA)
#     rau_EX_air_kWh = np.nan_to_num((m_RAU_kgpers * (rau_ex_air_in - ex_air_int)).values)
#     rau_ex_w_cond_kJperkg = np.nan_to_num(np.vectorize(calc_Ex.calc_exergy_liquid_water)(rau_T_SA, T_ref_C, rh_ref))
#     rau_Ex_w_kWh = (results['w_lcu'] * rau_ex_w_cond_kJperkg).values
#     # SCU
#     scu_T_SA = 20
#     scu_Ex_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_scu_sen'], scu_T_SA, T_ref_C)
#     return oau_Ex_air_kWh, oau_Ex_w_kWh, rau_EX_air_kWh, rau_Ex_w_kWh, scu_Ex_kWh

def calc_process_Ex_requirement(T_ref_C, air_flow_df, ex_air_ext, ex_air_int, operation_df, results, rh_ref,
                                w_RA_gperkg, w_ref_sat_gperkg):
    # OAU
    oau_Ex_air_kWh, oau_Ex_w_kWh, oau_Ex_total_kWh = calc_OAU_process_Ex(T_ref_C, air_flow_df, ex_air_ext, operation_df,
                                                                         results, rh_ref, w_ref_sat_gperkg)
    # RAU
    rau_EX_air_kWh, rau_Ex_w_kWh = calc_RAU_process_Ex(T_ref_C, ex_air_int, results, rh_ref, w_RA_gperkg, w_ref_sat_gperkg)
    # SCU
    scu_T_SA = 20
    scu_Ex_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_scu_sen'], scu_T_SA, T_ref_C)
    return oau_Ex_total_kWh, rau_EX_air_kWh, rau_Ex_w_kWh, scu_Ex_kWh


def calc_RAU_process_Ex(T_ref_C, ex_air_int, results, rh_ref, w_RA_gperkg, w_ref_sat_gperkg):
    rau_T_SA = 10.27
    rau_w_SA = aux.calc_w_ss_from_T(rau_T_SA)
    rau_ex_air_in = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(rau_T_SA, rau_w_SA, T_ref_C, w_ref_sat_gperkg)
    m_RAU_kgpers = results['w_lcu'].values * 1000 / (w_RA_gperkg - rau_w_SA)
    rau_EX_air_kWh = np.nan_to_num(m_RAU_kgpers * (rau_ex_air_in - ex_air_int))
    rau_ex_w_cond_kJperkg = np.nan_to_num(np.vectorize(calc_Ex.calc_exergy_liquid_water)(rau_T_SA, T_ref_C, rh_ref))
    rau_Ex_w_kWh = results['w_lcu'].values * rau_ex_w_cond_kJperkg
    return rau_EX_air_kWh, rau_Ex_w_kWh


def calc_OAU_process_Ex(T_ref_C, air_flow_df, ex_air_ext, operation_df, results, rh_ref, w_ref_sat_gperkg):
    # ex of air
    oau_ex_air_in = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(operation_df['T_SA'], operation_df['w_SA'], T_ref_C,
                                                                  w_ref_sat_gperkg)
    oau_ex_air_RA = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['T_RA'], 10.29, T_ref_C, w_ref_sat_gperkg)
    oau_ex_air_EA = np.vectorize(calc_Ex.calc_exergy_moist_air_2)(results['OAU_T_EA'].values,
                                                                  results['OAU_w_EA'].values,
                                                                  T_ref_C, w_ref_sat_gperkg)
    # Ex of air
    oau_Ex_air_kWh = np.nan_to_num((air_flow_df['OAU_in'] * (oau_ex_air_in - ex_air_ext)).values)
    oau_Ex_air_exhaust_kWh = np.nan_to_num((results['m_oau_out'] * (oau_ex_air_EA - oau_ex_air_RA)).values)
    # ex of water
    oau_ex_w_cond_kJperkg = np.nan_to_num(
        np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_chw'].values, T_ref_C, rh_ref))
    oau_ex_w_RA_kJperkg = np.nan_to_num(
        np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_RA'].values, T_ref_C, rh_ref))
    oau_Ex_w_removed_kWh_dict = {}
    for i in range(results.filter(like='T_w_removed').columns.size):
        oau_ex_w_removed = np.nan_to_num(np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_w_removed_'+str(i+1)], T_ref_C, rh_ref))
        oau_Ex_w_removed_kWh_dict['Ex_w_removed_'+str(i+1)] = np.nan_to_num(results['m_w_removed_'+str(i+1)].values * oau_ex_w_removed)
    # Ex of water
    oau_Ex_w_kWh = np.nan_to_num(results['m_w_coil_cond'].values * oau_ex_w_cond_kJperkg)
    if len(oau_Ex_w_removed_kWh_dict.keys()) > 0:
        oau_Ex_w_removed_kWh = sum(oau_Ex_w_removed_kWh_dict.values())
    else:
        oau_Ex_w_removed_kWh = np.zeros(results.shape[0])
    oau_Ex_w_add_kWh = np.nan_to_num(results['m_w_add'].values * oau_ex_w_RA_kJperkg)
    # total balance
    oau_Ex_total_kWh = oau_Ex_air_kWh + oau_Ex_air_exhaust_kWh + oau_Ex_w_kWh + oau_Ex_w_removed_kWh - oau_Ex_w_add_kWh
    oau_Ex_total_in_kWh = oau_Ex_air_kWh + oau_Ex_w_kWh
    return oau_Ex_air_kWh, oau_Ex_w_kWh, oau_Ex_total_kWh


def calc_theoretical_Ex_requirement(T_ref_C, ex_air_ext, ex_air_int, results, w_RA_gperkg):
    # exergy of sensible heat transfer
    Ex_min_Qc_kWh = np.vectorize(calc_Ex.calc_Ex_Qc)(results['q_bui'], results['T_RA'], T_ref_C)
    Ex_min_Qc_kWh = np.where(Ex_min_Qc_kWh < 0, 0, Ex_min_Qc_kWh)  # TODO: check results
    # exergy of moist air
    Ex_min_air_kWh = (results['m_ve_min'] * (ex_air_int - ex_air_ext)).values
    # exergy of water
    m_w_RA_kg = np.vectorize(calc_m_w_in_air)(results['M_dryair'], w_RA_gperkg)
    m_w_removed_kgpers = np.vectorize(m_w_removed_min)(results['m_ve_min'], results['w_ext'], w_RA_gperkg,
                                                       results['m_w_occ'], m_w_RA_kg)
    T_water_C = results['T_ext']
    rh_ref = results['rh_ext'].values
    ex_w_in_kJperkg = np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_RA'], T_ref_C, rh_ref)
    ex_w_out_kJperkg = np.vectorize(calc_Ex.calc_exergy_liquid_water)(results['T_RA'], T_ref_C, rh_ref)
    Ex_min_w_kWh = (m_w_removed_kgpers * ex_w_out_kJperkg - (results['m_w_occ'] / 1000) * ex_w_in_kJperkg).values
    return Ex_min_Qc_kWh, Ex_min_air_kWh, Ex_min_w_kWh, rh_ref


def calc_qc_loads(results, humidity_df, heat_df):
    results['m_w_oau_removed'] = humidity_df['m_w_oau_removed']
    results['m_w_lcu_removed'] = humidity_df['m_w_lcu_removed']
    results['m_w_tot_removed'] = humidity_df['m_w_oau_removed'] + humidity_df['m_w_lcu_removed']

    results['q_lcu_sen_load'] = heat_df['q_lcu_sen']
    results['q_oau_sen_load'] = heat_df['q_oau_sen']

    h_fg = 2501  # kJ/kg
    results['q_tot_sen_load'] = heat_df['q_scu_sen'] + heat_df['q_lcu_sen'] + heat_df['q_oau_sen']
    results['q_tot_lat_load'] = results['m_w_tot_removed'] * h_fg
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


