from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import math
from extract_demand_outputs import calc_m_dry_air


# from cea.plots.demand.comfort_chart import p_w_from_rh_p_and_ws, p_ws_from_t, hum_ratio_from_p_w_and_p


def check_balance(results, building, building_result_path, tech):
    # Bui_energy_bal
    check_bui_energy_bal(results, building, building_result_path, tech)
    # Bui_water_bal
    check_bui_water_bal(results, building, building_result_path, tech)
    # Bui_air_bal
    check_bui_air_bal(results, building, building_result_path, tech)

    check_electricity_bal(results, building, building_result_path, tech)

    return np.nan


def check_electricity_bal(results, building, building_result_path, tech):
    Electricity_IN = results['SU_elec']
    Electricity_OUT = results['el_oau_out_fan'] + results['el_scu_pump'] + results['el_chi_ht'] + \
                      results['el_lcu_fan'] + results['el_chi_lt'] + \
                      results.filter(like='el_oau_in').sum(axis=1) + \
                      results.filter(like='el_oau_chi').sum(axis=1) + results['el_ct']
    Electricity_bal = Electricity_IN - Electricity_OUT
    if abs(Electricity_bal.sum()) >= 1:
        print('Electriicty_bal not zero...')

        el_IN_dict = {}
        el_IN_dict['grid'] = results['SU_elec']

        el_OUT_dict = {}
        el_OUT_dict['el_oau_out_fan'] = results['el_oau_out_fan']
        el_OUT_dict['SCU'] = results['el_scu_pump'] + results['el_chi_ht']
        el_OUT_dict['LCU'] = results['el_lcu_fan'] + results['el_chi_lt']
        el_OUT_dict['el_oau_in'] = results.filter(like='el_oau_in').sum(axis=1)
        el_OUT_dict['el_oau_chi'] = results.filter(like='el_oau_chi').sum(axis=1)
        el_OUT_dict['el_ct Towers'] = results['el_ct']

        name = 'el_bal'
        plot_stacked_bars_side_by_side(el_IN_dict, el_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)
    return np.nan



def check_bui_air_bal(results, building, building_result_path, tech):
    Bui_air_bal_IN = results['m_inf_in'] + results.filter(like='m_oau_in').sum(axis=1) + results['SU_vent']
    Bui_air_bal_OUT = results['m_oau_out'] + results['SU_exhaust']
    Bui_air_bal = Bui_air_bal_IN - Bui_air_bal_OUT
    if abs(Bui_air_bal.sum()) >= 1e-3:
        print ('Bui_air_bal not zero...')

        # plot
        air_IN_dict = {}
        air_IN_dict['m_inf_in'] = results['m_inf_in']
        air_IN_dict['m_oau_in'] = results.filter(like='m_oau_in').sum(axis=1)
        air_IN_dict['SU_vent'] = results['SU_vent']

        air_OUT_dict = {}
        air_OUT_dict['m_oau_out'] = results['m_oau_out']
        air_OUT_dict['SU_exhaust'] = results['SU_exhaust']

        name = 'bui_air_bal'
        plot_stacked_bars_side_by_side(air_IN_dict, air_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)
    return np.nan


def check_bui_water_bal(results, building, building_result_path, tech):
    Bui_water_bal_IN = results['w_oau_out'] + results['w_lcu'] + results['w_sto_charge'] + results['SU_dhu']
    Bui_water_bal_OUT = results['w_bui'] + results.filter(like='w_oau_in').sum(axis=1) + results['w_sto_discharge'] \
                        + results['SU_hu']
    Bui_water_bal = Bui_water_bal_IN - Bui_water_bal_OUT
    if abs(Bui_water_bal.sum()) >= 1e-3:
        print ('Bui_water_bal not zero...')

        water_IN_dict = {}
        water_IN_dict['w_oau_out'] = results['w_oau_out']
        water_IN_dict['w_lcu'] = results['w_lcu']
        water_IN_dict['w_sto_charge'] = results['w_sto_charge']
        water_IN_dict['SU_dhu'] = results['SU_dhu']

        water_OUT_dict = {}
        water_OUT_dict['w_bui'] = results['w_bui']
        water_OUT_dict['w_oau_in'] = results.filter(like='w_oau_in').sum(axis=1)
        water_OUT_dict['w_sto_discharge'] = results['w_sto_discharge']
        water_OUT_dict['SU_hu'] = results['SU_hu']

        name = 'bui_water_bal'
        plot_stacked_bars_side_by_side(water_IN_dict, water_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)

    return np.nan


