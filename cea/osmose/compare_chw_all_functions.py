from __future__ import division
import numpy as np
import pandas as pd
import os
import operator
import matplotlib.pyplot as plt
from cea.osmose.compare_el_usages import path_to_elec_csv_files

label_dict = {'HCS_coil': 'Config|1', 'HCS_ER0': 'Config|2', 'HCS_3for2': 'Config|3', 'HCS_IEHX': 'Config|5'}

def main(path_result_folder, building, techs, time_steps, cases):

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharey=True, figsize=(12.5, 3))
    ax1 = plot_tech(ax1, techs[0], building, cases, path_result_folder, time_steps)
    ax1.set(ylabel='Water Temperature [C]')
    ax1.yaxis.label.set_size(14)
    ax2 = plot_tech(ax2, techs[1], building, cases, path_result_folder, time_steps)
    ax3 = plot_tech(ax3, techs[2], building, cases, path_result_folder, time_steps)
    ax4 = plot_tech(ax4, techs[3], building, cases, path_result_folder, time_steps)
    ax4.legend(loc="lower right", bbox_to_anchor=(1.5, 0),fontsize=12, columnspacing=0, frameon=False)

    plt.tight_layout()
    #plt.show()
    fig.savefig(os.path.join(path_result_folder,building))

    return np.nan


def plot_tech(ax, tech, building, cases, path_result_folder, time_steps):
    T_chw = {}
    for case in cases:
        path_to_file = path_to_elec_csv_files(building, tech, case, path_result_folder, time_steps)
        T_chw[case] = pd.read_csv(path_to_file)['T_chw'][72:96].fillna(0)
    CASE_TABLE = {'WTP_CBD_m_WP1_HOT': 'Hotel', 'WTP_CBD_m_WP1_OFF': 'Office', 'WTP_CBD_m_WP1_RET': 'Retail'}
    COLOR_TABLE = {'WTP_CBD_m_WP1_HOT': '#C96A50', 'WTP_CBD_m_WP1_OFF': '#3E9AA3', 'WTP_CBD_m_WP1_RET': '#51443D'}
    marker_table = {'WTP_CBD_m_WP1_HOT': "o", 'WTP_CBD_m_WP1_OFF': "x", 'WTP_CBD_m_WP1_RET': "+"}
    for key in T_chw.keys():
        x = np.arange(1, 25, 1)
        y = T_chw[key]
        # ax.plot(x,y)
        ax.scatter(x, y, marker=marker_table[key], c=COLOR_TABLE[key], label=CASE_TABLE[key])
    ax.set(xlabel='Time [hr]', xlim=(1, 24), ylim=(8, 14))
    ax.xaxis.label.set_size(14)
    # ax.legend(ncol=3, loc='lower right')

    ax.set_title(label_dict[tech], fontdict={'fontsize': 14, 'fontweight': 'medium'})
    return ax


def path_to_elec_csv_files(building, tech, case, path_result_folder, time_steps):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    path_to_case_folder = os.path.join(path_result_folder, case)
    building_folder_name = building + '_' + str(time_steps)
    path_to_building_folder = os.path.join(path_to_case_folder, building_folder_name)
    file_name = building + '_' + tech + '_el.csv'
    path_to_file = os.path.join(path_to_building_folder, file_name)
    return path_to_file


if __name__ == '__main__':
    cases = ['WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_RET']
    buildings = ['B005']
    techs = ['HCS_coil','HCS_ER0','HCS_3for2','HCS_IEHX']
    path_result_folder = "C:\\Users\\Shanshan\\Documents\\WP1_workstation"
    time_steps = 168
    for building in buildings:
        main(path_result_folder, building, techs, time_steps, cases)
