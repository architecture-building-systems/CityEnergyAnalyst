from __future__ import division
import numpy as np
import pandas as pd
import os
import operator
import matplotlib.pyplot as plt

CASE_TABLE = {'HOT': 'Hotel', 'OFF': 'Office', 'RET': 'Retail'}
COLOR_CODES = {'3for2': '#C96A50', 'coil': '#3E9AA3', 'ER0': '#E2B43F', 'IEHX': '#51443D', 'LD': '#6245A3',
               'status': '#707070'}


def main(path_result_folder, case, time_steps):
    path_district_result_folder = os.path.join(path_result_folder, case)
    el_compare_paths = path_to_el_compare_files(path_district_result_folder, time_steps)
    # iterate through files and combine results
    all_results_dict = {}
    all_el_total_dict = {}
    all_cop_dict = {}
    all_exergy_eff_dict = {}
    for path in el_compare_paths:
        building = path.split('\\')[6].split('_')[0]
        print(building)
        el_compare_df = pd.read_csv(path, index_col=0)
        #
        Af_m2 = el_compare_df.loc['el_Wh_total_per_Af'] / (el_compare_df.loc['el_total'] / 1000)
        el_compare_df.loc['qc_load_Wh_per_Af'] = el_compare_df.loc['qc_load_total'] / Af_m2
        list_of_labels = []
        for label in ['cop_system', 'el_total', 'qc_sys_total', 'cop_system_mean',
                      'eff_exergy', 'Qh', 'cop_Qh', 'el_Wh_total_per_Af', 'qc_load_Wh_per_Af',
                      'qc_Wh_sys_per_Af', 'process_exergy_Wh_per_Af', 'utility_exergy_Wh_per_Af',
                      'eff_process_utility']:
            list_of_labels.append(el_compare_df.loc[label])
        building_result_df = pd.concat(list_of_labels, axis=1)
        building_result_df = building_result_df.sort_values(by=['el_total']).T
        all_results_dict[building] = building_result_df

        all_el_total_dict[building] = el_compare_df.loc['el_Wh_total_per_Af'].to_dict()
        all_cop_dict[building] = el_compare_df.loc['cop_system_mean'].to_dict()  # FIXME
        all_exergy_eff_dict[building] = (el_compare_df.loc['eff_exergy'] * 100).to_dict()

        ## write qc all tech to one dict
        qc_all_tech_per_building_dict = {}
        ## change order of columns
        # new_column_list = []
        # for tech in ['coil', 'ER0', '3for2', 'LD', 'IEHX']:
        #     if tech in el_compare_df.columns:
        #         new_column_list.append(tech)
        new_column_list = el_compare_df.loc['el_total'].sort_values(ascending=True).index
        ordered_el_compare_df = el_compare_df[new_column_list]
        # qc_sys
        qc_sys_total = ordered_el_compare_df.loc['qc_sys_total']
        for label in ['qc_sys_scu', 'qc_sys_lcu', 'qc_sys_oau']:
            qc_sys_scu_percent = ordered_el_compare_df.loc[label] / qc_sys_total
            qc_all_tech_per_building_dict[label] = qc_sys_scu_percent
        # plot qc box plot
        techs = ordered_el_compare_df.columns
        plot_stacked_bar(building, time_steps, techs, qc_all_tech_per_building_dict, path_district_result_folder, case)

        # ex_Wh_per_Af
        ex_all_tech_per_building_dict = {}
        for label in ['process_exergy_Wh_per_Af', 'utility_exergy_Wh_per_Af', 'el_Wh_total_per_Af']:
            ex_all_tech_per_building_dict[label] = ordered_el_compare_df.loc[label]
        techs = ordered_el_compare_df.columns
        plot_overlapping_bar(building, time_steps, techs, ex_all_tech_per_building_dict, path_district_result_folder, case)

    all_results_df = pd.concat(all_results_dict).round(2)
    all_results_df.to_csv(path_to_save_all_dirstrict_df(case, path_district_result_folder))

    # scatter plot of COP
    plot_scatter_COP(all_cop_dict, all_el_total_dict, path_district_result_folder)

    # scatter plot of exergy eff
    plot_scatter_EX(all_exergy_eff_dict, path_district_result_folder)

    return np.nan