def check_bui_energy_bal(results, building, building_result_path, tech):
    Bui_energy_bal_IN = results['q_bui'] + results.filter(like='q_oau_sen_in').sum(axis=1) + results.filter(
        like='SU_Qh').sum(axis=1)
    Bui_energy_bal_OUT = results['q_oau_sen_out'] + results['q_scu_sen'] + results['q_lcu_sen'] + results.filter(
        like='SU_Qc').sum(axis=1)
    Bui_energy_bal = Bui_energy_bal_IN - Bui_energy_bal_OUT
    if abs(Bui_energy_bal.sum()) >= 1e-2:
        print('Bui_energy_bal not zero...')

        energy_IN_dict = {}
        energy_IN_dict['q_bui'] = results['q_bui']
        energy_IN_dict['q_oau_sen_in'] = results.filter(like='q_oau_sen_in').sum(axis=1)
        energy_IN_dict['SU_Qh'] = results.filter(like='SU_Qh').sum(axis=1)
        energy_OUT_dict = {}
        energy_OUT_dict['q_oau_sen_out'] = results['q_oau_sen_out']
        energy_OUT_dict['q_scu_sen'] = results['q_scu_sen']
        energy_OUT_dict['q_lcu_sen'] = results['q_lcu_sen']
        energy_OUT_dict['SU_Qc'] = results.filter(like='SU_Qc').sum(axis=1)

        name = 'bui_energy_bal'
        plot_stacked_bars_side_by_side(energy_IN_dict, energy_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)

    return np.nan


def plot_stacked_bars_side_by_side(left_stack_dict, right_stack_dict, length, building, building_result_path, tech,
                                   name):
    # plotting
    fig, ax = plt.subplots()
    bar_width = 0.3
    x_ticks = np.arange(length) + 1
    # left stack
    x_axis_left = x_ticks - 0.2
    y_offset = np.zeros(length)
    colors = ['#AD4456', '#D76176', '#E3909F', '#742D3A', '#270F14', '#FF4B31']  # PINKS
    c = 0
    for key in left_stack_dict.keys():
        ax.bar(x_axis_left, left_stack_dict[key], bar_width, bottom=y_offset, label=key, color=colors[c])
        y_offset = y_offset + left_stack_dict[key]
        c = c + 1
    y_max = y_offset.max()
    # right stack
    x_axis_right = x_ticks + 0.2
    y_offset = np.zeros(length)
    colors = ['#29465A', '#39617E', '#718C60', '#77AACF', '#111C24', '#507C88']  # BLUES
    c = 0
    for key in right_stack_dict.keys():
        ax.bar(x_axis_right, right_stack_dict[key], bar_width, bottom=y_offset, label=key, color=colors[c])
        y_offset = y_offset + right_stack_dict[key]
        c = c + 1
    y_max = max(y_offset.max(), y_max)
    # plot settings
    ax.set_xticks(x_ticks)
    # put legend to the right
    ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5))
    ax.set(xlabel='Time [hr]', ylabel=name, ylim=(0, y_max + 0.05 * y_max))
    # plt.show()

    plt.title(building + "_" + tech)
    fig.savefig(path_to_save_fig(building, building_result_path, tech, name), bbox_inches="tight")

    return np.nan


def main(building, TECHS, building_result_path):
    el_use_sum = {}
    for tech in TECHS:
        results = pd.read_csv(path_to_osmose_results(building_result_path, tech), header=None).T.reset_index()
        results = results.rename(columns=results.iloc[0])[1:]
        results = results.fillna(0)
        el_use_sum[tech] = results['SU_elec'].sum()

        # check balance
        print 'checking balance for: ', tech
        check_balance(results, building, building_result_path, tech)

        if tech in ['HCS_coil', 'HCS_3for2', 'HCS_ER0', 'HCS_IEHX']:
            chiller_count = analysis_chilled_water_usage(results, tech)
            chiller_count.to_csv(path_to_chiller_csv(building, building_result_path, tech))

        ## plot air flows
        air_flow_df = set_up_air_flow_df(results)
        plot_air_flow(air_flow_df, results, tech, building, building_result_path)

        ## plot T_SA and w_SA
        operation_df = set_up_operation_df(tech, results)
        plot_supply_temperature_humidity(building, building_result_path, operation_df, tech)

        ## plot water balance
        humidity_df = set_up_humidity_df(tech, results)
        plot_water_balance(building, building_result_path, humidity_df, results, tech)
        # plot_water_in_out(building, building_result_path, humidity_df, results, tech) # TODO: to be finished

        ## plot humidity level (storage)
        hu_store_df = set_up_hu_store_df(results)
        plot_hu_store(building, building_result_path, hu_store_df, tech)

        ## plot heat balance
        heat_df = set_up_heat_df(tech, results)
        plot_heat_balance(building, building_result_path, heat_df, results, tech)

        ## plot electricity usage
        plot_electricity_usage(building, building_result_path, results, tech)
        electricity_df = set_up_electricity_df(tech, results)
        calc_el_stats(building, building_result_path, electricity_df, results, tech)
        plot_electricity_usages(building, building_result_path, electricity_df, results, tech)

    print el_use_sum
    return


