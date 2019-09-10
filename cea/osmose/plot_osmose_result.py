from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

from cea.osmose.post_compute_osmose_results import set_up_ex_df, calc_qc_loads
from cea.osmose.auxiliary_functions import calc_RH_from_w
from cea.osmose.settings import PLOTS

CO2_env_ppm = 400 / 1e6  # [m3 CO2/m3]
CO2_max_ppm = 800 / 1e6

CONFIG_TABLE = {'HCS_coil': 'Config|1', 'HCS_ER0': 'Config|2', 'HCS_3for2': 'Config|3', 'HCS_LD': 'Config|4',
                'HCS_IEHX': 'Config|5', 'HCS_status_quo': 'Baseline'}


# from cea.plots.demand.comfort_chart import p_w_from_rh_p_and_ws, p_ws_from_t, hum_ratio_from_p_w_and_p
def main(building, TECHS, building_result_path):
    el_use_sum = {}
    for tech in TECHS:
        osmose_result_file = path_to_osmose_results(building_result_path, tech)
        if os.path.isfile(osmose_result_file):
            ## read results (outputs)
            results = read_osmose_csv(osmose_result_file)
            el_use_sum[tech] = results['SU_elec'].sum()

            # check balance
            print 'checking balance for: ', tech
            check_balance(results, building, building_result_path, tech)

            # calculate oau chiller operation
            output_chiller_count_and_Qc(building, building_result_path, results, tech)

            ## plot air flows
            air_flow_df = set_up_air_flow_df(results)
            if 'air_flow' in PLOTS:
                plot_air_flow(air_flow_df, results, tech, building, building_result_path)

            # plot T_SA and w_SA
            if building_result_path.split('\\')[len(building_result_path.split('\\')) - 1] == 'status_quo':
                operation_df = np.nan  # do nothing
            else:
                operation_df = set_up_operation_df(tech, results)
                if 'OAU_T_w_supply' in PLOTS:
                    plot_supply_temperature_humidity(building, building_result_path, operation_df, tech)

            # plot water balance
            humidity_df = set_up_humidity_df(tech, results)
            if 'humidity_balance' in PLOTS:
                plot_water_balance(building, building_result_path, humidity_df, results, tech)
                # plot_water_in_out(building, building_result_path, humidity_df, results, tech) # TODO: to be finished

            ## plot humidity level (storage)
            if 'hu_storage' in results.columns.values:
                hu_store_df = set_up_hu_store_df(results)
                if 'humidity_storage' in PLOTS:
                    plot_hu_store(building, building_result_path, hu_store_df, tech)

            ## plot co2 level (storage)
            if 'co2_storage' in results.columns.values:
                co2_store_df = set_up_co2_store_df(results)
                if 'co2_storage' in PLOTS:
                    plot_co2_store(building, building_result_path, co2_store_df, tech)

            ## plot heat balance
            heat_df = set_up_heat_df(tech, results)
            if 'heat_balance' in PLOTS:
                plot_heat_balance(building, building_result_path, heat_df, results, tech)

            ## calculate cooling loads
            results = calc_qc_loads(results, humidity_df, heat_df)

            ## plot electricity usage
            plot_electricity_usage(building, building_result_path, results, tech)
            electricity_df = set_up_electricity_df(tech, results)
            output_el_usage_by_units(tech, electricity_df, results, building, building_result_path)
            if 'electricity_usages' in PLOTS:
                plot_electricity_usages_by_units(building, building_result_path, electricity_df, results, tech)

            # plot exergy loads
            osmose_composite_file = path_to_osmose_composite(building_result_path, tech)
            if os.path.isfile(osmose_composite_file):
                composite_df = read_osmose_csv(osmose_composite_file)
            else:
                composite_df = pd.DataFrame()
            results = get_hourly_oau_operations(tech, results, composite_df)
            results = get_reheating_energy(tech, results)
            ex_df = set_up_ex_df(results, operation_df, electricity_df, air_flow_df)
            if 'exergy_usages' in PLOTS:
                plot_exergy_usages_by_units(building, building_result_path, ex_df, results, tech)

            ## write output_df
            calc_el_stats(building, building_result_path, electricity_df, operation_df, ex_df, results, tech)

        else:
            print 'Cannot find ', osmose_result_file

    print el_use_sum
    return


def output_chiller_count_and_Qc(building, building_result_path, results, tech):
    if building_result_path.split('\\')[len(building_result_path.split('\\')) - 1] == 'status_quo':
        chiller_count = 1  # do nothing
    elif tech in ['HCS_coil', 'HCS_3for2', 'HCS_ER0', 'HCS_IEHX']:
        chiller_count = analyse_chilled_water_usage(results, tech)
        chiller_count.to_csv(path_to_chiller_csv(building, building_result_path, tech, 'chiller'))
        chiller_Qc = analyse_Qc_from_chilled_water(results, tech)
        chiller_Qc.to_csv(path_to_chiller_csv(building, building_result_path, tech, 'chiller_Qc'))


def plot_exergy_usages_by_units(building, building_result_path, ex_df, results, tech):
    plot_exergy_loads(building, building_result_path, ex_df, results, tech)
    plot_exergy_usages(building, building_result_path, ex_df, results, tech, '')
    if results.shape[0] > 24:
        result_WED = results.iloc[72:96]
        ex_df_WED = ex_df.iloc[72:96]
        plot_exergy_usages(building, building_result_path, ex_df_WED, result_WED, tech, 'WED')
        ex_df_SAT = ex_df.iloc[144:168]
        result_SAT = results.iloc[144:168]
        plot_exergy_usages(building, building_result_path, ex_df_SAT, result_SAT, tech, 'SAT')


def plot_electricity_usages_by_units(building, building_result_path, electricity_df, results, tech):
    plot_electricity_usages(building, building_result_path, electricity_df, results, tech, '')
    if results.shape[0] > 24:
        result_WED = results.iloc[72:96]
        electricity_df_WED = electricity_df.iloc[72:96]
        plot_electricity_usages(building, building_result_path, electricity_df_WED, result_WED, tech, 'WED')
        electricity_df_SAT = electricity_df.iloc[144:168]
        result_SAT = results.iloc[144:168]
        plot_electricity_usages(building, building_result_path, electricity_df_SAT, result_SAT, tech, 'SAT')


def read_osmose_csv(osmose_result_file):
    results = pd.read_csv(osmose_result_file, header=None).T.reset_index()
    results = results.rename(columns=results.iloc[0])[1:]
    results = results.fillna(0)
    return results


def check_balance(results, building, building_result_path, tech):
    if 'status' not in tech:
        # Bui_energy_bal
        check_bui_energy_bal(results, building, building_result_path, tech)
        # Bui_water_bal
        check_bui_water_bal(results, building, building_result_path, tech)
        # Bui_air_bal
        check_bui_air_bal(results, building, building_result_path, tech)
        # Bui_co2_bal
        # check_CO2_bal(results, building, building_result_path, tech)

        check_electricity_bal(results, building, building_result_path, tech)

    return np.nan


