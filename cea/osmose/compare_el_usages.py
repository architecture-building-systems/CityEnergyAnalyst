from __future__ import division
import numpy as np
import pandas as pd
import os
import operator
import matplotlib.pyplot as plt
import math
from cea.osmose.plot_osmose_result import path_to_elec_unit_csv, set_figsize, set_xtick_shown, path_to_save_fig

CASE_TABLE = {'HOT': 'Hotel', 'OFF': 'Office', 'RET': 'Retail'}
# CONFIG_TABLE = {'coil': 'OAU|1', 'ER0': 'OAU|2', '3for2': 'OAU|3', 'LD': 'OAU|4',
#                 'IEHX': 'OAU|5'}
CONFIG_TABLE = {'coil': 'Config|1', 'ER0': 'Config|2', '3for2': 'Config|3', 'LD': 'Config|4',
                'IEHX': 'Config|5'}


def main(building, building_result_path, case):
    # get paths to chiller_T_tech_df and el csv
    paths = path_to_elec_csv_files(building_result_path)
    chiller_paths = path_to_chiller_csv_files(building_result_path, 'chiller')
    chiller_Qc_paths = path_to_chiller_csv_files(building_result_path, 'chiller_Qc')

    el_dfs = {}
    cop_mean = {}
    hourly_cop_shr_dict = {}
    compare_df = pd.DataFrame()
    for path in paths:
        # get file
        file_name = path.split('\\')
        tech = [x for x in file_name if 'HCS' in x][0].split('_')[2]
        el_dfs[tech] = pd.read_csv(path)
        index = el_dfs[tech].shape[0] - 1
        # write compare_DF
        cop_mean[tech] = el_dfs[tech]['cop_system'].replace(0, np.nan).mean()
        compare_df[tech] = el_dfs[tech].ix[index][1:]
        #
        cop_shr_df = pd.DataFrame()
        cop_shr_df['COP'] = el_dfs[tech]['cop_system']
        cop_shr_df['SHR'] = el_dfs[tech]['sys_SHR']
        hourly_cop_shr_dict[tech] = cop_shr_df
    compare_df.to_csv(path_to_save_compare_df(building, building_result_path))

    # get chiller_T_tech_df from all tech
    # chiller_T_all_tech_df = get_chiller_T_from_all_techs(chiller_paths)
    # plot_chiller_temperatures_bar(chiller_T_all_tech_df, building, building_result_path)
    # plot_chiller_temperatures_scatter(chiller_T_all_tech_df, building, building_result_path, case)

    # get chiller_T_Qc_all_tech_df from all tech
    chiller_T_Qc_all_tech_df = get_chiller_T_from_all_techs(chiller_Qc_paths)
    tech_rank = get_tech_rank_by_el_total(compare_df)
    plot_chiller_T_Qc_scatter(chiller_T_Qc_all_tech_df, tech_rank, building, building_result_path, case)

    # plot electricity usages
    if index > 24:
        plot_el_compare(building, building_result_path, compare_df)
        plot_el_usages_by_unit(building, building_result_path)
    ## plot hourly COP vs SHR
    plot_COP_SHR_scatter(hourly_cop_shr_dict, building, case, building_result_path)

    return


def get_tech_rank_by_el_total(compare_df):
    el_total_all_tech_df = compare_df.T.filter(like='el_total')
    if 'status' in el_total_all_tech_df.index: el_total_all_tech_df.drop(index='status', inplace=True)
    if 'LD' in el_total_all_tech_df.index: el_total_all_tech_df.drop(index='LD', inplace=True)
    tech_rank = el_total_all_tech_df.sort_values(by='el_total').index
    return tech_rank

def plot_T_w_scatter(ax, compare_df):
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    color_codes = {'3for2': '#C96A50', 'coil': '#3E9AA3', 'ER0': '#E2B43F', 'IEHX': '#51443D', 'LD': '#6245A3'}
    # anno_colors = tuple(map(lambda i: color_codes[i], anno))
    tech_list = ['coil', 'ER0', '3for2', 'LD', 'IEHX']
    for tech in tech_list:
        if tech in compare_df.columns:  # otherwise, don't plot
            T_SA = compare_df[tech]['T_SA']
            w_SA = compare_df[tech]['w_SA']
            label = CONFIG_TABLE[tech]
            color = color_codes[tech]
            ax.scatter(w_SA, T_SA, s=70, c=color, label=label)
    ax.legend(loc="lower left", ncol=3, bbox_to_anchor=(-0.05, 0.7), fontsize='small', columnspacing=0.05)
    ax.set(xlabel='Humidity Ratio [g/kg air]', ylabel='Temperature [C]', ylim=(14, 20))
    ax.set_title('OAU Supply Air Conditions ')
    # plt.show()
    return np.nan