def analysis_chilled_water_usage(results, tech):
    chiller_usage = results.filter(like='el_oau_chi').fillna(0).astype(bool).sum()
    T_low_C = 8.1
    T_high_C = 14.1
    T_interval = 0.65  # 0.5
    T_OAU_offcoil = np.arange(T_low_C, T_high_C, T_interval)
    count_chiller_usage = chiller_usage[chiller_usage > 0]
    total_count = float(count_chiller_usage.sum())
    chiller_in_use = count_chiller_usage.keys()
    T_chillers = {}
    chiller_occurance = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0}
    for chiller in chiller_in_use:
        chiller_number = int(chiller.split('chi')[1].split('_')[0])
        if chiller_occurance[str(chiller_number)] == 0:
            T_chillers[T_OAU_offcoil[chiller_number - 1]] = ((count_chiller_usage[chiller] / total_count) * 100)
        else:
            T_chillers[T_OAU_offcoil[chiller_number - 1]] = T_chillers[T_OAU_offcoil[chiller_number - 1]] + (
                    (count_chiller_usage[chiller] / total_count) * 100)
        chiller_occurance[str(chiller_number)] += 1
    T_chillers_df = pd.DataFrame(T_chillers, index=[tech])
    return T_chillers_df


def set_up_hu_store_df(results):
    hu_store_df = pd.DataFrame()
    hu_store_df['humidity_ratio'] = results['hu_storage'] * 3600 / results['M_dryair'] * 1000  # g/kg d.a.
    hu_store_df['relative_humidity'] = np.vectorize(calc_RH_from_w)(hu_store_df['humidity_ratio'],
                                                                    results['T_RA']) * 100
    return hu_store_df


def calc_RH_from_w(w_gperkg, T_C):
    T_K = 273.15 + T_C
    C_gKperJ = 2.16679
    P_ws_Pa = p_ws_from_t(T_C)  # T in Celcius
    rho_air_kgperm3 = 1.19  # kg/m3
    rh = w_gperkg * rho_air_kgperm3 * T_K / (C_gKperJ * P_ws_Pa)
    return rh


def set_up_electricity_df(tech, results):
    electricity_df = pd.DataFrame()
    # lcu
    electricity_df['el_chi_lt'] = results['el_chi_lt']
    electricity_df['el_aux_lcu'] = results['el_lcu_fan']
    # oau
    if tech == 'HCS_LD':
        electricity_df['el_aux_oau'] = results.filter(like='el_oau_in').sum(axis=1) + results['el_oau_out_fan']
        electricity_df['el_hp_oau'] = results['el_LDHP']
    else:
        electricity_df['el_aux_oau'] = results.filter(like='el_oau_in').sum(axis=1) + results['el_oau_out_fan']
        electricity_df['el_chi_oau'] = results.filter(like='el_oau_chi').sum(axis=1)

    # scu
    electricity_df['el_chi_ht'] = results['el_chi_ht']
    electricity_df['el_aux_scu'] = results['el_scu_pump']
    # ct
    electricity_df['el_ct'] = results['el_ct']

    balance = electricity_df.sum(axis=1) - results['SU_elec']
    balance = balance[abs(balance) > 1e-2]
    if abs(balance.sum()) > 1:
        print('electricity balance:', balance)

    return electricity_df


# def set_up_electricity_per_area_df(tech, results, building):
#     electricity_df = pd.DataFrame()
#     # lcu
#     electricity_df['el_chi_lt'] = results['el_chi_lt'] * 1000 / Af_m2[building]
#     electricity_df['el_aux_lcu'] = results['el_lcu_fan'] * 1000 / Af_m2[building]
#     # oau
#     if tech == 'HCS_LD':
#         total_el_aux_oau = results['el_oau_in_fan'] + results['el_oau_out_fan']
#         electricity_df['el_hp_oau'] = results['el_LDHP'] * 1000 / Af_m2[building]
#     else:
#         total_el_aux_oau = results['el_oau_in1_fan'] + results['el_oau_in2_fan'] + results['el_oau_in3_fan'] + results[
#             'el_oau_out_fan']
#         electricity_chi_oau = 0
#         for i in range(3):
#             for j in range(10):
#                 tag_name = 'el_oau_chi' + str(i + 1) + '_' + str(j + 1)
#                 electricity_chi_oau = electricity_chi_oau + results[tag_name]
#         electricity_df['el_chi_oau'] = electricity_chi_oau * 1000 / Af_m2[building]
#     electricity_df['el_aux_oau'] = total_el_aux_oau * 1000 / Af_m2[building]
#
#     # scu
#     electricity_df['el_chi_ht'] = results['el_chi_ht'] * 1000 / Af_m2[building]
#     electricity_df['el_aux_scu'] = results['el_scu_pump'] * 1000 / Af_m2[building]
#     # ct
#     electricity_df['el_ct'] = results['el_ct'] * 1000 / Af_m2[building]
#
#     return electricity_df