def check_CO2_bal(results, building, building_result_path, tech):
    CO2_IN = (results.filter(like='m_oau_in').sum(axis=1) / results['rho_air']) * CO2_env_ppm * 3600 + \
             results['co2_sto_discharge'] + results['co2_bui_inf_occ']
    # CO2_IN = (results.filter(like='m_oau_in').sum(axis=1) / results['rho_air']) * CO2_env_ppm * 3600 + \
    #          results['co2_sto_discharge'] + results['co2_bui_inf_occ']
    CO2_OUT = (results['m_oau_out'] / results['rho_air']) * CO2_max_ppm * 3600 + results['co2_sto_charge']

    Bui_CO2_bal = CO2_IN - CO2_OUT
    if abs(Bui_CO2_bal.sum() / CO2_IN.sum()) >= 1e-5:
        print ('Bui_CO2_bal not zero...')

        # plotR
        co2_IN_dict = {}
        co2_IN_dict['m_infil_occupants'] = results['co2_bui_inf_occ']
        co2_IN_dict['m_oau_in'] = (results.filter(like='m_oau_in').sum(axis=1) / results[
            'rho_air']) * CO2_env_ppm * 3600
        co2_IN_dict['co2_sto_discharge'] = results['co2_sto_discharge']

        air_OUT_dict = {}
        air_OUT_dict['m_oau_out'] = (results.filter(like='m_oau_out').sum(axis=1) / results[
            'rho_air']) * CO2_max_ppm * 3600
        air_OUT_dict['co2_sto_charge'] = results['co2_sto_charge']

        name = 'bui_CO2_bal'
        plot_stacked_bars_side_by_side(co2_IN_dict, air_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)
    return np.nan


def check_electricity_bal(results, building, building_result_path, tech):
    Electricity_IN = results['SU_elec']
    if tech == 'HCS_LD':
        Electricity_OUT = results['el_scu_pump'] + results['el_chi_ht'] + \
                          results['el_lcu_fan'] + results['el_chi_lt'] + \
                          results.filter(like='el_oau_out').sum(axis=1) + \
                          results.filter(like='el_oau_in').sum(axis=1) + results['el_LDHP'] + \
                          results.filter(like='el_oau_chi').sum(axis=1) + results['el_ct']
    else:
        Electricity_OUT = results['el_scu_pump'] + results['el_chi_ht'] + \
                          results['el_chi_lt'] + \
                          results.filter(like='el_lcu').sum(axis=1) + \
                          results.filter(like='el_oau_out').sum(axis=1) + \
                          results.filter(like='el_oau_in').sum(axis=1) + \
                          results.filter(like='el_oau_chi').sum(axis=1) + results['el_ct']
    Electricity_bal = Electricity_IN - Electricity_OUT
    if abs(Electricity_bal.sum() / Electricity_OUT.sum()) >= 1e-5:
        print('Electriicty_bal not zero...')

    el_IN_dict = {}
    el_IN_dict['grid'] = results['SU_elec']
    el_IN_label_dict = {'grid': 'el grid'}

    el_OUT_dict = {}
    # el_OUT_dict['el_oau_out_fan'] = results['el_oau_out_fan']
    # el_OUT_dict['el_iehx_out_fan'] = results.filter(like='el_oau_out').sum(axis=1) - results['el_oau_out_fan']
    el_OUT_dict['SCU pump'] = results['el_scu_pump']
    el_OUT_dict['SCU chiller'] = results['el_chi_ht']
    el_OUT_dict['LCU fan'] = results['el_lcu_fan']
    if 'el_lcu_reheat' in results.columns.values:
        el_OUT_dict['LCU reheater'] = results['el_lcu_reheat']
    el_OUT_dict['LCU chiller'] = results['el_chi_lt']
    el_OUT_dict['OAU fan'] = results.filter(like='el_oau_in').sum(axis=1) + results['el_oau_out_fan']
    el_OUT_dict['OAU chiller'] = results.filter(like='el_oau_chi').sum(axis=1)
    el_OUT_dict['Cooling Towers'] = results['el_ct']
    el_OUT_label_dict = {'el_oau_out_fan': 'Fan'}

    if tech == 'HCS_LD':
        el_OUT_dict['el_oau_HP'] = results['el_LDHP']
    name = 'Electricity [kW]'
    plot_stacked_bars_side_by_side(el_IN_dict, el_OUT_dict, results.shape[0], building, building_result_path, tech,
                                   name)
    return np.nan


def check_bui_air_bal(results, building, building_result_path, tech):
    Bui_air_bal_IN = results['m_inf_in'] + results.filter(like='m_oau_in').sum(axis=1) + results.filter(
        like='SU_vent').sum(axis=1)
    Bui_air_bal_OUT = results.filter(like='m_oau_out').sum(axis=1) + results.filter(like='SU_exhaust').sum(axis=1)
    Bui_air_bal = Bui_air_bal_IN - Bui_air_bal_OUT
    if abs(Bui_air_bal.sum()) >= 1e-3:
        print ('Bui_air_bal not zero...')

        # plot
        air_IN_dict = {}
        air_IN_dict['Infiltration'] = results['m_inf_in']
        air_IN_dict['OAU'] = results.filter(like='m_oau_in').sum(axis=1)
        air_IN_dict['Error'] = results.filter(like='SU_vent').sum(axis=1)

        air_OUT_dict = {}
        air_OUT_dict['Exhaust'] = results.filter(like='m_oau_out').sum(axis=1)
        air_OUT_dict['Error'] = results.filter(like='SU_exhaust').sum(axis=1)

        name = 'Air flows [kg/s]'
        plot_stacked_bars_side_by_side(air_IN_dict, air_OUT_dict, results.shape[0], building, building_result_path,
                                       tech, name)
    return np.nan


def check_bui_water_bal(results, building, building_result_path, tech):
    if 'w_sto_charge' in results.columns.values:
        w_sto_charge = results['w_sto_charge']
        w_sto_discharge = results['w_sto_discharge']
    else:
        timesteps = results.shape[0]
        w_sto_charge = np.zeros(timesteps)
        w_sto_discharge = np.zeros(timesteps)
    Bui_water_bal_IN = results.filter(like='w_oau_out').sum(axis=1) + results['w_lcu'] + w_sto_charge + results.filter(
        like='SU_dhu').sum(axis=1)
    # Bui_water_bal_OUT = results['w_bui'] + results.filter(like='w_oau_in').sum(axis=1) + results['w_sto_discharge'] \
    #                     + results.filter(like='SU_hu').sum(axis=1)
    Bui_water_bal_OUT = results['w_bui'] + results.filter(like='w_oau_in').sum(axis=1) + w_sto_discharge + \
                        results.filter(like='SU_hu').sum(axis=1)
    Bui_water_bal = Bui_water_bal_IN - Bui_water_bal_OUT
    if abs(Bui_water_bal.sum() / Bui_water_bal_IN.sum()) >= 1e-5:
        print ('Bui_water_bal not zero...')

    water_IN_dict = {}
    water_IN_dict['OAU out'] = results.filter(like='w_oau_out').sum(axis=1)
    water_IN_dict['RAU'] = results['w_lcu']
    if w_sto_charge.max() > 0.0:
        water_IN_dict['Stored'] = w_sto_charge
    if results.filter(like='SU_dhu').sum(axis=1).sum() > 0.0:
        water_IN_dict['Error'] = results.filter(like='SU_dhu').sum(axis=1)

    water_OUT_dict = {}
    water_OUT_dict['Building gains'] = results['w_bui']
    water_OUT_dict['OAU in'] = results.filter(like='w_oau_in').sum(axis=1)
    if w_sto_discharge.max() > 0.0:
        water_OUT_dict['Discharged'] = w_sto_discharge
    if results.filter(like='SU_hu').sum(axis=1).sum() > 0.0:
        water_OUT_dict['Error'] = results.filter(like='SU_hu').sum(axis=1)

    name = 'Water'
    plot_stacked_bars_side_by_side(water_IN_dict, water_OUT_dict, results.shape[0], building, building_result_path,
                                   tech, name)

    return np.nan


