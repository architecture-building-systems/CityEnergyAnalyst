from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from cea.osmose import settings
from matplotlib import rc

rc('text', usetex=True)


def main(cases, building, path_to_save_results):
    # get occupancy from all cases
    WED_occupancy_dict = {}
    SAT_occupancy_dict = {}
    for case in cases:
        WED_occupancy_dict[case], SAT_occupancy_dict[case] = calc_occupancy(case, building)

    # table
    setpoint_df = setpoint_table()

    # plot
    plot_occupancy_and_setpoints(SAT_occupancy_dict, WED_occupancy_dict, building, path_to_save_results, setpoint_df)
    return np.nan


def plot_occupancy_and_setpoints(SAT_occupancy_dict, WED_occupancy_dict, building, path_to_save_results, setpoint_df):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharey=True, figsize=(10, 3.5))
    # plot WED
    ax1 = plot_occupancy(ax1, WED_occupancy_dict, 'Wednesday')
    ax1.set(ylabel='Occupancy [ppl/m2]')
    ax1.yaxis.label.set_size(10)
    # plot SAT
    ax2 = plot_occupancy(ax2, SAT_occupancy_dict, 'Saturday')
    ax2.legend(loc='upper right', ncol=3, fontsize='small', columnspacing=0.15)
    # plot table
    ax3.axis('off')
    table = ax3.table(cellText=setpoint_df.values,
                      colLabels=setpoint_df.columns, rowLabels=setpoint_df.index,
                      loc='center right', colWidths=[0.11] * 3)
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(2, 2)
    plt.tight_layout()
    #plt.show()
    filename = building + '_occupancy' + '.png'
    fig.savefig(os.path.join(path_to_save_results, filename))
    return np.nan


def setpoint_table():
    setpoint_df = pd.DataFrame()
    setpoint_df['Office'] = [24, 27]
    setpoint_df['Hotel'] = [24, 27]
    setpoint_df['Retail'] = [24, 24]
    setpoint_df = setpoint_df.set_index(pd.Index(['Tset-point [C]', 'Tset-back [C]']))
    return setpoint_df


def plot_occupancy(ax, occupancy_dict, day):
    CASE_TABLE = {'WTP_CBD_m_WP1_HOT': 'Hotel', 'WTP_CBD_m_WP1_OFF': 'Office', 'WTP_CBD_m_WP1_RET': 'Retail'}
    COLOR_TABLE = {'WTP_CBD_m_WP1_HOT': '#C96A50', 'WTP_CBD_m_WP1_OFF': '#3E9AA3', 'WTP_CBD_m_WP1_RET': '#51443D'}
    for case in occupancy_dict.keys():
        x = np.arange(1, occupancy_dict[case].values.size + 1, 1)
        y = occupancy_dict[case].values
        ax.plot(x, y, label=CASE_TABLE[case], color=COLOR_TABLE[case])
    ax.set(xlabel='Time [hr]')
    ax.xaxis.label.set_size(10)
    ax.set_title(day, fontdict={'fontsize': 10, 'fontweight': 'medium'})
    ax.set(xlim=(1, 24), ylim=(0, 0.17))
    for tick in ax.get_xticklabels():
        tick.set_fontname("Arial")
    for tick in ax.get_yticklabels():
        tick.set_fontname("Arial")
    return ax


def calc_occupancy(case, building):
    # read total demand
    total_demand_df = pd.read_csv(path_to_total_demand(case)).set_index('Name')
    tsd_df = pd.read_excel(path_to_demand_output(building, case)['xls'])
    # reduced_demand_df = demand_df[start_t:end_t]
    # WED
    start_t = 5136
    occupancy_WED = get_hourly_occupancy_in_a_day(start_t, building, total_demand_df, tsd_df)

    # SAT
    start_t = 5208
    occupancy_SAT = get_hourly_occupancy_in_a_day(start_t, building, total_demand_df, tsd_df)
    return occupancy_WED, occupancy_SAT


def latex_table(celldata,rowlabel,collabel):
    # function that creates latex-table
    table = r'\begin{table} \begin{tabular}{|1|'
    for c in range(0,len(collabel)):
        # add additional columns
        table += r'1|'
    table += r'} \hline'

    # provide the column headers
    for c in range(0,len(collabel)-1):
        table += collabel[c]
        table += r'&'
    table += collabel[-1]
    table += r'\\ \hline'

    # populate the table:
    # this assumes the format to be celldata[index of rows][index of columns]
    for r in range(0,len(rowlabel)):
        table += rowlabel[r]
        table += r'&'
        for c in range(0,len(collabel)-2):
            if not isinstance(celldata[r][c], basestring):
                table += str(celldata[r][c])
            else:
                table += celldata[r][c]
            table += r'&'

        if not isinstance(celldata[r][-1], basestring):
            table += str(celldata[r][-1])
        else:
            table += celldata[r][-1]
        table += r'\\ \hline'

    table += r'\end{tabular} \end{table}'

    return table


def get_hourly_occupancy_in_a_day(start_t, building, total_demand_df, tsd_df):
    end_t = start_t + 24
    reduced_tsd_df = tsd_df[start_t:end_t]
    hourly_people_df = reduced_tsd_df['people']
    GFA_m2 = total_demand_df.loc[building]['GFA_m2']
    hourly_ppl_per_m2 = hourly_people_df / GFA_m2
    return hourly_ppl_per_m2


def path_to_demand_output(building_name, case):
    path_to_file = {}
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    path_to_file['csv'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'csv'))
    path_to_file['xls'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'xls'))
    return path_to_file


def path_to_total_demand(case):
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    path_to_file = os.path.join(path_to_folder, 'Total_demand.%s' % ('csv'))
    return path_to_file


if __name__ == '__main__':
    cases = ['WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_RET']
    building = 'B006'
    path_to_save_results = settings.result_destination
    main(cases, building, path_to_save_results)