def plot_COP_SHR_scatter(hourly_cop_shr_dict, building, case, building_result_path):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    color_codes = {'3for2': '#C96A50', 'coil': '#3E9AA3', 'ER0': '#E2B43F', 'IEHX': '#51443D', 'LD': '#6245A3'}
    for tech in hourly_cop_shr_dict.keys():
        if 'status' not in tech:
            COP = hourly_cop_shr_dict[tech]['COP']
            SHR = hourly_cop_shr_dict[tech]['SHR']
            color = color_codes[tech]
            ax.scatter(SHR, COP, c=color)
    ax.set(xlabel='SHR', ylabel='COP', ylim=(3, 9), xlim=(0, 1))
    ax.set_title(building + '_' + case.split('_')[4] + '_' + case.split('_')[0], fontsize=16)
    fig.savefig(path_to_save_cop_shr_scatter(building, building_result_path))
    # plt.show()
    return


def get_chiller_T_from_all_techs(chiller_paths):
    i = 0
    for path in chiller_paths:
        if i == 0:
            chiller_T_all_tech_df = pd.read_csv(path)
            chiller_T_all_tech_df = chiller_T_all_tech_df.set_index(chiller_T_all_tech_df.columns[0])
            i = i + 1
        else:
            chiller_T_tech_df = pd.read_csv(path)
            chiller_T_tech_df = chiller_T_tech_df.set_index(chiller_T_tech_df.columns[0])
            chiller_T_all_tech_df = chiller_T_all_tech_df.append(chiller_T_tech_df)
    float_columns = [float(x) for x in chiller_T_all_tech_df.columns]
    float_columns.sort()
    string_columns = [str(x) for x in float_columns]
    chiller_T_all_tech_df = chiller_T_all_tech_df.reindex(string_columns, axis=1)
    chiller_T_all_tech_df = chiller_T_all_tech_df.fillna(0)
    return chiller_T_all_tech_df


def plot_chiller_temperatures_bar(chiller_df, building, building_result_path):
    X = np.arange(chiller_df.columns.size)
    fig, ax = plt.subplots()
    width = 0.00
    # colors = {'HCS_3for2': '#C97A64', 'HCS_coil': '#4E9DA3', 'HCS_ER0': '#E2BB56', 'HCS_IEHX': '#889164'}
    colors = {'HCS_3for2': '#C96A50', 'HCS_coil': '#3E9AA3', 'HCS_ER0': '#E2B43F', 'HCS_IEHX': '#51443D'}
    for i in range(chiller_df.index.size):
        color = colors[chiller_df.index[i]]
        ax.bar(X + width, chiller_df.loc[chiller_df.index[i]][:], width=0.15, label=chiller_df.index[i], color=color)
        width = width + 0.15
    # ax.bar(X + 0.25, chiller_df.loc[chiller_df.index[1]][:], width=0.25, label=chiller_df.index[1])
    ax.legend(loc='upper right')
    ax.set_xticks(X + width / 2)
    ax.set_xticklabels(tuple(chiller_df.columns))
    # ax.set_xticks(chiller_df.columns)
    ax.set(xlabel='Temperature [C]', ylabel='Frequency [%]', ylim=(0, 100))
    # plt.show()
    fig.savefig(path_to_save_chiller_t(building, building_result_path))
    return ax