def check_bui_energy_bal(results, building, building_result_path, tech):
    Bui_energy_bal_IN = results['q_bui'] + results.filter(like='q_oau_sen_in').sum(axis=1) + results.filter(
        like='SU_Qh').sum(axis=1)
    Bui_energy_bal_OUT = results.filter(like='q_oau_sen_out').sum(axis=1) + results['q_scu_sen'] + results[
        'q_lcu_sen'] + results.filter(
        like='SU_Qc').sum(axis=1)
    Bui_energy_bal = Bui_energy_bal_IN - Bui_energy_bal_OUT
    if abs(
            Bui_energy_bal.sum() / Bui_energy_bal_IN.sum()) >= 1e-5:  # difference more than 1% of total sensible energy in
        print('Bui_energy_bal not zero...')

    energy_IN_dict = {}
    energy_IN_dict['building gains'] = results['q_bui']
    energy_IN_dict['OAU in'] = results.filter(like='q_oau_sen_in').sum(axis=1)
    if results.filter(like='SU_Qh').sum(axis=1).sum() > 0.0:
        energy_IN_dict['Dummy heating'] = results.filter(like='SU_Qh').sum(axis=1)

    energy_OUT_dict = {}
    energy_OUT_dict['OAU out'] = results.filter(like='q_oau_sen_out').sum(axis=1)
    energy_OUT_dict['SCU'] = results['q_scu_sen']
    energy_OUT_dict['RAU'] = results['q_lcu_sen']
    if results.filter(like='SU_Qc').sum(axis=1).sum() > 0.0:
        energy_OUT_dict['Dummy cooling'] = results.filter(like='SU_Qc').sum(axis=1)

    name = 'Sensible heat [kW]'
    plot_stacked_bars_side_by_side(energy_IN_dict, energy_OUT_dict, results.shape[0], building, building_result_path,
                                   tech, name)

    return np.nan


def plot_stacked_bars_side_by_side(left_stack_dict, right_stack_dict, timesteps, building, building_result_path, tech,
                                   name):
    # plotting
    fig, ax = plt.subplots()
    bar_width = 0.4
    x_ticks = np.arange(timesteps) + 1
    # left stack
    x_axis_left = x_ticks - 0.2
    y_offset = np.zeros(timesteps)
    # colors = ['#AD4456', '#D76176', '#E3909F', '#742D3A', '#270F14', '#FF4B31']  # PINKS
    colors = ['#85a391', '#b9cac0', '#270F14', '#dce4df', '#ab9c81', '#e7dfcf']  # Organic Forest Logo Color Palette
    c = 0
    for key in left_stack_dict.keys():
        ax.bar(x_axis_left, left_stack_dict[key], bar_width, bottom=y_offset, label=key, color=colors[c])
        y_offset = y_offset + left_stack_dict[key]
        c = c + 1
    y_max = y_offset.max()
    # right stack
    x_axis_right = x_ticks + 0.2
    y_offset = np.zeros(timesteps)
    # colors = ['#29465A', '#39617E', '#718C60', '#77AACF', '#111C24', '#507C88', '#111C24', '#507C88']  # BLUES
    colors = ['#cd98a4', '#b86d7e', '#f7dcd7', '#eccac9', '#f6e9e6', '#bca1a0', '#DEB3B7', '#ebd1d3']  # Broken Blush Color Palette
    c = 0
    for key in right_stack_dict.keys():
        ax.bar(x_axis_right, right_stack_dict[key], bar_width, bottom=y_offset, label=key, color=colors[c])
        y_offset = y_offset + right_stack_dict[key]
        c = c + 1
    y_max = max(y_offset.max(), y_max)
    # plot settings
    x_ticks_shown = set_xtick_shown(x_ticks, timesteps)
    ax.set_xticks(x_ticks_shown)
    # put legend to the right
    ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5))
    ax.set(xlabel='Time [hr]', ylabel=name, ylim=(0, y_max + 0.05 * y_max))
    ax.yaxis.label.set_size(16)
    # plt.show()

    plt.title(building + "_" + tech)
    fig.savefig(path_to_save_fig(building, building_result_path, tech, name), bbox_inches="tight")

    return np.nan


def analyse_chilled_water_usage(results, tech):
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


def analyse_Qc_from_chilled_water(results, tech):
    number_oau_in = results.filter(like='OAU_T_SA').shape[1]
    # Qc_from_chilled_water_df = (results.filter(like='q_oau_in_')*1000/results['Af_m2'].max()).sum(axis=0).reset_index()
    Qc_from_chilled_water_df = results.filter(like='q_oau_in_').sum(axis=0).reset_index()
    T_low_C, T_high_C = 8.1, 14.1
    if (tech == 'HCS_3for2' and number_oau_in < 10):
        T_interval = 0.65 * 2
    else:
        T_interval = 0.65  # 0.5
    T_OAU_offcoil = np.arange(T_low_C, T_high_C, T_interval).round(2)
    Qc_from_chilled_water_df = Qc_from_chilled_water_df.set_index([T_OAU_offcoil])
    del Qc_from_chilled_water_df['index']
    Qc_from_chilled_water_df.columns = [tech]
    Qc_from_chilled_water_df = Qc_from_chilled_water_df.T
    return Qc_from_chilled_water_df


def calc_m_w_cond_results(w_in, w_out, chiller_used, i, results):
    w_air_in_kgperkg = results[w_in + chiller_used][i + 1]
    w_air_out_kgperkg = results[w_out + chiller_used][i + 1]
    m_w_cond_kgpers = results['m_oau_in_' + chiller_used][i + 1] * (w_air_in_kgperkg - w_air_out_kgperkg)
    return m_w_cond_kgpers


def calc_m_w_cond_composite(w_in, w_out, chiller_used, i, results, composite_df):
    w_air_in_kgperkg = composite_df[w_in + chiller_used][i + 1]
    w_air_out_kgperkg = composite_df[w_out + chiller_used][i + 1]
    m_w_cond_kgpers = results['m_oau_in_' + chiller_used][i + 1] * (w_air_in_kgperkg - w_air_out_kgperkg)
    return m_w_cond_kgpers


def set_up_hu_store_df(results):
    hu_store_df = pd.DataFrame()
    hu_store_df['humidity_ratio'] = results['hu_storage'] * 3600 / results['M_dryair'] * 1000  # g/kg d.a.
    hu_store_df['relative_humidity'] = np.vectorize(calc_RH_from_w)(hu_store_df['humidity_ratio'],
                                                                    results['T_RA']) * 100

    # calculate actual balance
    w_gain_kgpers = (results['w_bui'] + results.filter(like='w_oau_in').sum(axis=1)).values
    w_lcu_out = results['w_lcu'].values
    m_air_out = results.filter(like='m_oau_out').sum(axis=1).values
    M_room_kg = results['M_dryair'].values
    T_RA_C = results['T_RA'].values
    timesteps = results.shape[0]
    W_room_kg = np.zeros(timesteps)
    w_room_kgperkg = np.zeros(timesteps)
    RH = np.zeros(timesteps)
    for i in range(timesteps):
        if i == 0:
            w_gperkg_0 = hu_store_df['humidity_ratio'].values[0]
            W_room_kg[i] = w_gperkg_0 * M_room_kg[i] / 1000
            w_room_kgperkg[i] = W_room_kg[i] / M_room_kg[i]
            RH[i] = calc_RH_from_w(w_gperkg_0, T_RA_C[i])
        else:
            water_added_kgperhr = (w_gain_kgpers[i] - w_lcu_out[i] - m_air_out[i] * w_room_kgperkg[i - 1]) * 3600
            W_room_kg[i] = W_room_kg[i - 1] + water_added_kgperhr
            w_room_kgperkg[i] = W_room_kg[i] / M_room_kg[i]
            RH[i] = calc_RH_from_w(w_room_kgperkg[i] * 1000, T_RA_C[i])
    hu_store_df['RH'] = RH * 100
    hu_store_df['w'] = W_room_kg / M_room_kg * 1000
    return hu_store_df


