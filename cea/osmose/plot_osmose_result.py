from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2']
# TECHS = ['HCS_3for2']
Af_m2 = {'B001': 28495.062, 'B002': 28036.581, 'B007': 30743.113}


def main():
    el_use_sum = {}
    for tech in TECHS:
        building = 'B007'
        results = pd.read_csv(path_to_osmose_results(building, tech)).T.reset_index()
        results = results.rename(columns=results.iloc[0])[1:]
        el_use_sum[tech] = results['SU_elec'].sum()

        # calculate total electricity usage

        ## calculate T_SA, w_SA
        operation_df = pd.DataFrame()
        # output actual temperature
        results.ix[results.m_oau_in_1 <= 0.01, 'OAU_T_SA1'] = 0
        results.ix[results.m_oau_in_2 <= 0.01, 'OAU_T_SA2'] = 0
        results.ix[results.m_oau_in_3 <= 0.01, 'OAU_T_SA3'] = 0
        operation_df['T_SA'] = results.apply(lambda row: row.OAU_T_SA1 + row.OAU_T_SA2 + row.OAU_T_SA3, axis=1)
        results.ix[results.m_oau_in_1 <= 0.01, 'OAU_w_SA1'] = 0
        results.ix[results.m_oau_in_2 <= 0.01, 'OAU_w_SA2'] = 0
        results.ix[results.m_oau_in_3 <= 0.01, 'OAU_w_SA3'] = 0
        operation_df['w_SA'] = results.apply(lambda row: row.OAU_w_SA1 + row.OAU_w_SA2 + row.OAU_w_SA3, axis=1)
        # plot
        fig, ax = plt.subplots()
        x_ticks = operation_df.index.values
        line1, = ax.plot(x_ticks, operation_df['T_SA'], '-o', linewidth=2,
                         label='T,supply,OAU')
        line2, = ax.plot(x_ticks, operation_df['w_SA'], '-o', label='w,supply,OAU')

        ax.legend(loc='lower right')
        ax.set_xticks(x_ticks)
        ax.grid(True)
        plt.xlim(1, 24)
        plt.ylim(0, 25)
        plt.xlabel('Time [hr]')
        plt.ylabel('Temperature [C] ; Humidity Ratio [g/kg d.a.]')
        # plt.show()
        fig.savefig(path_to_OAU_supply_fig(building, tech))
        plt.close(fig)

        ## electricity usage
        results['el_per_Af'] = results['SU_elec'] * 1000 / Af_m2[building]
        fig, ax = plt.subplots()
        ax.plot(x_ticks, results['el_per_Af'], '-o', label='el_used')
        ax.legend(loc='lower right')
        ax.set(xlabel='Time [hr]', ylabel='Electricity Usage [Wh/m2]', xlim=(1, 24), ylim=(0, 30))
        ax.set_xticks(x_ticks)
        ax.grid(True)
        fig.savefig(path_to_el_usage_fig(building, tech))
        # plt.show()

        ## humidity
        humidity_df = pd.DataFrame()
        # humidity_df['m_w_infil_occupant'] = results['w_bui']
        humidity_df['m_w_lcu_removed'] = results['w_lcu']
        total_oau_removed = results['w_oau_out'] - (
                results['w_oau_in_1'] + results['w_oau_in_2'] + results['w_oau_in_3'])
        total_oau_removed[total_oau_removed < 0] = 0
        humidity_df['m_w_oau_removed'] = total_oau_removed
        humidity_df['m_w_stored'] = results['w_sto_charge']
        # humidity_df['m_w_discharged'] = results['w_sto_discharge']

        fig, ax = plt.subplots()
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
        ax.set(xlabel='Time [hr]', ylabel='Water flow [kg/s]', xlim=(1, 24), ylim=(0, 0.3))
        ax.legend(loc='upper left')
        # plot line
        ax1 = ax.twinx()
        w_bui_float = pd.to_numeric(results['w_bui'])
        ax1.plot(x_ticks, w_bui_float, '-o', label='water gain')
        ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
        ax.legend(loc='upper right')

        # plot layout

        fig.savefig(path_to_water_flow_fig(building, tech))
        # plt.show()

        ## heat
        heat_df = pd.DataFrame()
        # humidity_df['m_w_infil_occupant'] = results['w_bui']
        heat_df['q_lcu_sen'] = results['q_lcu_sen']
        total_oau_removed = results['q_oau_sen_out'] - (
                results['q_oau_sen_in_1'] + results['q_oau_sen_in_2'] + results['q_oau_sen_in_3'])
        # q_bui_float = pd.to_numeric(results['q_bui']) + 0.01
        # total_oau_removed[total_oau_removed > q_bui_float] = 0
        heat_df['q_oau_sen'] = total_oau_removed
        heat_df['q_scu_sen'] = results['q_scu_sen']

        fig, ax = plt.subplots()
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
        ax.set(xlabel='Time [hr]', ylabel='Sensible heat [kWh]', xlim=(1, 24), ylim=(0, 2000))
        ax.legend(loc='upper left')
        # plot line
        ax1 = ax.twinx()
        q_bui_float = pd.to_numeric(results['q_bui'])
        ax1.plot(x_ticks, q_bui_float, '-o', label='sensible heat gain')
        ax1.set(xlim=ax.get_xlim(), ylim=ax.get_ylim())
        ax1.legend(loc='upper right')
        # plot layout
        fig.savefig(path_to_heat_fig(building, tech))
        # plt.show()

        # ## heat usage
        # fig, ax = plt.subplots()
        # q_bui_float = pd.to_numeric(results['q_bui'])
        # ax.plot(x_ticks, q_bui_float, '-o', label='q_bui')
        # ax.legend(loc='lower right')
        # ax.set(xlabel='Time [hr]', ylabel='Electricity Usage [Wh/m2]', xlim=(1, 24))
        # ax.set_xticks(x_ticks)
        # ax.grid(True)
        # fig.savefig(path_to_el_usage_fig(building, tech))
        # # plt.show()

    print el_use_sum
    return


def path_to_osmose_results(building, tech):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_outputs.%s' % (tech, format))
    return path_to_file


def path_to_OAU_supply_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_OAU_supply.png' % (building, tech))
    return path_to_file


def path_to_el_usage_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_el_usage.png' % (building, tech))
    return path_to_file


def path_to_water_flow_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_water.png' % (building, tech))
    return path_to_file


def path_to_heat_fig(building, tech):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, '%s_%s_heat.png' % (building, tech))
    return path_to_file


if __name__ == '__main__':
    main()
