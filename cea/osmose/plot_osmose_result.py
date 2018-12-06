from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

# TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD']
TECHS = ['HCS_coil']
Af_m2 = {'B001': 28495.062, 'B002': 28036.581, 'B007': 30743.113}


def main():
    el_use_sum = {}
    for tech in TECHS:
        building = 'B001'
        results = pd.read_csv(path_to_osmose_results(building, tech)).T.reset_index()
        results = results.rename(columns=results.iloc[0])[1:]
        el_use_sum[tech] = results['SU_elec'].sum()

        ## plot T_SA and w_SA
        operation_df = set_up_operation_df(tech, results)
        plot_supply_temperature_humidity(building, operation_df, tech)

        ## plot electricity usage
        plot_electricity_usage(building, results, tech)
        electricity_df = set_up_electricity_df(tech, results, building)
        plot_electricity_usages(building, electricity_df, results, tech)

        ## plot water balance
        humidity_df = set_up_humidity_df(tech, results)
        plot_water_balance(building, humidity_df, results, tech)

        ## plot heat balance
        heat_df = set_up_heat_df(tech, results)
        plot_heat_balance(building, heat_df, results, tech)

    print el_use_sum
    return


def set_up_electricity_df(tech, results, building):
    electricity_df = pd.DataFrame()
    # lcu
    electricity_df['el_chi_lt'] = results['el_chi_lt'] * 1000 / Af_m2[building]
    electricity_df['el_aux_lcu'] = results['el_lcu_fan'] * 1000 / Af_m2[building]
    # oau
    if tech == 'HCS_LD':
        total_el_aux_oau = results['el_oau_in_fan'] + results['el_oau_out_fan']
        electricity_df['el_hp_oau'] = results['el_LDHP'] * 1000 / Af_m2[building]
    else:
        total_el_aux_oau = results['el_oau_in1_fan'] + results['el_oau_in2_fan'] + results['el_oau_in3_fan'] + results[
            'el_oau_out_fan']
        electricity_chi_oau = 0
        for i in range(3):
            for j in range(10):
                tag_name = 'el_oau_chi' + str(i + 1) + '_' + str(j + 1)
                electricity_chi_oau = electricity_chi_oau + results[tag_name]
        electricity_df['el_chi_oau'] = electricity_chi_oau * 1000 / Af_m2[building]
    electricity_df['el_aux_oau'] = total_el_aux_oau * 1000 / Af_m2[building]
    # scu
    electricity_df['el_chi_ht'] = results['el_chi_ht'] * 1000 / Af_m2[building]
    electricity_df['el_aux_scu'] = results['el_scu_pump'] * 1000 / Af_m2[building]
    # ct
    electricity_df['el_ct'] = results['el_ct'] * 1000 / Af_m2[building]

    # statistics
    el_stats_df = electricity_df.copy()
    # el_stats_df = el_stats_df.append(el_stats_df.sum(), ignore_index=True)
    total_df = pd.DataFrame(el_stats_df.sum()).T
    el_stats_df = el_stats_df.append(total_df).reset_index().drop(columns='index')
    el_stats_df['el_total'] = el_stats_df.sum(axis=1)
    el_stats_df['scu'] = el_stats_df['el_chi_ht'] / el_stats_df['el_total'] * 100
    el_stats_df['scu_aux'] = el_stats_df['el_aux_scu'] / el_stats_df['el_total'] * 100
    el_stats_df['lcu'] = el_stats_df['el_chi_lt'] / el_stats_df['el_total'] * 100
    el_stats_df['lcu_aux'] = el_stats_df['el_aux_lcu'] / el_stats_df['el_total'] * 100
    if tech == 'HCS_LD':
        el_stats_df['oau'] = el_stats_df['el_hp_oau'] / el_stats_df['el_total'] * 100
        el_stats_df['oau_aux'] = el_stats_df['el_aux_oau'] / el_stats_df['el_total'] * 100
    else:
        el_stats_df['oau'] = el_stats_df['el_chi_oau'] / el_stats_df['el_total'] * 100
        el_stats_df['oau_aux'] = el_stats_df['el_aux_oau'] / el_stats_df['el_total'] * 100

    el_stats_df['ct'] = el_stats_df['el_ct'] / el_stats_df['el_total'] * 100
    el_stats_df.to_csv(path_to_elec_csv(building, tech))
    return electricity_df


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
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    q_bui_float = pd.to_numeric(results['q_bui'])
    ax1.plot(x_ticks, q_bui_float, '-o', linewidth=2, markersize=4, label='sensible heat gain')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.legend(loc='upper right')
    ax1.set_xticks(x_ticks_shown)
    # plt.show()
    # plot layout
    fig.savefig(path_to_heat_fig(building, tech))



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
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    w_bui_float = pd.to_numeric(results['w_bui'])
    ax1.plot(x_ticks, w_bui_float, '-o', linewidth=2, markersize=4, label='water gain')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax1.set_xticks(x_ticks_shown)
    ax.legend(loc='upper right')
    # plt.show()
    # plot layout
    fig.savefig(path_to_water_flow_fig(building, tech))



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
    ax.legend(loc='lower right')
    ax.set(xlabel='Time [hr]', ylabel='Electricity Usage [Wh/m2]', xlim=(1, time_steps), ylim=(0, 35))
    ax.set_xticks(x_ticks_shown)
    ax.grid(True)
    fig.savefig(path_to_el_usage_fig(building, tech))
    # plt.show()