def set_up_co2_store_df(results):
    co2_store_df = pd.DataFrame()
    co2_store_df['m3'] = results['co2_storage']
    if results['co2_storage'].values[0] >= 0.01:
        co2_store_df['ppm'] = results['co2_storage'] / results['Vf_m3'] * 1e6
    else:
        co2_store_df['ppm'] = 0

    ## calculate actual co2 concentration
    # get numbers
    m_air_out = results.filter(like='m_oau_out').sum(axis=1).values
    rho_air = results['rho_air'].values
    V_room_m3 = results['Vf_m3'].values
    co2_occupants_m3 = results['co2_bui_inf_occ'].values
    timesteps = results.shape[0]
    # set up empty arrays
    co2_RA_ppm = np.zeros(timesteps)
    co2_RA_m3 = np.zeros(timesteps)
    for i in range(timesteps):
        if i == 0:
            co2_RA_storage_0 = results['co2_storage'].values[0]
            co2_RA_ppm[i] = 1200 / 1e6 if co2_RA_storage_0 <= 0 else co2_RA_storage_0 / V_room_m3[i]
            if co2_RA_ppm[i] <= 800 / 1e6:
                co2_RA_ppm[i] = 800 / 1e6
            # co2_RA_ppm[i] = 500 / 1e6
            co2_RA_m3[i] = co2_RA_ppm[i] * V_room_m3[i]
        else:
            co2_change_m3 = calc_co2_level(co2_RA_ppm[i - 1], co2_occupants_m3[i], m_air_out[i], rho_air[i])
            co2_RA_m3[i] = co2_RA_m3[i - 1] + co2_change_m3
            co2_RA_ppm[i] = co2_RA_m3[i] / V_room_m3[i]

    co2_store_df['co2_RA_ppm'] = co2_RA_ppm * 1e6
    co2_store_df['co2_RA_m3'] = co2_RA_m3
    return co2_store_df


def set_up_electricity_df(tech, results):
    electricity_df = pd.DataFrame()
    # lcu
    electricity_df['el_chi_lt'] = results['el_chi_lt']
    if 'el_lcu_reheat' in results.columns.values:
        electricity_df['el_fan_lcu'] = results['el_lcu_fan']
        electricity_df['el_reheat_lcu'] = results['el_lcu_reheat']
    else:
        electricity_df['el_fan_lcu'] = results['el_lcu_fan']

    # oau
    if tech == 'HCS_LD':
        electricity_df['el_fan_oau'] = results.filter(like='el_oau_in').sum(axis=1) + results['el_oau_out_fan'] + \
                                       results['el_oau_out_by_fan']
        electricity_df['el_hp_oau'] = results['el_LDHP']
    else:
        electricity_df['el_fan_oau'] = results.filter(like='el_oau_in').filter(like='fan').sum(axis=1) + results.filter(
            like='el_oau_out').sum(axis=1)
        electricity_df['el_reheat_oau'] = results.filter(like='el_oau_in').filter(like='reheat').sum(axis=1)
        electricity_df['el_chi_oau'] = results.filter(like='el_oau_chi').sum(axis=1)

    # scu
    electricity_df['el_chi_ht'] = results['el_chi_ht'] if 'status' not in tech else 0
    electricity_df['el_aux_scu'] = results['el_scu_pump'] if 'status' not in tech else 0
    # ct
    electricity_df['el_ct'] = results['el_ct']

    ## calculate balance
    balance = electricity_df.sum(axis=1) - results['SU_elec']
    balance = balance[abs(balance) > 1e-2]
    if abs(balance.sum()) > 1:
        print('electricity balance:', balance)

    return electricity_df


def output_el_usage_by_units(tech, electricity_df, results, building, building_result_path):
    Af_m2 = results['Af_m2'].mean()
    el_per_unit_df = pd.DataFrame()
    ## aggregate electricity usage per unit
    q_ct_lcu = results['q_chi_lt']
    q_ct_scu = results['q_chi_ht'] if 'status' not in tech else 0
    q_ct_oau = results.filter(like='q_oau_chi').sum(axis=1)
    q_ct_total = q_ct_lcu + q_ct_scu + q_ct_oau

    el_per_unit_df['el_lcu'] = electricity_df['el_chi_lt'] + electricity_df['el_fan_lcu'] + electricity_df['el_reheat_lcu']+ \
                               results['el_ct'] * (q_ct_lcu / q_ct_total).fillna(0)
    el_per_unit_df['el_scu'] = results['el_chi_ht'] + results['el_scu_pump'] + \
                               results['el_ct'] * (q_ct_scu / q_ct_total).fillna(0) if 'status' not in tech else 0
    if tech == 'HCS_LD':
        el_per_unit_df['el_oau'] = electricity_df['el_fan_oau'] + electricity_df['el_hp_oau']
    else:
        el_per_unit_df['el_oau'] = electricity_df['el_fan_oau'] + electricity_df['el_reheat_oau'] + electricity_df['el_chi_oau'] + \
                                   results['el_ct'] * (q_ct_oau / q_ct_total).fillna(0)
    el_per_unit_df['el_total'] = results['SU_elec']
    el_per_unit_df = el_per_unit_df * 1000 / Af_m2
    el_per_unit_df.to_csv(path_to_elec_unit_csv(building, building_result_path, tech))
    return np.nan


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