def calc_el_stats(building, building_result_path, electricity_df, results, tech):
    output_df = electricity_df.copy()
    # calculate electricity used in each technology
    output_df['el_total'] = output_df.sum(axis=1)
    output_df['el_scu'] = output_df['el_aux_scu'] + output_df['el_chi_ht']
    output_df['el_lcu'] = output_df['el_aux_lcu'] + output_df['el_chi_lt']
    if tech == 'HCS_LD':
        output_df['el_oau'] = output_df['el_aux_oau'] + output_df['el_hp_oau']
    else:
        output_df['el_oau'] = output_df['el_aux_oau'] + output_df['el_chi_oau']
    # calculate total cooling energy produced
    cooling_df = calc_cooling_energy(results)
    # output_df['qc_bui_sen_total'] = cooling_df.filter(like='qc_bui_sen').sum(axis=1)
    # output_df['qc_bui_lat_total'] = cooling_df.filter(like='qc_bui_lat').sum(axis=1)
    output_df['qc_sys_scu'] = cooling_df['qc_sys_sen_scu']
    output_df['qc_sys_lcu'] = cooling_df['qc_sys_sen_lcu'] + cooling_df['qc_sys_lat_lcu']
    output_df['qc_sys_oau'] = cooling_df['qc_sys_sen_oau'] + cooling_df['qc_sys_lat_oau']
    output_df['qc_sys_sen_total'] = cooling_df.filter(like='qc_sys_sen').sum(axis=1)
    output_df['qc_sys_lat_total'] = cooling_df.filter(like='qc_sys_lat').sum(axis=1)

    # add total row in the bottom
    total_df = pd.DataFrame(output_df.sum()).T
    output_df = output_df.append(total_df).reset_index().drop(columns='index')

    # calculate values from column operations
    # output_df['qc_bui_total'] = output_df['qc_bui_sen_total'] + output_df['qc_bui_lat_total']
    # output_df['cop_cooling'] = output_df['qc_bui_total'] / output_df['el_total']
    output_df['qc_sys_total'] = output_df['qc_sys_sen_total'] + output_df['qc_sys_lat_total']
    output_df['SHR'] = output_df['qc_sys_sen_total'] / output_df['qc_sys_total']  # sensible heat ratio
    output_df['qc_Wh_sys_per_Af'] = output_df['qc_sys_total'] * 1000 / results.iloc[0]['Af_m2']
    output_df['cop_system'] = output_df['qc_sys_total'] / output_df['el_total']
    # calc system mean cop
    index = output_df.shape[0] - 1
    cop_system_mean = output_df['cop_system'].ix[0:index - 1].replace(0, np.nan).mean(skipna=True)
    output_df['cop_system_mean'] = output_df['cop_system']
    output_df.at[index, 'cop_system_mean'] = cop_system_mean
    # output_df = output_df.set_value(index, 'cop_system_mean', cop_system_mean)
    # output_df['cop_scu'] = output_df['qc_sys_scu']/output_df['el_scu']
    # output_df['cop_lcu'] = output_df['qc_sys_lcu']/output_df['el_lcu']
    # output_df['cop_oau'] = output_df['qc_sys_oau']/output_df['el_oau']

    # calculate the percentage used by each component
    output_df['scu'] = output_df['el_chi_ht'] / output_df['el_total'] * 100
    output_df['scu_aux'] = output_df['el_aux_scu'] / output_df['el_total'] * 100
    output_df['lcu'] = output_df['el_chi_lt'] / output_df['el_total'] * 100
    output_df['lcu_aux'] = output_df['el_aux_lcu'] / output_df['el_total'] * 100
    if tech == 'HCS_LD':
        output_df['oau'] = output_df['el_hp_oau'] / output_df['el_total'] * 100
        output_df['oau_aux'] = output_df['el_aux_oau'] / output_df['el_total'] * 100
    else:
        output_df['oau'] = output_df['el_chi_oau'] / output_df['el_total'] * 100
        output_df['oau_aux'] = output_df['el_aux_oau'] / output_df['el_total'] * 100
    output_df['ct'] = output_df['el_ct'] / output_df['el_total'] * 100

    # export results
    output_df.to_csv(path_to_elec_csv(building, building_result_path, tech))
    return np.nan


