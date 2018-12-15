from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

# TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD']
TECHS = ['HCS_coil']
# TECHS = ['HCS_LD']
# TECHS = ['HCS_coil', 'HCS_LD']
PATH_TO_RESULT_FOLDER = 'C:\\Users\\Shanshan\\Documents\\0_Shanshan_Hsieh\\WP1\\results\\'

Af_m2 = {'B001': 28495.062, 'B002': 28036.581, 'B007': 30743.113}


def main():
    el_use_sum = {}
    for tech in TECHS:
        building = 'B002'
        results = pd.read_csv(path_to_osmose_results(building, tech)).T.reset_index()
        results = results.rename(columns=results.iloc[0])[1:]
        el_use_sum[tech] = results['SU_elec'].sum()

        ## plot T_SA and w_SA
        operation_df = set_up_operation_df(tech, results)
        plot_supply_temperature_humidity(building, operation_df, tech)

        ## plot water balance
        humidity_df = set_up_humidity_df(tech, results)
        plot_water_balance(building, humidity_df, results, tech)

        ## plot heat balance
        heat_df = set_up_heat_df(tech, results)
        plot_heat_balance(building, heat_df, results, tech)

        ## plot electricity usage
        plot_electricity_usage(building, results, tech)
        electricity_df = set_up_electricity_df(tech, results)
        calc_el_stats(building, electricity_df, results, tech)
        plot_electricity_usages(building, electricity_df, results, tech)

    print el_use_sum
    return


def set_up_electricity_df(tech, results):
    electricity_df = pd.DataFrame()
    # lcu
    electricity_df['el_chi_lt'] = results['el_chi_lt']
    electricity_df['el_aux_lcu'] = results['el_lcu_fan']
    # oau
    if tech == 'HCS_LD':
        electricity_df['el_aux_oau'] = results['el_oau_in_fan'] + results['el_oau_out_fan']
        electricity_df['el_hp_oau'] = results['el_LDHP']
    else:
        electricity_df['el_aux_oau'] = results.filter(like='el_oau_in').sum(axis=1) + results['el_oau_out_fan']
        electricity_df['el_chi_oau'] = results.filter(like='el_oau_chi').sum(axis=1)

    # scu
    electricity_df['el_chi_ht'] = results['el_chi_ht']
    electricity_df['el_aux_scu'] = results['el_scu_pump']
    # ct
    electricity_df['el_ct'] = results['el_ct']

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


def calc_el_stats(building, electricity_df, results, tech):
    output_df = electricity_df.copy()
    # calculate electricity used in each technology
    output_df['el_total'] = output_df.sum(axis=1)
    output_df['el_scu'] = output_df['el_aux_scu'] + output_df['el_chi_ht']
    output_df['el_lcu'] = output_df['el_aux_lcu'] + output_df['el_chi_lt']
    output_df['el_oau'] = output_df['el_aux_oau'] + output_df['el_chi_oau']
    # calculate total cooling energy produced
    cooling_df = calc_cooling_energy(results)
    output_df['qc_bui_sen_total'] = cooling_df.filter(like='qc_bui_sen').sum(axis=1)
    output_df['qc_bui_lat_total'] = cooling_df.filter(like='qc_bui_lat').sum(axis=1)
    output_df['qc_sys_scu'] = cooling_df['qc_sys_sen_scu']
    output_df['qc_sys_lcu'] = cooling_df['qc_sys_sen_lcu'] + cooling_df['qc_sys_lat_lcu']
    output_df['qc_sys_oau'] = cooling_df['qc_sys_sen_oau'] + cooling_df['qc_sys_lat_oau']
    output_df['qc_sys_sen_total'] = cooling_df.filter(like='qc_sys_sen').sum(axis=1)
    output_df['qc_sys_lat_total'] = cooling_df.filter(like='qc_sys_lat').sum(axis=1)

    # add total row in the bottom
    total_df = pd.DataFrame(output_df.sum()).T
    output_df = output_df.append(total_df).reset_index().drop(columns='index')

    # calculate values from column operations
    output_df['qc_bui_total'] = output_df['qc_bui_sen_total'] + output_df['qc_bui_lat_total']
    output_df['cop_cooling'] = output_df['qc_bui_total']/output_df['el_total']
    output_df['qc_sys_total'] = output_df['qc_sys_sen_total'] + output_df['qc_sys_lat_total']
    output_df['cop_system'] = output_df['qc_sys_total']/output_df['el_total']
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
    output_df.to_csv(path_to_elec_csv(building, tech))
    return np.nan