def calc_el_stats(building, building_result_path, electricity_df, operation_df, ex_df, results, tech):
    output_df = electricity_df.copy()
    # calculate electricity used in each technology
    output_df['el_total'] = output_df.sum(axis=1)
    output_df['el_scu'] = output_df['el_aux_scu'] + output_df['el_chi_ht']
    output_df['el_lcu'] = output_df['el_fan_lcu'] + output_df['el_reheat_lcu'] + output_df['el_chi_lt']
    if tech == 'HCS_LD':
        output_df['el_oau'] = output_df['el_fan_oau'] + output_df['el_hp_oau']
    else:
        output_df['el_oau'] = output_df['el_fan_oau'] + output_df['el_reheat_oau'] + output_df['el_chi_oau']
    if tech == 'HCS_ER0' or 'HCS_IEHX' or 'HCS_coil':
        output_df['el_oau_reheat'] = results['q_reheat']
    else:
        output_df['el_oau_reheat'] = np.zeros(results.shape[0])
    output_df['el_oau_in_fan'] = results.filter(like='fan').filter(like='oau_in').sum(axis=1)
    output_df['el_oau_out_fan'] = results.filter(like='fan').filter(like='oau_out').sum(axis=1)
    # calculate total cooling energy produced
    cooling_df = set_up_cooling_df(results)
    # output_df['qc_bui_sen_total'] = cooling_df.filter(like='qc_bui_sen').sum(axis=1)
    # output_df['qc_bui_lat_total'] = cooling_df.filter(like='qc_bui_lat').sum(axis=1)
    output_df['qc_sys_scu'] = cooling_df['qc_sys_sen_scu']
    output_df['qc_sys_lcu'] = cooling_df['qc_sys_sen_lcu'] + cooling_df['qc_sys_lat_lcu']
    output_df['qc_sys_oau'] = cooling_df['qc_sys_sen_oau'] + cooling_df['qc_sys_lat_oau']
    output_df['qc_sys_sen_total'] = cooling_df.filter(like='qc_sys_sen').sum(axis=1)
    output_df['qc_sys_lat_total'] = cooling_df.filter(like='qc_sys_lat').sum(axis=1)
    # calculate minimum exergy required
    output_df['Ex_min'] = ex_df['Ex_min_total']
    output_df['Ex_process_OAU'] = ex_df['Ex_process_OAU']
    output_df['Ex_process_RAU'] = ex_df['Ex_process_RAU']
    output_df['Ex_process_SCU'] = ex_df['Ex_process_SCU']
    output_df['Ex_process'] = ex_df['Ex_process_total']
    output_df['Ex_utility_OAU'] = ex_df['Ex_utility_OAU']
    output_df['Ex_utility_RAU'] = ex_df['Ex_utility_RAU']
    output_df['Ex_utility_SCU'] = ex_df['Ex_utility_SCU']
    output_df['Ex_utility'] = ex_df['Ex_utility_total']
    # get Qh
    output_df['Qh'] = results['SU_Qh']
    output_df['el_tot_with_Qh'] = output_df['Qh'] + output_df['el_total']
    # get T,w
    output_df['T_SA'] = operation_df['T_SA']
    output_df['w_SA'] = operation_df['w_SA']
    # get T_chw
    output_df['T_chw'] = results['T_chw']
    output_df['m_w_coil_cond'] = results['m_w_coil_cond']
    # cooling loads at buildings
    output_df['qc_load_sen'] = results['q_tot_sen_load']
    output_df['qc_load_total'] = results['q_tot_load']

    ## add total row in the bottom
    total_df = pd.DataFrame(output_df.sum()).T
    output_df = output_df.append(total_df).reset_index().drop(columns='index')
    ##############################

    # area
    output_df['Af_m2'] = results['Af_m2'].max()

    ## calculate values from column operations
    # output_df['qc_bui_total'] = output_df['qc_bui_sen_total'] + output_df['qc_bui_lat_total']
    # output_df['cop_cooling'] = output_df['qc_bui_total'] / output_df['el_total']
    output_df['qc_sys_total'] = output_df['qc_sys_sen_total'] + output_df['qc_sys_lat_total']
    output_df['qc_per_m2'] = output_df['qc_sys_total'] / output_df['Af_m2']
    output_df['sys_SHR'] = output_df['qc_sys_sen_total'] / output_df['qc_sys_total']  # sensible heat ratio
    output_df['load_SHR'] = output_df['qc_load_sen'] / output_df['qc_load_total']  # sensible heat ratio
    output_df['qc_impact'] = output_df['qc_load_total'] / output_df['qc_sys_total']
    output_df['qc_Wh_sys_per_Af'] = output_df['qc_sys_total'] * 1000 / output_df['Af_m2']
    output_df['el_Wh_total_per_Af'] = output_df['el_total'] * 1000 / output_df['Af_m2']
    output_df['el_Wh_OAU_per_Af'] = output_df['el_oau'] * 1000 / output_df['Af_m2']
    output_df['el_Wh_RAU_per_Af'] = output_df['el_lcu'] * 1000 / output_df['Af_m2']
    output_df['el_Wh_SCU_per_Af'] = output_df['el_scu'] * 1000 / output_df['Af_m2']
    output_df['cop_system'] = output_df['qc_sys_total'] / output_df['el_total']

    ## calculate values to add to the last row
    # calc system mean cop
    index = output_df.shape[0] - 1
    cop_system_mean = output_df['cop_system'].ix[0:index - 1].replace(0, np.nan).mean(skipna=True)
    output_df['cop_system_mean'] = output_df['cop_system']
    output_df.at[index, 'cop_system_mean'] = cop_system_mean
    # calculate cop with Qh
    output_df['cop_Qh'] = output_df['qc_sys_total'] / output_df['el_tot_with_Qh']

    # output_df = output_df.set_value(index, 'cop_system_mean', cop_system_mean)
    # output_df['cop_scu'] = output_df['qc_sys_scu']/output_df['el_scu']
    # output_df['cop_lcu'] = output_df['qc_sys_lcu']/output_df['el_lcu']
    # output_df['cop_oau'] = output_df['qc_sys_oau']/output_df['el_oau']

    # calculate mean T_SA, w_SA
    T_SA_mean = operation_df['T_SA'].ix[0:index - 1].replace(0, np.nan).mean(skipna=True)
    output_df.at[index, 'T_SA'] = T_SA_mean
    w_SA_mean = operation_df['w_SA'].ix[0:index - 1].replace(0, np.nan).mean(skipna=True)
    output_df.at[index, 'w_SA'] = w_SA_mean

    # calculate exergy efficiency
    output_df['process_exergy_OAU_Wh_per_Af'] = output_df['Ex_process_OAU'] * 1000 / output_df['Af_m2']
    output_df['process_exergy_RAU_Wh_per_Af'] = output_df['Ex_process_RAU'] * 1000 / output_df['Af_m2']
    output_df['process_exergy_SCU_Wh_per_Af'] = output_df['Ex_process_SCU'] * 1000 / output_df['Af_m2']
    output_df['process_exergy_Wh_per_Af'] = output_df['Ex_process'] * 1000 / output_df['Af_m2']
    output_df['utility_exergy_OAU_Wh_per_Af'] = output_df['Ex_utility_OAU'] * 1000 / output_df['Af_m2']
    output_df['utility_exergy_RAU_Wh_per_Af'] = output_df['Ex_utility_RAU'] * 1000 / output_df['Af_m2']
    output_df['utility_exergy_SCU_Wh_per_Af'] = output_df['Ex_utility_SCU'] * 1000 / output_df['Af_m2']
    output_df['utility_exergy_Wh_per_Af'] = output_df['Ex_utility'] * 1000 / output_df['Af_m2']
    output_df['eff_exergy'] = output_df['Ex_min'] / output_df['el_total']
    output_df['eff_process_exergy'] = output_df['Ex_process'] / output_df['el_total']
    output_df['eff_utility_exergy'] = output_df['Ex_utility'] / output_df['el_total']
    output_df['eff_process_utility'] = output_df['Ex_process'] / output_df['Ex_utility']

    # calculate the percentage used by each component
    output_df['scu'] = output_df['el_chi_ht'] / output_df['el_total'] * 100
    output_df['scu_aux'] = output_df['el_aux_scu'] / output_df['el_total'] * 100
    output_df['lcu'] = output_df['el_chi_lt'] / output_df['el_total'] * 100
    output_df['lcu_aux'] = (output_df['el_fan_lcu'] + output_df['el_reheat_lcu']) / output_df['el_total'] * 100
    if tech == 'HCS_LD':
        output_df['oau'] = output_df['el_hp_oau'] / output_df['el_total'] * 100
        output_df['oau_aux'] = output_df['el_fan_oau'] / output_df['el_total'] * 100
    else:
        output_df['oau'] = output_df['el_chi_oau'] / output_df['el_total'] * 100
        output_df['oau_aux'] = (output_df['el_fan_oau'] + output_df['el_reheat_oau']) / output_df['el_total'] * 100
    output_df['ct'] = output_df['el_ct'] / output_df['el_total'] * 100

    ## export results
    output_df.to_csv(path_to_elec_csv(building, building_result_path, tech))
    return ex_df


def set_up_cooling_df(results):
    cooling_df = pd.DataFrame()
    # suppress to check calculation
    # cooling_df['qc_bui_sen_scu'] = results['q_scu_sen']
    # cooling_df['qc_bui_sen_lcu'] = results['q_lcu_sen']
    # cooling_df['qc_bui_sen_oau'] = results.filter(like='oau_Qc_bui_sen').sum(axis=1)
    # cooling_df['qc_bui_lat_lcu'] = results['q_coi_lcu'] - results['q_lcu_sen']
    # cooling_df['qc_bui_lat_oau'] = results.filter(like='oau_Qc_bui_total').sum(axis=1) - results.filter(
    #     like='oau_Qc_bui_sen').sum(axis=1)

    cooling_df['qc_sys_sen_scu'] = results['q_coi_scu'] if 'q_coi_scu' in results.columns.values else 0
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
    # if 'q_coi_scu' in results.columns.values:
    # if (abs(results['q_scu_sen'] - results['q_coi_scu']) < 1e3).all() == False:
    #     raise ValueError('Check SCU heat balance')

    return cooling_df