def calc_cooling_energy(results):
    cooling_df = pd.DataFrame()
    # suppress to check calculation
    # cooling_df['qc_bui_sen_scu'] = results['q_scu_sen']
    # cooling_df['qc_bui_sen_lcu'] = results['q_lcu_sen']
    # cooling_df['qc_bui_sen_oau'] = results.filter(like='oau_Qc_bui_sen').sum(axis=1)
    # cooling_df['qc_bui_lat_lcu'] = results['q_coi_lcu'] - results['q_lcu_sen']
    # cooling_df['qc_bui_lat_oau'] = results.filter(like='oau_Qc_bui_total').sum(axis=1) - results.filter(
    #     like='oau_Qc_bui_sen').sum(axis=1)

    cooling_df['qc_sys_sen_scu'] = results['q_coi_scu']
    cooling_df['qc_sys_sen_lcu'] = results['q_lcu_sen']
    cooling_df['qc_sys_sen_oau'] = results.filter(like='oau_Qc_sen').sum(axis=1)
    cooling_df['qc_sys_lat_lcu'] = results['q_coi_lcu'] - results['q_lcu_sen']
    cooling_df['qc_sys_lat_oau'] = results.filter(like='oau_Qc_total').sum(axis=1) - results.filter(
        like='oau_Qc_sen').sum(axis=1)

    # check validity of results
    if cooling_df.min().min() < -1e3:
        columns = np.unique(np.where(cooling_df < 0)[1])
        names = []
        for i in columns:
            names.append(cooling_df.columns[i])
        raise ValueError('Check cooling results from osmose: ', ' ,'.join(names))
    if (abs(results['q_scu_sen'] - results['q_coi_scu']) < 1e3).all() == False:
        raise ValueError('Check SCU heat balance')

    return cooling_df


def set_up_heat_df(tech, results):
    heat_df = pd.DataFrame()
    heat_df['q_lcu_sen'] = results['q_lcu_sen']
    heat_df['q_scu_sen'] = results['q_scu_sen']
    if tech == 'HCS_LD':
        total_oau_in = results.filter(like='q_oau_sen_in').sum(axis=1)
        total_oau_out = results['q_oau_sen_out']
    else:
        total_oau_in = results.filter(like='q_oau_sen_in').sum(axis=1)
        total_oau_out = results['q_oau_sen_out']
        # q_bui_float = pd.to_numeric(results['q_bui']) + 0.01
    # total_oau_removed[total_oau_removed > q_bui_float] = 0
    total_oau = total_oau_out - total_oau_in
    heat_df['q_oau_sen'] = total_oau[total_oau >= 0]
    heat_df['q_oau_sen_add'] = total_oau[total_oau < 0] * (-1)
    heat_df = heat_df.fillna(0)

    # balance
    balance_in = results['q_bui'] + heat_df['q_oau_sen_add'] + results.filter(like='SU_Qh').sum(axis=1)
    balance_out = heat_df['q_lcu_sen'] + heat_df['q_scu_sen'] + heat_df['q_oau_sen'] + results.filter(like='SU_Qc').sum(
        axis=1)
    balance = balance_in - balance_out
    balance = balance[abs(balance) > 1e-2]
    if abs(balance.sum()) > 1E-3:
        print ('heat balance: ', balance)

    return heat_df


def set_up_humidity_df(tech, results):
    humidity_df = pd.DataFrame()
    # humidity_df['m_w_infil_occupant'] = results['w_bui']
    humidity_df['m_w_lcu_removed'] = results['w_lcu']
    if tech == 'HCS_LD':
        total_oau_in = results.filter(like='w_oau_in').sum(axis=1)
        total_oau_out = results['w_oau_out']
    else:
        total_oau_in = results.filter(like='w_oau_in').sum(axis=1)
        total_oau_out = results['w_oau_out']
    # total_oau_removed[total_oau_removed < 0] = 0 # FIXME: check graph
    total_oau = total_oau_out - total_oau_in
    humidity_df['m_w_oau_removed'] = total_oau[total_oau > 0]
    humidity_df['m_w_oau_added'] = total_oau[total_oau < 0] * (-1)
    humidity_df['m_w_stored'] = results['w_sto_charge']
    # humidity_df['m_w_discharged'] = results['w_sto_discharge']
    humidity_df = humidity_df.fillna(0)

    # test balance
    balance_in = results['w_bui'] + results['w_sto_discharge'] + humidity_df['m_w_oau_added'] + results['SU_hu']
    balance_out = humidity_df['m_w_lcu_removed'] + humidity_df['m_w_oau_removed'] + humidity_df['m_w_stored'] + results[
        'SU_dhu']
    balance = balance_in - balance_out
    balance = balance[abs(balance) > 1e-4]
    if abs(balance.sum()) > 1E-6:
        print ('humidity balance: ', balance)
    return humidity_df