def plot_chiller_temperatures_scatter(chiller_df, building, building_result_path, case):
    chiller_dict = chiller_df.T.to_dict()

    # sort two level dict with the value of key in second level
    sorted_dict = sort_dict_with_second_level_key(chiller_dict)

    # x axis (keys of the first level dict)
    chiller_dict_keys = list(chiller_dict.keys())
    x_labels = []
    for i in ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD', 'HCS_IEHX']:
        if i in chiller_dict_keys:
            x_labels.append(i)
    x_labels_shown = []
    label_dict = {'HCS_coil': 'Config|1', 'HCS_ER0': 'Config|2', 'HCS_3for2': 'Config|3', 'HCS_LD': 'Config|4',
                  'HCS_IEHX': 'Config|5'}
    for i in x_labels:
        x_labels_shown.append(label_dict[i])
    x_values = list(range(len(x_labels)))
    # lookup table mapping category
    lookup_table = dict((v, k) for k, v in enumerate(x_labels))  # determine the x-axis order
    # build a list of points (x,y,annotation)
    points = [(lookup_table[action], key, anno)
              for action, values in chiller_dict.items()
              for key, anno in (values if values else {}).items()]
    x, y, anno = zip(*points)
    y_float = tuple(map(lambda i: float(i), y))
    # y axis (keys of the second level dict)
    y_values = [8.1, 8.75, 9.4, 10.05, 10.7, 11.35, 12., 12.65, 13.3, 13.95]
    # y_values = [float(i) for i in chiller_df.columns]
    y_labels = [str(v) for v in y_values]
    # marker size
    area = tuple(map(lambda x: 10 * x, anno))

    # figure name
    figure_name = 'chw_freq'

    format_chw_scatter_plot(area, building, building_result_path, case, figure_name, x, x_labels_shown, x_values,
                            y_float, y_labels, y_values)
    return np.nan


def plot_chiller_T_Qc_scatter(chiller_df, tech_rank, building, building_result_path, case):
    chiller_dict = chiller_df.T.to_dict()

    # x axis (keys of the first level dict)
    chiller_dict_keys = list(chiller_dict.keys())
    x_labels = []
    # for i in ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD', 'HCS_IEHX']:
    #     if i in chiller_dict_keys:
    #         x_labels.append(i)
    for i in tech_rank:
        x_labels.append('HCS_' + i)
    x_labels_shown = []
    label_dict = {'HCS_coil': 'Config|1', 'HCS_ER0': 'Config|2', 'HCS_3for2': 'Config|3', 'HCS_LD': 'Config|4',
                  'HCS_IEHX': 'Config|5'}
    for i in x_labels:
        x_labels_shown.append(label_dict[i])
    x_values = list(range(len(x_labels)))

    # lookup table mapping category, assign ranking to x labels
    ranking_lookup_table = dict((v, k) for k, v in enumerate(x_labels))  # determine the x-axis order

    # build a list of points (x,y,annotation)
    points_list = [(ranking_lookup_table[tech], key_T, anno_Qc)
              for tech, T_Qc_dict in chiller_dict.items()
              for key_T, anno_Qc in (T_Qc_dict if T_Qc_dict else {}).items()]
    x, y, anno_Qc = zip(*points_list)
    y_float = tuple(map(lambda i: float(i), y))
    # y axis (keys of the second level dict)
    y_values = [8.1, 8.75, 9.4, 10.05, 10.7, 11.35, 12., 12.65, 13.3, 13.95]
    # y_values = [float(i) for i in chiller_df.columns]
    y_labels = [str(v) for v in y_values]
    # marker size
    area = tuple(map(lambda x: (x / 1000) ** 2, anno_Qc))  # area = Qc

    # figure name
    figure_name = 'chw_Qc'

    format_chw_scatter_plot(area, building, building_result_path, case, figure_name, x, x_labels_shown, x_values,
                            y_float, y_labels, y_values)
    return np.nan


def format_chw_scatter_plot(area, building, building_result_path, case, figure_name, x, x_labels_shown, x_values,
                            y_float, y_labels, y_values):
    # format the plt
    plt.figure()
    case_name = case.split('_')[4]
    plt.title(case.split('_')[0] + ' ' + CASE_TABLE[case_name] + ' ' + building, fontsize=16)
    # plt.xlabel('x')
    plt.xticks(x_values, x_labels_shown, fontsize=16)
    plt.yticks(y_values, y_labels, fontsize=16)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.5, max(y_values) + 0.5])
    plt.scatter(x, y_float, s=area, c='#454545')  # navy: #14453
    plt.ylabel('Chilled water temperature [C]', fontsize=16)
    # plt.show()
    plt.savefig(path_to_save_chw_scatter(building, building_result_path, figure_name))