def set_up_heat_df(tech, results):
    heat_df = pd.DataFrame()
    heat_df['q_lcu_sen'] = results['q_lcu_sen']
    heat_df['q_scu_sen'] = results['q_scu_sen'] if 'status' not in tech else 0
    if tech == 'HCS_LD':
        total_oau_in = results.filter(like='q_oau_sen_in').sum(axis=1)
        total_oau_out = results['q_oau_sen_out'] + results['q_oau_sen_out_by']
    else:
        total_oau_in = results.filter(like='q_oau_sen_in').sum(axis=1)
        total_oau_out = results.filter(like='q_oau_sen_out').sum(axis=1)
        # q_bui_float = pd.to_numeric(results['q_bui']) + 0.01
    # total_oau_removed[total_oau_removed > q_bui_float] = 0
    total_oau = total_oau_out - total_oau_in
    heat_df['q_oau_sen'] = total_oau[total_oau >= 0]
    heat_df['q_oau_sen_add'] = total_oau[total_oau < 0] * (-1)
    heat_df = heat_df.fillna(0)

    # Bui_energy_bal_IN = results['q_bui'] + results.filter(like='q_oau_sen_in').sum(axis=1) + results.filter(
    #     like='SU_Qh').sum(axis=1)
    # Bui_energy_bal_OUT = results['q_oau_sen_out'] + results['q_scu_sen'] + results['q_lcu_sen'] + results.filter(
    #     like='SU_Qc').sum(axis=1)
    # balance
    balance_in = results['q_bui'] + heat_df['q_oau_sen_add'] + results.filter(like='SU_Qh').sum(axis=1)
    if 'status' not in tech:
        balance_out = heat_df['q_lcu_sen'] + heat_df['q_scu_sen'] + heat_df['q_oau_sen'] + results.filter(
            like='SU_Qc').sum(
            axis=1)
    else:
        balance_out = heat_df['q_lcu_sen'] + heat_df['q_oau_sen'] + results.filter(like='SU_Qc').sum(
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
        total_oau_out = results.filter(like='w_oau_out').sum(axis=1)
    else:
        total_oau_in = results.filter(like='w_oau_in').sum(axis=1)
        total_oau_out = results.filter(like='w_oau_out').sum(axis=1)
    # total_oau_removed[total_oau_removed < 0] = 0 # FIXME: check graph
    total_oau = total_oau_out - total_oau_in
    humidity_df['m_w_oau_removed'] = total_oau[total_oau > 0]
    humidity_df['m_w_oau_added'] = total_oau[total_oau < 0] * (-1)
    if 'hu_storage' in results.columns.values:
        humidity_df['m_w_stored'] = results['w_sto_charge']
    # humidity_df['m_w_discharged'] = results['w_sto_discharge']
    humidity_df = humidity_df.fillna(0)

    # test balance
    # balance_in = results['w_bui'] + results['w_sto_discharge'] + humidity_df['m_w_oau_added'] + results['SU_hu']
    # balance_out = humidity_df['m_w_lcu_removed'] + humidity_df['m_w_oau_removed'] + humidity_df['m_w_stored'] + results[
    #     'SU_dhu']
    # balance = balance_in - balance_out
    # balance = balance[abs(balance) > 1e-4]
    # if abs(balance.sum()) > 1E-6:
    #     print ('humidity balance: ', balance)
    return humidity_df


def set_up_air_flow_df(results):
    air_flow_df = pd.DataFrame()
    air_flow_df['infiltration'] = results['m_inf_in']
    oau_out = results.filter(like='m_oau_out').sum(axis=1)
    if 'm_oau_in_by' in results.columns:
        air_flow_df['OAU_in_bypass'] = results.filter(like='m_oau_in_by').sum(axis=1)
        air_flow_df['OAU_in'] = results.filter(like='m_oau_in').drop(
            columns=results.filter(like='m_oau_in_by').columns).sum(axis=1)
        balance = air_flow_df['OAU_in'] + air_flow_df['OAU_in_bypass'] + air_flow_df['infiltration'] - oau_out

    else:
        air_flow_df['OAU_in'] = results.filter(like='m_oau_in').sum(axis=1)
        balance = air_flow_df['OAU_in'] + air_flow_df['infiltration'] - oau_out

    # testing for balance
    # if abs(air_flow_df['OAU_in'].sum()) > 0 and abs(balance.sum()) >= 10:
    #     raise (ValueError, 'wrong air balance')
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
        if number_oau_in == 5:
            oau_range = [0, 2, 4, 6, 8]
        else:
            oau_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        for i in oau_range:
            m_label = 'm_oau_in_' + str(i + 1)
            T_label = 'OAU_T_SA' + str(i + 1)
            w_label = 'OAU_w_SA' + str(i + 1)
            results.ix[results[m_label] <= 0.01, T_label] = 0
            results.ix[results[m_label] <= 0.01, w_label] = 0
        operation_df['T_SA'] = results.filter(like='OAU_T_SA').sum(axis=1)
        operation_df['w_SA'] = results.filter(like='OAU_w_SA').sum(axis=1)

        number_oau_chillers = int(results.filter(like='cop_oau_chi').shape[1] / number_oau_in)
        for i in oau_range:
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
    line3, = ax.plot(x_ticks, hu_store_df['RH'], '-o', linewidth=2, markersize=4, label='%RH_actual')
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


def plot_co2_store(building, building_result_path, co2_store_df, tech):
    # extract parameters
    time_steps = co2_store_df.shape[0]
    x_ticks = co2_store_df.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)
    # line 1
    fig, ax1 = plt.subplots(figsize=fig_size)
    line1, = ax1.plot(x_ticks, co2_store_df['ppm'], '-o', color='darkcyan', linewidth=2, markersize=4, label='ppm')
    line3, = ax1.plot(x_ticks, co2_store_df['co2_RA_ppm'], '-o', color='darkred', linewidth=2, markersize=4,
                      label='RA_ppm')
    ax1.set_ylabel('CO2 concentration [ppm]', fontsize=14)
    ax1.set(xlim=(1, time_steps), ylim=(1, 1400))
    ax1.legend(loc='upper left')
    # line 2
    ax2 = ax1.twinx()
    line2, = ax2.plot(x_ticks, co2_store_df['m3'], '-o', color='darkorange', linewidth=2, markersize=4, label='m3')
    ax2.set_ylabel('CO2 volume [m3]', fontsize=14)
    ax2.set(xlim=(1, time_steps), ylim=(1, 100))
    ax2.set_xticks(x_ticks_shown)
    ax2.legend(loc='upper right')
    # line 3
    # ax3 = ax1.twinx()
    # line3, = ax3.plot(x_ticks, co2_store_df['co2_RA_ppm'], '-o', color='darkred', linewidth=2, markersize=4, label='RA_ppm')
    # ax3.set(xlim=(1, time_steps), ylim=(1, 1200))
    # ax3.legend(loc='upper right')

    plt.grid(True)
    plt.xlabel('Time [hr]', fontsize=14)
    # plt.ylabel('CO2 concentration [ppm] ; CO2 volume [m3]', fontsize=14)
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'co2_store'))
    plt.close(fig)
    return np.nan


def calc_co2_level(co2_RA_ppm, co2_occupant_m3, m_air_out, rho_air):
    if co2_RA_ppm <= CO2_env_ppm:
        co2_RA_ppm = CO2_env_ppm
    co2_out_m3perh = ((m_air_out * 3600) / rho_air) * (CO2_env_ppm - co2_RA_ppm)
    co2_change_m3perh = co2_out_m3perh + co2_occupant_m3
    return co2_change_m3perh


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
    ax1.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'water_flow'))
    return np.nan