def plot_stacked_bar(building, time_steps, techs, qc_all_tech_per_building_dict, path_district_result_folder, case):
    # plotting
    fig, ax = plt.subplots()
    bar_width = 0.5
    opacity = 1
    # initialize the vertical-offset for the stacked bar chart
    number_of_columns = len(techs)
    y_offset = np.zeros(number_of_columns)
    # plot bars
    x_ticks = range(len(techs))
    # set colors
    # COLOR_TABLE = {'OAU': '#14453D', 'RAU': '#4D9169', 'SCU': '#BACCCC'}  # # OLIVE, GRASS, GREY
    # COLOR_TABLE = {'OAU': '#171717', 'RAU': '#454545', 'SCU': '#737373'} # Grey scale
    COLOR_TABLE = {'OAU': '#080808', 'RAU': '#707070', 'SCU': '#C8C8C8'}  # Gray scale
    i = 0
    KEY_TABLE = {'qc_sys_oau': 'OAU', 'qc_sys_scu': 'SCU', 'qc_sys_lcu': 'RAU'}
    for key in qc_all_tech_per_building_dict.keys():
        stack_label = KEY_TABLE[key]
        x_values = x_ticks
        bar_values = qc_all_tech_per_building_dict[key]
        ax.bar(x_values, bar_values, bar_width, bottom=y_offset, alpha=opacity, color=COLOR_TABLE[stack_label],
               label=stack_label)
        y_offset = y_offset + qc_all_tech_per_building_dict[key]
        i = i + 1
    ax.set(ylabel='% of heat removed', xlim=(-0.5, 4.5), ylim=(0, 1))
    label_dict = {'coil': 'Config|1', 'ER0': 'Config|2', '3for2': 'Config|3', 'LD': 'Config|4', 'IEHX': 'Config|5'}
    x_tick_shown = [0]
    for tech in techs:
        x_tick_shown.append(label_dict[tech])
    ax.set_xticklabels(x_tick_shown)
    # ax.set_xticklabels(np.append(([0]), label_dict[techs.values]), fontsize=18)
    ax.xaxis.label.set_size(16)
    ax.yaxis.label.set_size(16)
    ax.xaxis.set_tick_params(labelsize=14)
    ax.yaxis.set_tick_params(labelsize=14)
    ax.legend(loc='lower right', fontsize=16)
    case_name = case.split('_')[4]
    title = CASE_TABLE[case_name] + ' ' + building
    ax.set_title(title, fontsize=16)

    # plt.show()
    # plot layout
    filename = building + '_total_heat_supplied.png'
    fig.savefig(path_to_save_building_fig(filename, building, time_steps, path_district_result_folder))

    return np.nan


def plot_overlapping_bar(building, time_steps, techs, ex_all_tech_per_building_dict, path_district_result_folder, case):
    # plotting
    fig, ax = plt.subplots()
    bar_width = 0.5
    opacity = 1
    # initialize the vertical-offset for the stacked bar chart
    number_of_columns = len(techs)
    # plot bars
    x_ticks = range(len(techs))
    # set colors
    # COLOR_TABLE = {'OAU': '#14453D', 'RAU': '#4D9169', 'SCU': '#BACCCC'}  # # OLIVE, GRASS, GREY
    # COLOR_TABLE = {'OAU': '#171717', 'RAU': '#454545', 'SCU': '#737373'} # Grey scale
    COLOR_TABLE = {'process_exergy_Wh_per_Af': '#080808', 'utility_exergy_Wh_per_Af': '#707070', 'el_Wh_total_per_Af': '#C8C8C8'}  # Gray scale
    i = 0
    KEY_TABLE = {'process_exergy_Wh_per_Af': 'process exergy', 'utility_exergy_Wh_per_Af': 'utility exergy', 'el_Wh_total_per_Af': 'electricity'}
    for key in ['el_Wh_total_per_Af', 'utility_exergy_Wh_per_Af', 'process_exergy_Wh_per_Af']:
        stack_label = KEY_TABLE[key]
        x_values = x_ticks
        bar_values = ex_all_tech_per_building_dict[key]/1000 #to kWh
        ax.bar(x_values, bar_values, bar_width, alpha=opacity, color=COLOR_TABLE[key], label=stack_label)
        i = i + 1
    ax.set(ylabel='Energy [kWh/m2]', xlim=(-0.5, 4.5), ylim=(0, 2))
    label_dict = {'coil': 'Config|1', 'ER0': 'Config|2', '3for2': 'Config|3', 'LD': 'Config|4', 'IEHX': 'Config|5'}
    x_tick_shown = [0]
    for tech in techs:
        x_tick_shown.append(label_dict[tech])
    ax.set_xticklabels(x_tick_shown)
    # ax.set_xticklabels(np.append(([0]), label_dict[techs.values]), fontsize=18)
    ax.xaxis.label.set_size(16)
    ax.yaxis.label.set_size(16)
    ax.xaxis.set_tick_params(labelsize=14)
    ax.yaxis.set_tick_params(labelsize=14)
    ax.legend(loc='upper right', fontsize=12, ncol=3, mode="expand")
    case_name = case.split('_')[4]
    title = CASE_TABLE[case_name] + ' ' + building
    ax.set_title(title, fontsize=16)

    # plt.show()
    # plot layout
    filename = building + '_total_exergy_supplied.png'
    fig.savefig(path_to_save_building_fig(filename, building, time_steps, path_district_result_folder))

    return np.nan