def calc_cooling_energy(results):
    cooling_df = pd.DataFrame()
    cooling_df['qc_bui_sen_scu'] = results['q_scu_sen']
    cooling_df['qc_bui_sen_lcu'] = results['q_lcu_sen']
    cooling_df['qc_bui_sen_oau'] = results.filter(like='oau_Qc_bui_sen').sum(axis=1)
    cooling_df['qc_bui_lat_lcu'] = results['q_coi_lcu'] - results['q_lcu_sen']
    cooling_df['qc_bui_lat_oau'] = results.filter(like='oau_Qc_bui_total').sum(axis=1) - results.filter(like='oau_Qc_bui_sen').sum(axis=1)

    cooling_df['qc_sys_sen_scu'] = results['q_coi_scu']
    cooling_df['qc_sys_sen_lcu'] = results['q_lcu_sen']
    cooling_df['qc_sys_sen_oau'] = results.filter(like='oau_Qc_sen').sum(axis=1)
    cooling_df['qc_sys_lat_lcu'] = results['q_coi_lcu'] - results['q_lcu_sen']
    cooling_df['qc_sys_lat_oau'] = results.filter(like='oau_Qc_total').sum(axis=1) - results.filter(like='oau_Qc_sen').sum(axis=1)

    # check validity of results
    if cooling_df.min().min() < 0:
        columns = np.unique(np.where(cooling_df < 0)[1])
        names = []
        for i in columns:
            names.append(cooling_df.columns[i])
        raise ValueError('Check cooling results from osmose: ',' ,'.join(names))
    if (abs(results['q_scu_sen']-results['q_coi_scu'])<1e3).all() == False:
        raise ValueError('Check SCU heat balance')

    return cooling_df


def set_up_heat_df(tech, results):
    heat_df = pd.DataFrame()
    # humidity_df['m_w_infil_occupant'] = results['w_bui']
    heat_df['q_lcu_sen'] = results['q_lcu_sen']
    heat_df['q_scu_sen'] = results['q_scu_sen']
    if tech == 'HCS_LD':
        total_oau_removed = results['q_oau_sen_out'] - results['q_oau_sen_in']
    else:
        total_oau_removed = results['q_oau_sen_out'] - (
                results['q_oau_sen_in_1'] + results['q_oau_sen_in_2'] + results['q_oau_sen_in_3'])
    # q_bui_float = pd.to_numeric(results['q_bui']) + 0.01
    # total_oau_removed[total_oau_removed > q_bui_float] = 0
    heat_df['q_oau_sen'] = total_oau_removed
    return heat_df


def set_up_humidity_df(tech, results):
    humidity_df = pd.DataFrame()
    # humidity_df['m_w_infil_occupant'] = results['w_bui']
    humidity_df['m_w_lcu_removed'] = results['w_lcu']
    if tech == 'HCS_LD':
        total_oau_removed = results['w_oau_out'] - results['w_oau_in']
    else:
        total_oau_removed = results['w_oau_out'] - (
                results['w_oau_in_1'] + results['w_oau_in_2'] + results['w_oau_in_3'])
    total_oau_removed[total_oau_removed < 0] = 0
    humidity_df['m_w_oau_removed'] = total_oau_removed
    humidity_df['m_w_stored'] = results['w_sto_charge']
    # humidity_df['m_w_discharged'] = results['w_sto_discharge']
    return humidity_df


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
        # output actual temperature
        results.ix[results.m_oau_in_1 <= 0.01, 'OAU_T_SA1'] = 0
        results.ix[results.m_oau_in_2 <= 0.01, 'OAU_T_SA2'] = 0
        results.ix[results.m_oau_in_3 <= 0.01, 'OAU_T_SA3'] = 0
        operation_df['T_SA'] = results.apply(lambda row: row.OAU_T_SA1 + row.OAU_T_SA2 + row.OAU_T_SA3, axis=1)
        results.ix[results.m_oau_in_1 <= 0.01, 'OAU_w_SA1'] = 0
        results.ix[results.m_oau_in_2 <= 0.01, 'OAU_w_SA2'] = 0
        results.ix[results.m_oau_in_3 <= 0.01, 'OAU_w_SA3'] = 0
        operation_df['w_SA'] = results.apply(lambda row: row.OAU_w_SA1 + row.OAU_w_SA2 + row.OAU_w_SA3, axis=1)
        for i in range(3):
            for j in range(10):
                cop_tag_name = 'cop_oau_chi' + str(i + 1) + '_' + str(j + 1)
                el_tag_name = 'el_oau_chi' + str(i + 1) + '_' + str(j + 1)
                results.ix[results[el_tag_name] <= 0.00, cop_tag_name] = 0
        operation_df['COP'] = results.filter(regex='cop').sum(axis=1)
    return operation_df