def plot_el_compare(building, building_result_path, compare_df):
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(9.5, 5))

    # ax1.set_visible(False)
    ax1 = plot_T_w_scatter(ax1, compare_df)

    # ax2
    config = 'Config|1 \n Cooling Coils'
    tech = 'HCS_coil'
    if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
        el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
        el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
        ax2 = plot_electricity_usages_units(ax2, el_per_unit_df, config)
        ax2.set(ylabel='Electricity Use [Wh/m2]')
        ax2.yaxis.label.set_size(10)
    # ax3
    config = 'Config|2 \n Direct Evaporative Cooling'
    tech = 'HCS_ER0'
    if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
        el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
        el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
        ax3 = plot_electricity_usages_units(ax3, el_per_unit_df, config)
        # ax3.legend(loc=(0.2,-0.35), ncol=3, fontsize='small', columnspacing=0.1)
    # ax4
    config = 'Config|3 \n Desiccant Wheels'
    tech = 'HCS_3for2'
    if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
        el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
        el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
        ax4 = plot_electricity_usages_units(ax4, el_per_unit_df, config)
        ax4.set(ylabel='Electricity Use [Wh/m2]')
        ax4.yaxis.label.set_size(10)
        ax4.set(xlabel='Time [hr]')
        ax4.xaxis.label.set_size(10)
    # ax5
    config = 'Config|4 \n Liquid Desiccant'
    tech = 'HCS_LD'
    if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
        el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
        el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
        ax5 = plot_electricity_usages_units(ax5, el_per_unit_df, config)
        ax5.set(xlabel='Time [hr]')
        ax5.xaxis.label.set_size(10)
        ax5.legend(loc="upper center", ncol=3, fontsize='small', columnspacing=0.15)
    # ax6
    config = 'Config|5 \n Indirect Evaporative Cooling'
    tech = 'HCS_IEHX'
    if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
        el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
        el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
        ax6 = plot_electricity_usages_units(ax6, el_per_unit_df, config)
        ax6.set(xlabel='Time [hr]')
        ax6.xaxis.label.set_size(10)

    # plot layout
    filename = 'el_usages_compare_' + 'WED'
    # plt.legend()
    plt.tight_layout()
    # plt.show()
    fig.savefig(path_to_save_fig(building, building_result_path, tech, filename))
    return np.nan


def plot_el_usages_by_unit(building, building_result_path):

    TECH_TABLE = {'HCS_coil':'Config|1 Cooling Coils',
                  'HCS_ER0': 'Config|2 Direct Evaporative Cooling',
                  'HCS_3for2':'Config|3 Desiccant Wheels',
                  'HCS_LD': 'Config|4 Liquid Desiccant',
                  'HCS_IEHX': 'Config|5 Indirect Evaporative Cooling'}

    for tech in TECH_TABLE.keys():
        config_name = building + '\n' + TECH_TABLE[tech]
        if os.path.isfile(path_to_elec_unit_csv(building, building_result_path, tech)):
            fig, ax = plt.subplots()
            el_per_unit_df = pd.read_csv(path_to_elec_unit_csv(building, building_result_path, tech))
            el_per_unit_df = el_per_unit_df.iloc[72:96]  # WED
            ax = plot_electricity_usages_units(ax, el_per_unit_df, config_name)
            ax.xaxis.set_tick_params(labelsize=16)
            ax.yaxis.set_tick_params(labelsize=16)
            ax.set(ylabel='Electricity Use [Wh/m2]', xlabel='Time [hr]')
            ax.yaxis.label.set_size(16)
            ax.xaxis.label.set_size(16)
            ax.legend(loc="upper center", ncol=3, fontsize='large', columnspacing=0.15)

            ax.set_title(config_name, fontdict={'fontsize': 16})
            # plot layout
            filename = 'el_usages_' + 'WED'
            # plt.legend()
            plt.tight_layout()
            # plt.show()
            fig.savefig(path_to_save_fig(building, building_result_path, tech, filename))
    return np.nan