def set_up_air_flow_df(results):
    air_flow_df = pd.DataFrame()
    air_flow_df['infiltration'] = results['m_inf_in']
    if 'm_oau_in_by' in results.columns:
        air_flow_df['OAU_in'] = results.filter(like='m_oau_in').drop(columns=['m_oau_in_by']).sum(axis=1)
        air_flow_df['OAU_in_bypass'] = results['m_oau_in_by']

        balance = air_flow_df['OAU_in'] + air_flow_df['OAU_in_bypass'] + air_flow_df['infiltration'] - results[
            'm_oau_out']

    else:
        air_flow_df['OAU_in'] = results.filter(like='m_oau_in').sum(axis=1)
        balance = air_flow_df['OAU_in'] + air_flow_df['infiltration'] - results['m_oau_out']

    # testing for balance
    if abs(balance.sum()) >= 1E-6:
        raise (ValueError, 'wrong air balance')
    return air_flow_df


def set_up_operation_df(tech, results):
    """
    construct a dataframe containing operating conditions of the oau (T,w)
    :param tech:
    :param results:
    :return:
    """

    operation_df = pd.DataFrame()
    if tech == 'HCS_LD':
        operation_df['T_SA'] = results['OAU_T_SA']
        operation_df['w_SA'] = results['OAU_w_SA']
    else:
        # output actual temperature and humidity
        number_oau_in = results.filter(like='OAU_T_SA').shape[1]
        for i in range(number_oau_in):
            m_label = 'm_oau_in_' + str(i + 1)
            T_label = 'OAU_T_SA' + str(i + 1)
            w_label = 'OAU_w_SA' + str(i + 1)
            results.ix[results[m_label] <= 0.01, T_label] = 0
            results.ix[results[m_label] <= 0.01, w_label] = 0
        operation_df['T_SA'] = results.filter(like='OAU_T_SA').sum(axis=1)
        operation_df['w_SA'] = results.filter(like='OAU_w_SA').sum(axis=1)

        number_oau_chillers = int(results.filter(like='cop_oau_chi').shape[1] / number_oau_in)
        for i in range(number_oau_in):
            for j in range(number_oau_chillers):
                cop_tag_name = 'cop_oau_chi' + str(i + 1) + '_' + str(j + 1)
                el_tag_name = 'el_oau_chi' + str(i + 1) + '_' + str(j + 1)
                results.ix[results[el_tag_name] <= 0.00, cop_tag_name] = 0
        operation_df['oau_chiller_COP'] = results.filter(regex='cop').sum(axis=1)
    return operation_df


def plot_heat_balance(building, building_result_path, heat_df, results, tech):
    heat_df = heat_df * 1000 / results['Af_m2'][1]
    # extract parameters
    time_steps = results.shape[0]
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    # colors = plt.cm.Set2(np.linspace(0, 1, len(heat_df.columns)))
    colors = ['#086375', '#1DD380', '#B2FF9E', '#B2FF0E']  # lcu, scu, oau, #AFFC41, #B2FF9E
    # colors = ['red', 'blue', 'green']
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(heat_df.shape[0])
    # plot bars
    for c in range(len(heat_df.columns)):
        column = heat_df.columns[c]
        ax.bar(x_ticks, heat_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + heat_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Sensible heat [Wh/m2]', xlim=(1, time_steps), ylim=(0, 100))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    results['q_bui_per_Af'] = pd.to_numeric(results['q_bui']) * 1000 / results['Af_m2'][1]
    q_bui_float = pd.to_numeric(results['q_bui_per_Af'])
    ax1.plot(x_ticks, q_bui_float, '-o', linewidth=2, markersize=4, label='sensible heat gain', color='#5F4064')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.legend(loc='upper right')
    ax1.set_xticks(x_ticks_shown)
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'heat'))


def plot_hu_store(building, building_result_path, hu_store_df, tech):
    # extract parameters
    time_steps = hu_store_df.shape[0]
    x_ticks = hu_store_df.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    fig, ax = plt.subplots(figsize=fig_size)
    line1, = ax.plot(x_ticks, hu_store_df['humidity_ratio'], '-o', linewidth=2, markersize=4,
                     label='humidity ratio')
    line2, = ax.plot(x_ticks, hu_store_df['relative_humidity'], '-o', linewidth=2, markersize=4, label='%RH')
    ax.legend(loc='upper right')
    ax.set_xticks(x_ticks_shown)
    ax.grid(True)
    ax.set(xlim=(1, time_steps), ylim=(1, 80))
    plt.xlabel('Time [hr]', fontsize=14)
    plt.ylabel('%RH [-] ; Humidity Ratio [g/kg d.a.]', fontsize=14)
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'hu_store'))
    plt.close(fig)
    return np.nan