def plot_heat_balance(building, heat_df, results, tech):
    # extract parameters
    time_steps = results.shape[0] - 1
    x_ticks = results.index.values
    fig_size = set_figsize(time_steps)
    x_ticks_shown = set_xtick_shown(x_ticks, time_steps)

    # plotting
    fig, ax = plt.subplots(figsize=fig_size)
    bar_width = 0.5
    opacity = 1
    colors = plt.cm.Set2(np.linspace(0, 1, len(heat_df.columns)))
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(heat_df.shape[0])
    # plot bars
    for c in range(len(heat_df.columns)):
        column = heat_df.columns[c]
        ax.bar(x_ticks, heat_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + heat_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Sensible heat [kWh]', xlim=(1, time_steps), ylim=(0, 2000))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    q_bui_float = pd.to_numeric(results['q_bui'])
    ax1.plot(x_ticks, q_bui_float, '-o', linewidth=2, markersize=4, label='sensible heat gain')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.legend(loc='upper right')
    ax1.set_xticks(x_ticks_shown)
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, tech, 'heat'))


def plot_water_balance(building, humidity_df, results, tech):
    # extract parameters
    time_steps = results.shape[0] - 1
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
    fig.savefig(path_to_save_fig(building, tech, 'water_flow'))


def plot_electricity_usage(building, results, tech):
    results['el_per_Af'] = results['SU_elec'] * 1000 / Af_m2[building]
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
    fig.savefig(path_to_save_fig(building, tech, 'el_usage'))

def plot_electricity_usages(building, electricity_df, results, tech):
    electricity_per_area_df = electricity_df * 1000 / Af_m2[building]
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
    ax.set(xlabel='Time [hr]', ylabel='Electricity Use [kW]', xlim=(1, time_steps), ylim=(0, 35))
    ax.xaxis.label.set_size(14)
    ax.yaxis.label.set_size(14)
    ax.set_xticks(x_ticks_shown)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    total_el_float = pd.to_numeric(results['SU_elec'] * 1000 / Af_m2[building])
    ax1.plot(x_ticks, total_el_float, '-o', linewidth=2, markersize=4, label='total electricity use', color='steelblue')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax.legend(loc='upper right')
    plt.title(building + '_' + tech, fontsize=14)
    # plt.show()
    # plot layout
    fig.savefig(path_to_save_fig(building, tech, 'el_usages'))


def plot_supply_temperature_humidity(building, operation_df, tech):
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
        ax.bar(x_ticks, operation_df['COP'], bar_width, alpha=opacity, label='COP')
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
        fig.savefig(path_to_save_fig(building, tech, 'OAU_supply'))
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
        fig.savefig(path_to_save_fig(building, tech, 'OAU_supply'))
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

def path_to_osmose_results(building, tech):
    format = 'csv'
    path_to_folder = PATH_TO_RESULT_FOLDER + building
    path_to_file = os.path.join(path_to_folder, '%s_outputs.%s' % (tech, format))
    return path_to_file

def path_to_save_fig(building, tech, fig_type):
    path_to_folder = PATH_TO_RESULT_FOLDER + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_%s.png' % (building, tech, fig_type))
    return path_to_file

def path_to_elec_csv(building, tech):
    path_to_folder = PATH_TO_RESULT_FOLDER + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_el.csv' % (building, tech))
    return path_to_file


if __name__ == '__main__':
    main()