def plot_scatter_COP(all_cop_dict, all_el_total_dict, path_district_result_folder):
    # get all the points
    building_lookup_key, tech_key, value = get_all_points_from_dict(all_cop_dict)

    # x axis
    x = building_lookup_key
    x_labels = list(all_cop_dict.keys())
    x_labels.sort()
    x_values = list(range(len(x_labels)))
    # y axis
    y = value
    # y_values = np.arange(round(min(y)),round(max(y))+2)
    y_values = np.arange(4, 8)
    y_minor_values = y_values + 0.5
    y_labels = [str(v) for v in y_values]
    # marker size
    anno = tech_key
    el_tot_list = []
    for i in range(len(anno)):
        building = x_labels[building_lookup_key[i]]
        tech = anno[i]
        #area = (all_el_total_dict[building][tech]/500)**2 # qc_load_Wh_per_Af
        area = (all_el_total_dict[building][tech] / 110) ** 2  # el_Wh_total_per_Af
        #area = (all_el_total_dict[building][tech] / 600) ** 2  # qc_Wh_sys_per_Af
        el_tot_list.append(area)  # Wh/m2
    el_tot = tuple(el_tot_list)
    area = el_tot
    # area = tuple(map(lambda x:100, anno))
    # marker colors
    anno_colors = tuple(map(lambda i: COLOR_CODES[i], anno))

    # format the plt
    plt.figure()
    case_names = {'HOT': 'Hotel', 'OFF': 'Office', 'RET': 'Retail'}
    case_shown = case_names[case.split('_')[4]]
    plt.title(case_shown, fontsize=18)
    plt.ylabel('COP', fontsize=18)
    x_labels_shown = []
    for label in x_labels:
        A, B, C = label.split("0")
        label_shown = A + B + C if C != '' else A + B + '0'
        x_labels_shown.append(label_shown)
    plt.xticks(x_values, x_labels_shown, fontsize=18, rotation=40)
    plt.yticks(y_values, y_labels, fontsize=18)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.2, max(y_values) + 0.2])
    plt.scatter(x, y, c=anno_colors, s=area)
    # plt.show()
    plt.savefig(path_to_all_district_plot(case, path_district_result_folder, 'COP'))
    return np.nan


def plot_scatter_EX(all_exergy_eff_dict, path_district_result_folder):
    # get all the points
    look_up_first_level_key, second_level_key, value = get_all_points_from_dict(all_exergy_eff_dict)

    # x axis
    x = look_up_first_level_key
    x_labels = list(all_exergy_eff_dict.keys())
    x_labels.sort()
    x_values = list(range(len(x_labels)))
    # y axis
    y = value
    # y_values = np.arange(round(min(y)),round(max(y))+2)
    y_values = np.arange(0, 30, 5)
    y_minor_values = y_values + 0.5
    y_labels = [0, 5, 10, 15, 30, 25]
    # marker size
    anno = second_level_key
    area = tuple(map(lambda x: 100, anno))
    # marker colors
    anno_colors = tuple(map(lambda i: COLOR_CODES[i], anno))

    # format the plt
    plt.figure()
    case_names = {'HOT': 'Hotel', 'OFF': 'Office', 'RET': 'Retail'}
    case_shown = case_names[case.split('_')[4]]
    plt.title(case_shown, fontsize=18)
    plt.ylabel('exergy efficiency [%]', fontsize=18)
    x_labels_shown = []
    for label in x_labels:
        A, B, C = label.split("0")
        label_shown = A + B + C if C != '' else A + B + '0'
        x_labels_shown.append(label_shown)
    plt.xticks(x_values, x_labels_shown, fontsize=18, rotation=40)
    plt.yticks(y_values, y_labels, fontsize=18)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.2, max(y_values) + 0.2])
    plt.scatter(x, y, c=anno_colors, s=area)
    # plt.show()
    plt.savefig(path_to_all_district_plot(case, path_district_result_folder, 'EX'))
    return np.nan