def plot_water_balance(building, building_result_path, humidity_df, results, tech):
    # extract parameters
    time_steps = results.shape[0]
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    colors = plt.cm.Set2(np.linspace(0, 1, len(humidity_df.columns)))
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(humidity_df.shape[0])
    # plot bars
    for c in range(len(humidity_df.columns)):
        column = humidity_df.columns[c]
        ax.bar(x_ticks, humidity_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + humidity_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Water flow [kg/s]', xlim=(1, time_steps), ylim=(0, 0.3))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    w_bui_float = pd.to_numeric(results['w_bui'])
    ax1.plot(x_ticks, w_bui_float, '-o', linewidth=2, markersize=4, label='water gain')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.set_xticks(x_ticks_shown)
    ax.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'water_flow'))
    return np.nan


def plot_air_flow(air_flow_df, results, tech, building, building_result_path):
    # extract parameters
    time_steps = results.shape[0]
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    colors = plt.cm.Set2(np.linspace(0, 1, len(air_flow_df.columns)))
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(air_flow_df.shape[0])
    # plot bars
    for c in range(len(air_flow_df.columns)):
        column = air_flow_df.columns[c]
        ax.bar(x_ticks, air_flow_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + air_flow_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Air flow [kg/s]', xlim=(1, time_steps), ylim=(0, 50))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper left')

    # plt.show()
    # plot layout
    plt.title(building + '_' + tech, fontsize=14)
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'air_flow'))

    return np.nan


def plot_water_in_out(building, building_result_path, humidity_df, results, tech):
    # rearrange humidity_df
    water_in_out_df = humidity_df * (-1)
    water_in_out_df['m_w_gain'] = results['w_bui']

    # extract parameters
    time_steps = results.shape[0]
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    colors = plt.cm.Set2(np.linspace(0, 1, len(humidity_df.columns)))
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(water_in_out_df.shape[0])
    # plot bars
    for c in range(len(water_in_out_df.columns)):
        column = water_in_out_df.columns[c]
        ax.bar(x_ticks, water_in_out_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + water_in_out_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Water flow [kg/s]', xlim=(1, time_steps), ylim=(0, 0.3))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    w_bui_float = pd.to_numeric(results['w_bui'])
    ax1.plot(x_ticks, w_bui_float, '-o', linewidth=2, markersize=4, label='water gain')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.set_xticks(x_ticks_shown)
    ax.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'water_flow'))


def plot_electricity_usage(building, building_result_path, results, tech):
    results['el_per_Af'] = results['SU_elec'] * 1000 / results['Af_m2'][1]
    # extract parameters
    time_steps = results.shape[0] - 1
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    ax.plot(x_ticks, results['el_per_Af'], '-o', linewidth=2, markersize=4, label='el_used')
    ax.legend(loc='upper right')
    ax.set(xlabel='Time [hr]', ylabel='Electricity Usage [Wh/m2]', xlim=(1, time_steps), ylim=(0, 35))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.set_xticks(x_ticks_shown)
    ax.grid(True)
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'el_usage'))


def plot_electricity_usages(building, building_result_path, electricity_df, results, tech):
    electricity_per_area_df = electricity_df * 1000 / results['Af_m2'][1]
    # extract parameters
    time_steps = results.shape[0] - 1
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    # colors = plt.cm.Set2(np.linspace(0, 1, len(electricity_df.columns)))
    colors = [(0.4, 0.76078, 0.647059, 1), (0.5, 0.8078, 0.647059, 1),
              (0.65098, 0.847059, 0.32941, 1), (0.8, 0.9, 0.32941, 1),
              (0.70196078, 0.70196078, 0.70196078, 1), (0.70196078, 0.73196078, 0.8, 1),
              (0.5, 0.5, 0.7, 1)]
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(electricity_per_area_df.shape[0])
    # plot bars
    for c in range(len(electricity_per_area_df.columns)):
        column = electricity_per_area_df.columns[c]
        ax.bar(x_ticks, electricity_per_area_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + electricity_per_area_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Electricity Use [Wh/m2]', xlim=(1, time_steps), ylim=(0, 35))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.set_xticks(x_ticks_shown)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    total_el_float = pd.to_numeric(results['SU_elec'] * 1000 / results['Af_m2'][1])
    ax1.plot(x_ticks, total_el_float, '-o', linewidth=2, markersize=4, label='total electricity use', color='steelblue')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'el_usages'))