def plot_electricity_usages(building, electricity_df, results, tech):
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
    y_offset = np.zeros(electricity_df.shape[0])
    # plot bars
    for c in range(len(electricity_df.columns)):
        column = electricity_df.columns[c]
        ax.bar(x_ticks, electricity_df[column], bar_width, bottom=y_offset, alpha=opacity, color=colors[c],
               label=column)
        y_offset = y_offset + electricity_df[column]
    ax.set(xlabel='Time [hr]', ylabel='Electricity Use [kW]', xlim=(1, time_steps), ylim=(0, 35))
    ax.set_xticks(x_ticks_shown)
    ax.legend(loc='upper left')
    # plot line
    ax1 = ax.twinx()
    total_el_float = pd.to_numeric(results['SU_elec'] * 1000 / Af_m2[building])
    ax1.plot(x_ticks, total_el_float, '-o', linewidth=2, markersize=4, label='total electricity use', color='steelblue')
    ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
    ax.legend(loc='upper right')
    # plt.show()
    # plot layout
    fig.savefig(path_to_el_usages_fig(building, tech))


def plot_supply_temperature_humidity(building, operation_df, tech):
    # plot
    time_steps = operation_df.shape[0]
    fig_size = (6.6, 5) if time_steps <= 24 else (15.4, 5)
    fig, ax = plt.subplots(figsize=fig_size)
    x_ticks = operation_df.index.values
    x_ticks_shown = operation_df.index.values if time_steps <= 24 else np.arange(0, time_steps, 12)
    time_steps = operation_df.shape[0]
    line1, = ax.plot(x_ticks, operation_df['T_SA'], '-o', linewidth=2, markersize=4,
                     label='T,supply,OAU')
    line2, = ax.plot(x_ticks, operation_df['w_SA'], '-o', linewidth=2, markersize=4, label='w,supply,OAU')
    ax.legend(loc='lower right')
    ax.set_xticks(x_ticks_shown)
    ax.grid(True)
    plt.xlim(1, time_steps)
    plt.ylim(0, 25)
    plt.xlabel('Time [hr]')
    plt.ylabel('Temperature [C] ; Humidity Ratio [g/kg d.a.]')
    # plt.show()
    fig.savefig(path_to_OAU_supply_fig(building, tech))
    plt.close(fig)
    return np.nan


def path_to_osmose_results(building, tech):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_outputs.%s' % (tech, format))
    return path_to_file


def path_to_OAU_supply_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_OAU_supply.png' % (building, tech))
    return path_to_file

## auxiliary functions
def set_xtick_shown(x_ticks, time_steps):
    x_ticks_shown = x_ticks if time_steps <= 24 else np.arange(0, time_steps, 12)
    return x_ticks_shown


def set_figsize(time_steps):
    fig_size = (6.6, 5) if time_steps <= 24 else (15.4, 5)
    return fig_size

def path_to_el_usage_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_el_usage.png' % (building, tech))
    return path_to_file


def path_to_el_usages_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_el_usages.png' % (building, tech))
    return path_to_file


def path_to_water_flow_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_water.png' % (building, tech))
    return path_to_file


def path_to_heat_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_heat.png' % (building, tech))
    return path_to_file


def path_to_elec_csv(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_el.csv' % (building, tech))
    return path_to_file


if __name__ == '__main__':
    main()