def plot_air_flow(air_flow_df, results, tech, building, building_result_path):
    specific_air_flow_df = (air_flow_df * 1000) / results['Af_m2'].max()
    # extract parameters
    time_steps = results.shape[0]
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    colors = plt.cm.Set2(np.linspace(0, 1, len(specific_air_flow_df.columns)))
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(specific_air_flow_df.shape[0])
    # plot bars
    for c in range(len(specific_air_flow_df.columns)):
        column = specific_air_flow_df.columns[c]
        ax.bar(x_ticks, specific_air_flow_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + specific_air_flow_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Air flow [g/s/m2]', xlim=(1, time_steps), ylim=(0, 2))
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
    ax1.legend(loc='upper right')
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
    return np.nan


def plot_electricity_usages(building, building_result_path, electricity_df, results, tech, day):
    t_0 = results.index.min()
    t_end = results.index.max()
    # reset index
    Af_m2 = results['Af_m2'].mean()
    electricity_per_area_df = electricity_df * 1000 / Af_m2
    # extract parameters
    time_steps = electricity_df.shape[0]
    x_ticks = electricity_df.index.values
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
    colors = ['#fae57c', '#7d723e', '#ffc0cb', '#7f6065', '#ffc3a0', '#7f6150', '#b0e0e6', '#69868a',
              '#90ce92', '#567b57']
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(electricity_per_area_df.shape[0])
    # plot bars
    for c in range(len(electricity_per_area_df.columns)):
        column = electricity_per_area_df.columns[c]
        label_dict = {'el_chi_lt':'RAU chiller', 'el_fan_lcu':'RAU fan', 'el_reheat_lcu': 'RAU reheat',
                      'el_fan_oau':'OAU fan', 'el_reheat_oau':'OAU reheat', 'el_chi_oau':'OAU chiller',
                      'el_chi_ht':'SCU chiller', 'el_aux_scu':'SCU aux', 'el_ct': 'Cooling Tower'}
        ax.bar(x_ticks, electricity_per_area_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=label_dict[column])
        y_offset = y_offset + electricity_per_area_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Electricity Use [Wh/m2]', xlim=(t_0, t_end), ylim=(0, 35))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.set_xticks(x_ticks_shown)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    total_el_float = pd.to_numeric(results['SU_elec'] * 1000 / Af_m2)
    ax1.plot(x_ticks, total_el_float, '-o', linewidth=2, markersize=4, label='total electricity use', color='steelblue')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax.legend(loc='upper right')

    if day != '':
        name = CONFIG_TABLE[tech]
        plt.title(name + ' ' + building + ' ' + day, fontsize=14)
    else:
        plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    filename = 'el_usages_' + day
    fig.savefig(path_to_save_fig(building, building_result_path, tech, filename))
    return np.nan


def get_hourly_oau_operations(tech, results, composite_df):
    # initialization
    hourly_chiller_usage = results.filter(like='el_oau_chi').fillna(0)
    T_low_C = 8.1
    T_high_C = 14.1
    T_interval = 0.65  # 0.5
    T_OAU_offcoil = np.arange(T_low_C, T_high_C, T_interval)
    hourly_chilled_water_temperature, hourly_evap_temperature, hourly_water_coil_cond = [], [], []
    hourly_water_removed = {}
    hourly_T_EA, hourly_w_EA, hourly_m_w_add = [], [], []
    # hourly calculation
    for i in range(results.shape[0]):
        t = i + 1
        chiller_timestep = hourly_chiller_usage.loc[i + 1]
        if chiller_timestep[chiller_timestep > 0].values.size > 0:
            # oau chiller operation
            chiller_used = str(chiller_timestep[chiller_timestep > 0].index).split('chi')[1].split('_')[0]
            chiller_number = int(chiller_used) - 1
            hourly_chilled_water_temperature.append(T_OAU_offcoil[chiller_number])
            hourly_evap_temperature.append(T_OAU_offcoil[chiller_number] - 2.0)
            # oau states
            if tech == 'HCS_ER0':
                m_w_cond_kgpers = calc_m_w_cond_results('w_OA1_h_', 'w_OA1_c_', chiller_used, i, results)
                if 'm_w_removed_1' not in results.columns.values:
                    # save the amount of water removed in the recovery
                    results['m_w_removed_1'] = np.full(results.shape[0], np.nan)
                    results['T_w_removed_1'] = np.full(results.shape[0], np.nan)
                results['m_w_removed_1'][t] = results['m_oau_in_' + chiller_used][t] * (composite_df['w_OA'][t] - composite_df['w_OA1'][t])
                results['T_w_removed_1'][t] = results['T_OA1_' + chiller_used][t]
                hourly_T_EA.append(results['T_EA_' + chiller_used][t])
                hourly_w_EA.append(results['w_EA_' + chiller_used][t])
                hourly_m_w_add.append((results['w_RA1_' + chiller_used][t] - 10.29 / 1000)*results['m_oau_out'][t])
            elif tech == 'HCS_coil':
                m_w_cond_kgpers = calc_m_w_cond_results('w_OA1_', 'w_OA2_', chiller_used, i, results) / 1000
                hourly_T_EA.append(results['T_RA'][t])
                hourly_w_EA.append(10.29)
                hourly_m_w_add.append(np.nan)
            elif tech == 'HCS_3for2':
                m_w_cond_kgpers = calc_m_w_cond_composite('w_OA1_', 'w_OA2_', chiller_used, i, results, composite_df)
                # if t == 1:
                #     results['m_w_removed_1'] = np.full(results.shape[0], np.nan)
                #     results['T_w_removed_1'] = np.full(results.shape[0], np.nan)
                #     results['m_w_removed_2'] = np.full(results.shape[0], np.nan)
                #     results['T_w_removed_2'] = np.full(results.shape[0], np.nan)
                # results['m_w_removed_1'][t] = results['m_oau_in_' + chiller_used][t] * (
                #             composite_df['w_OA'][t] - composite_df['w_OA1_' + chiller_used][t])
                # results['T_w_removed_1'][t] = composite_df['T_OA1_' + chiller_used][t]
                # results['m_w_removed_2'][t] = calc_m_w_cond_composite('w_OA2_', 'w_OA3_', chiller_used, i,
                #                                                                  results, composite_df)
                # results['m_w_removed_2'][t] = composite_df['T_OA3_' + chiller_used][t]
                hourly_T_EA.append(composite_df['OAU_T_EA_' + chiller_used][t])
                hourly_w_EA.append(composite_df['OAU_w_EA_' + chiller_used][t]*1000)
                hourly_m_w_add.append(np.nan)
            elif tech == 'HCS_IEHX':
                # water condensed on coil
                m_w_cond_kgpers = calc_m_w_cond_composite('w_OA2_', 'w_OA3_', chiller_used, i, results, composite_df)
                if 'm_w_removed_1' not in results.columns.values:
                    # save the amount of water removed in the recovery
                    results['m_w_removed_1'] = np.full(results.shape[0], np.nan)
                    results['T_w_removed_1'] = np.full(results.shape[0], np.nan)
                w_OA_OA1 = composite_df['w_ext'][t]/1000 - composite_df['w_OA1'][t] if composite_df['w_ext'][t]/1000 - composite_df['w_OA1'][t] > 0.0 else 0
                results['m_w_removed_1'][t] = results['m_oau_in_' + chiller_used][t] * (w_OA_OA1)
                results['T_w_removed_1'][t] = composite_df['T_OA1'][t]
                hourly_T_EA.append(composite_df['T_EA'][t])
                hourly_w_EA.append(composite_df['w_EA'][t]*1000)
                hourly_m_w_add.append((composite_df['w_EA'][t] - 10.29 / 1000)*results['m_oau_out'][t])
            else:
                m_w_cond_kgpers = 0
            hourly_water_coil_cond.append(m_w_cond_kgpers)

        else:
            if tech == 'HCS_LD':
                # m_w_cond_kgpers = results['m_oau_in'][t] * (results['w_OA1'][t] / 1000 - results['w_SA'][t])
                # hourly_chilled_water_temperature.append(results['OAU_T_SA'][t])  # TODO: change to desiccant temperature
                # hourly_water_coil_cond.append(m_w_cond_kgpers)
                # hourly_evap_temperature.append(results['T_s_i_de'][t]-273.15)
                hourly_chilled_water_temperature.append(np.nan)
                hourly_water_coil_cond.append(np.nan)
                hourly_evap_temperature.append(np.nan)
                # water removed
                # results['m_w_removed_1'] = results['m_oau_in']*(results['w_ext']/1000 - results['w_OA1']/1000)
                # results['T_w_removed_1'] = results['T_OA1']
                # results['m_w_removed_2'] = results['m_oau_in'] * (results['w_ext'] / 1000 - results['w_OA1'] / 1000)
                # results['T_w_removed_2'] = results['T_OA1']
                hourly_T_EA = results['T_EA_K'] - 273.15
                hourly_w_EA = results['w_EA']*1000
                hourly_m_w_add.append(np.nan)
            else:
                hourly_chilled_water_temperature.append(np.nan)
                hourly_water_coil_cond.append(np.nan)
                hourly_evap_temperature.append(np.nan)
                hourly_T_EA.append(np.nan)
                hourly_w_EA.append(np.nan)
                hourly_m_w_add.append(np.nan)

    results['T_chw'] = hourly_chilled_water_temperature
    results['T_evap'] = hourly_evap_temperature
    results['m_w_coil_cond'] = hourly_water_coil_cond
    results['OAU_T_EA'] = hourly_T_EA
    results['OAU_w_EA'] = hourly_w_EA
    results['m_w_add'] = hourly_m_w_add
    return results


def get_reheating_energy(tech, results):
    if tech == 'HCS_coil' or 'HCS_ER0' or 'HCS_IEHX':
        results['q_reheat'] = results.filter(like='reheat').sum(axis=1)
    else:
        results['q_reheat'] = np.zeros(results.shape[0])
    return results


def plot_exergy_loads(building, building_result_path, exergy_df, results, tech):
    Af_m2 = results['Af_m2'].mean()
    eff_exergy = exergy_df['eff_process_exergy'].values
    # del exergy_df['eff_exergy']
    exergy_per_area_df = exergy_df * 1000 / Af_m2
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
    colors = ['#AD4456', '#D76176', '#E3909F', '#742D3A', '#270F14', '#FF4B31']  # PINKS
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(exergy_per_area_df.shape[0])
    # plot bars
    # columns = ['Ex_min_Qc','Ex_min_air','Ex_min_water']
    columns = ['Ex_process_OAU', 'Ex_process_RAU', 'Ex_process_SCU']
    for c in range(len(columns)):
        column = columns[c]
        ax.bar(x_ticks, exergy_per_area_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + exergy_per_area_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Exergy loads [Wh/m2]', xlim=(1, time_steps), ylim=(0, 5))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.set_xticks(x_ticks_shown)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    eff_exergy_float = pd.to_numeric(eff_exergy)
    ax1.plot(x_ticks, eff_exergy_float, '-o', linewidth=2, markersize=4, label='exergy efficiency', color='darkgrey')
    ax1.set(ylabel='Exergy Efficiency [-]', xlim=ax.get_xlim(), ylim=(0, 1))
    ax.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, building_result_path, tech, 'exergy'))
    return np.nan