def plot_electricity_usages_units(ax, el_per_unit_df, config):
    el_per_unit_df = el_per_unit_df.set_index(pd.Series(range(1, 25, 1)))
    x_ticks = el_per_unit_df.index.values
    # plotting
    bar_width = 0.5
    opacity = 1
    # color_table = {'OAU': '#14453D', 'LCU': '#4D9169', 'SCU': '#BACCCC'}
    # color_table = {'OAU': '#171717', 'RAU': '#454545', 'SCU': '#737373'}
    color_table = {'OAU': '#080808', 'RAU': '#707070', 'SCU': '#C8C8C8'}  # Gray scale
    # initialize the vertical-offset for the stacked bar chart
    y_offset = np.zeros(el_per_unit_df.shape[0])
    # plot bars
    unit_table = {'OAU': 'el_oau', 'RAU': 'el_lcu', 'SCU': 'el_scu'}
    for unit in ['OAU','RAU','SCU']:
        column = unit_table[unit]
        ax.bar(x_ticks, el_per_unit_df[column], bar_width, bottom=y_offset, alpha=opacity, color=color_table[unit],
               label=unit)
        y_offset = y_offset + el_per_unit_df[column]
    ax.set(xlim=(1, 24), ylim=(0, 25))
    ax.set_xticks(range(1, 25, 4))
    # ax.legend(loc='upper left')
    ax.set_title(config)
    return ax


def sort_dict_with_second_level_key(two_level_dict):
    dict_sorted_with_second_level_key = {}
    for k, v in two_level_dict.items():
        new_sub_dict = {}
        for i, j in v.items():
            new_sub_dict[float(i)] = j
        new_sub_dict_sorted = sorted(new_sub_dict.items(), key=operator.itemgetter(0))
        dict_sorted_with_second_level_key[k] = new_sub_dict_sorted
    return dict_sorted_with_second_level_key


def path_to_elec_csv_files(building_result_path):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    # path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(building_result_path)
    path_to_files = []
    file_name = 'el.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(building_result_path, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_chiller_csv_files(building_result_path, name):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    # path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(building_result_path)
    path_to_files = []
    file_name = name + '.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(building_result_path, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_save_compare_df(building, building_result_path):
    filename = building + '_el_compare.csv'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


def path_to_save_chiller_t(building, building_result_path):
    filename = building + '_chiller.png'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


def path_to_save_chw_scatter(building, building_result_path, name):
    filename = building + '_' + name + '.png'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


def path_to_save_cop_shr_scatter(building, building_result_path):
    filename = building + '_shr_cop_scatter.png'
    path_to_file = os.path.join(building_result_path, filename)
    return path_to_file


if __name__ == '__main__':
    # buildings = ["B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009", "B010"]
    buildings = ["B004", "B005", "B006"]
    timestep = "168"
    cases = ['WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_RET']
    # cases = ["HKG_CBD_m_WP1_RET", "HKG_CBD_m_WP1_OFF", "HKG_CBD_m_WP1_HOT",
    #          "ABU_CBD_m_WP1_RET", "ABU_CBD_m_WP1_OFF", "ABU_CBD_m_WP1_HOT",
    #          "MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT",
    #          "WTP_CBD_m_WP1_RET", "WTP_CBD_m_WP1_OFF", "WTP_CBD_m_WP1_HOT"]
    # cases = ["HKG_CBD_m_WP1_RET", "HKG_CBD_m_WP1_OFF", "HKG_CBD_m_WP1_HOT"]
    # cases = ["ABU_CBD_m_WP1_RET", "ABU_CBD_m_WP1_OFF", "ABU_CBD_m_WP1_HOT"]
    # cases = ["MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT"]
    # cases = ['WTP_CBD_m_WP1_OFF']
    result_folder = 'C:\\Users\\Shanshan\\Documents\\WP1_results_0717'
    # result_folder = "C:\\Users\\Shanshan\\Documents\\WP1_results"
    for case in cases:
        print case
        case_folder = os.path.join(result_folder, case)
        for building in buildings:
            building_result_path = os.path.join(case_folder, building + "_" + timestep)
            # building_result_path = os.path.join(building_result_path, 'reduced') #FIXME
            if os.path.isdir(building_result_path):
                main(building, building_result_path, case)
                print building
            else:
                'cannot find ', building_result_path