def plot_supply_temperature_humidity(building, building_result_path, operation_df, tech):
    # extract parameters
    time_steps = operation_df.shape[0]
    x_ticks = operation_df.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    ## plotting
    if tech != 'HCS_LD':
        # COP bar
        fig, ax = plt.subplots(figsize=fig_size)
        bar_width = 0.5
        opacity = 0.5
        ax.bar(x_ticks, operation_df['oau_chiller_COP'], bar_width, alpha=opacity, label='COP')
        ax.legend(loc='upper left')
        plt.xlim(1, time_steps)
        plt.ylim(0, 25)

        # T, w lines
        ax1 = ax.twinx()
        line1, = ax1.plot(x_ticks, operation_df['T_SA'], '-o', linewidth=2, markersize=4,
                          label='T,supply,OAU')
        line2, = ax1.plot(x_ticks, operation_df['w_SA'], '-o', linewidth=2, markersize=4, label='w,supply,OAU')
        ax1.legend(loc='upper right')
        ax1.set_xticks(x_ticks_shown)
        ax1.grid(True)
        ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
        plt.xlabel('Time [hr]', fontsize=14)
        plt.ylabel('Temperature [C] ; Humidity Ratio [g/kg d.a.]', fontsize=14)
        plt.title(building + '_' + tech, fontsize=14)
        # plt.show()
        fig.savefig(path_to_save_fig(building, building_result_path, tech, 'OAU_supply'))
    else:
        # T, w lines
        fig, ax1 = plt.subplots(figsize=fig_size)
        line1, = ax1.plot(x_ticks, operation_df['T_SA'], '-o', linewidth=2, markersize=4,
                          label='T,supply,OAU')
        line2, = ax1.plot(x_ticks, operation_df['w_SA'], '-o', linewidth=2, markersize=4, label='w,supply,OAU')
        ax1.legend(loc='upper right')
        ax1.set_xticks(x_ticks_shown)
        ax1.grid(True)
        plt.xlabel('Time [hr]', fontsize=14)
        plt.ylabel('Temperature [C] ; Humidity Ratio [g/kg d.a.]', fontsize=14)
        plt.xlim(1, time_steps)
        plt.ylim(0, 25)
        plt.title(building + '_' + tech, fontsize=14)
        # plt.show()
        fig.savefig(path_to_save_fig(building, building_result_path, tech, 'OAU_supply'))
    plt.close(fig)
    return np.nan


## auxiliary functions
def set_xtick_shown(x_ticks, time_steps):
    reduced_x_ticks = np.insert(np.arange(0, time_steps, 12)[1:], 0, 1)
    x_ticks_shown = x_ticks if time_steps <= 24 else reduced_x_ticks
    return x_ticks_shown


def set_figsize(time_steps):
    fig_size = (6.6, 5) if time_steps <= 24 else (15.4, 5)
    return fig_size


## paths

# PATH_TO_RESULT_FOLDER = 'C:\\OSMOSE_projects\\hcs_windows\\results\\'

def path_to_osmose_results(building_result_path, tech):
    format = 'csv'
    path_to_file = os.path.join(building_result_path, '%s_outputs.%s' % (tech, format))
    return path_to_file


def path_to_save_fig(building, building_result_path, tech, fig_type):
    path_to_file = os.path.join(building_result_path, '%s_%s_%s.png' % (building, tech, fig_type))
    return path_to_file


def path_to_elec_csv(building, building_result_path, tech):
    path_to_file = os.path.join(building_result_path, '%s_%s_el.csv' % (building, tech))
    return path_to_file


def path_to_chiller_csv(building, building_result_path, tech):
    path_to_file = os.path.join(building_result_path, '%s_%s_chiller.csv' % (building, tech))
    return path_to_file


def p_ws_from_t(t_celsius):
    # convert temperature
    t = t_celsius + 273.15

    # constants
    C8 = -5.8002206E+03
    C9 = 1.3914993E+00
    C10 = -4.8640239E-02
    C11 = 4.1764768E-05
    C12 = -1.4452093E-08
    C13 = 6.5459673E+00

    return math.exp(C8 / t + C9 + C10 * t + C11 * t ** 2 + C12 * t ** 3 + C13 * math.log1p(t))


if __name__ == '__main__':
    building = "B002"
    tech = ["HCS_coil"]
    building_result_path = "C:\Users\Shanshan\Documents\WP1_results\WTP_CBD_m_WP1_HOT\B002_24"
    main(building, tech, building_result_path)