def format_func(value, tick_number):
    return value % 24


def plot_exergy_usages(building, building_result_path, exergy_df, results, tech, day):
    timesteps = results.shape[0]
    results.set_index(np.arange(1, timesteps + 1, 1), inplace=True)
    exergy_df.set_index(np.arange(1, timesteps + 1, 1), inplace=True)
    t_0 = results.index.min()
    t_end = results.index.max()
    # reset index
    Af_m2 = results['Af_m2'].mean()
    exergy_per_area_df = exergy_df * 1000 / Af_m2
    # extract parameters
    time_steps = exergy_df.shape[0]
    x_ticks = exergy_df.index.values
    fig_size = set_figsize(time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1

    COLOR_TABLE = {'Ex_process_total': '#080808', 'Ex_utility_total': '#707070',
                   'el_Wh_total_per_Af': '#C8C8C8'}  # Gray scale
    KEY_TABLE = {'Ex_process_total': 'process exergy', 'Ex_utility_total': 'utility exergy',
                 'el_Wh_total_per_Af': 'electricity'}

    # plot bars
    total_el_float = pd.to_numeric(results['SU_elec'] * 1000 / Af_m2)
    ax.bar(x_ticks, total_el_float, bar_width, alpha=opacity, color=COLOR_TABLE['el_Wh_total_per_Af'],
           label=KEY_TABLE['el_Wh_total_per_Af'])
    for column in ['Ex_utility_total', 'Ex_process_total']:
        ax.bar(x_ticks, exergy_per_area_df[column], bar_width, alpha=opacity, color=COLOR_TABLE[column],
               label=KEY_TABLE[column])

    ax.set(xlabel='Time [hr]', ylabel='Energy [Wh/m2]', xlim=(t_0, t_end), ylim=(0, 20))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper right', fontsize=12, ncol=3, mode="expand")

    if day != '':
        name = CONFIG_TABLE[tech]
        plt.title(name + ' ' + building + ' ' + day, fontsize=14)
    else:
        plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    filename = 'exergy_usages_' + day
    fig.savefig(path_to_save_fig(building, building_result_path, tech, filename))
    return np.nan


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


def path_to_osmose_composite(building_result_path, tech):
    format = 'csv'
    path_to_file = os.path.join(building_result_path, '%s_composite.%s' % (tech, format))
    return path_to_file


def path_to_save_fig(building, building_result_path, tech, fig_type):
    path_to_file = os.path.join(building_result_path, '%s_%s_%s.png' % (building, tech, fig_type))
    return path_to_file


def path_to_elec_csv(building, building_result_path, tech):
    path_to_file = os.path.join(building_result_path, '%s_%s_el.csv' % (building, tech))
    return path_to_file


def path_to_elec_unit_csv(building, building_result_path, tech):
    path_to_file = os.path.join(building_result_path, '%s_%s_el_kWh_m2.csv' % (building, tech))
    return path_to_file


def path_to_chiller_csv(building, building_result_path, tech, name):
    path_to_file = os.path.join(building_result_path, '%s_%s_%s.csv' % (building, tech, name))
    return path_to_file


if __name__ == '__main__':
    buildings = ["B003"]
    # buildings = ["B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009", "B010"]
    tech = ["HCS_coil"]
    # tech = ["HCS_3for2", "HCS_IEHX", "HCS_coil", "HCS_LD", "HCS_ER0"]
    #  tech = ["HCS_ER0", "HCS_3for2", "HCS_IEHX", "HCS_coil", "HCS_LD", "HCS_status_quo"]
    # cases = ["WTP_CBD_m_WP1_RET", "WTP_CBD_m_WP1_OFF", "WTP_CBD_m_WP1_HOT"]
    # cases = ["HKG_CBD_m_WP1_RET", "HKG_CBD_m_WP1_OFF", "HKG_CBD_m_WP1_HOT",
    #          "ABU_CBD_m_WP1_RET", "ABU_CBD_m_WP1_OFF", "ABU_CBD_m_WP1_HOT",
    #          "MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT",
    #          "WTP_CBD_m_WP1_RET", "WTP_CBD_m_WP1_OFF", "WTP_CBD_m_WP1_HOT"]
    # cases = ["MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT"]
    cases = ["WTP_CBD_m_WP1_OFF"]
    # result_path = "C:\\Users\\Shanshan\\Documents\\WP1_results"
    result_path = "E:\\test_0805"
    # result_path = "C:\\Users\\Shanshan\\Documents\\WP1_0421"
    for case in cases:
        folder_path = os.path.join(result_path, case)
        for building in buildings:
            building_time = building + "_1_24"
            building_result_path = os.path.join(folder_path, building_time)
            # building_result_path = os.path.join(building_result_path, "SU")
            print building_result_path
            main(building, tech, building_result_path)