def get_all_points_from_dict(two_level_dict):
    building_name_key = list(two_level_dict.keys())
    building_name_key.sort()  # so the results display by this order
    # lookup table mapping category
    building_lookup_table = dict((v, k) for k, v in enumerate(building_name_key))
    # build a list of points (x,y,annotation)
    points = [(building_lookup_table[v], tech, cop)
              for v, values in two_level_dict.items()
              for tech, cop in (values if values else {}).items()]
    building_lookup_key, tech_key, value = zip(*points)
    return building_lookup_key, tech_key, value


def path_to_el_compare_files(path_district_result_folder, time_steps):
    """
    find files with _el_compare.csv and return a list of paths
    :param building:
    :return:
    """

    all_folders_in_path = os.listdir(path_district_result_folder)
    path_to_files = []
    for folder in all_folders_in_path:
        if '.csv' not in folder and '.png' not in folder:  # avoid opening a file
            if '_' in folder and float(folder.split('_')[1]) == time_steps:
                path_to_building_folder = os.path.join(path_district_result_folder, folder)
                # path_to_building_folder = os.path.join(path_to_building_folder, "reduced") #FIXME
                file_name = folder.split('_')[0] + '_' + 'el_compare.csv'
                path_to_file = os.path.join(path_to_building_folder, file_name)
                path_to_files.append(path_to_file)
    return path_to_files


def path_to_save_all_dirstrict_df(case, path_district_result_folder):
    filename = case + '_all_districts.csv'
    path_to_file = os.path.join(path_district_result_folder, filename)
    return path_to_file


def path_to_all_district_plot(case, path_district_result_folder, name):
    filename = case + '_' + name + '_all_techs.png'
    path_to_file = os.path.join(path_district_result_folder, filename)
    return path_to_file


def path_to_save_building_fig(filename, building, time_steps, path_district_result_folder):
    foldername = building + '_' + str(time_steps)
    path_to_folder = os.path.join(path_district_result_folder, foldername)
    path_to_file = os.path.join(path_to_folder, filename)
    return path_to_file


if __name__ == '__main__':
    # cases = ["HKG_CBD_m_WP1_RET", "HKG_CBD_m_WP1_OFF", "HKG_CBD_m_WP1_HOT",
    #          "ABU_CBD_m_WP1_RET", "ABU_CBD_m_WP1_OFF", "ABU_CBD_m_WP1_HOT",
    #          "MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT",
    #          "WTP_CBD_m_WP1_RET", "WTP_CBD_m_WP1_OFF", "WTP_CBD_m_WP1_HOT"]
    # cases = ['WTP_CBD_m_WP1_RET']
    cases = ['WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_RET']
    #cases = ["HKG_CBD_m_WP1_RET", "HKG_CBD_m_WP1_OFF", "HKG_CBD_m_WP1_HOT"]
    # cases = ["ABU_CBD_m_WP1_RET", "ABU_CBD_m_WP1_OFF", "ABU_CBD_m_WP1_HOT"]
    # cases = ["MDL_CBD_m_WP1_RET", "MDL_CBD_m_WP1_OFF", "MDL_CBD_m_WP1_HOT"]
    # cases = ['WTP_CBD_m_WP1_RET']
    for case in cases:
        print case
        # path_result_folder = "C:\\Users\\Shanshan\\Documents\\WP1_results"
        path_result_folder = "C:\\Users\\Shanshan\\Documents\\WP1_results_0629"
        time_steps = 168
        main(path_result_folder, case, time_steps)
