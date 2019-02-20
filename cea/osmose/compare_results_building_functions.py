from __future__ import division
import numpy as np
import pandas as pd
import os
import operator
import matplotlib.pyplot as plt


def main(path_result_folder, cases, time_steps):
    # get names
    building_names_to_analyse, case_names = get_building_and_case_names(cases, path_result_folder, time_steps)
    building_names_to_analyse = ['B001', 'B002', 'B007'] #FIXME: to improve
    # get cop from buildings in all cases
    cop_in_all_cases_dict = {}
    for case in cases:
        path_district_result_folder = os.path.join(path_result_folder, case)
        el_compare_paths = path_to_el_compare_files(path_district_result_folder, time_steps)
        # iterate through files and combine results
        all_cop_dict = {}
        for path in el_compare_paths:
            building_name_of_path = path.split('\\')[6].split('_')[0]
            if building_name_of_path in building_names_to_analyse:
                el_compare_df = pd.read_csv(path, index_col=0)
                all_cop_dict[building_name_of_path] = el_compare_df.loc['cop_system'].to_dict()
        cop_in_all_cases_dict[case] = all_cop_dict
    # exchange dict levels
    for building in building_names_to_analyse:
        cop_building_in_all_case_dict = {}
        for case in cases:
            cop_building_in_all_case_dict[case] = cop_in_all_cases_dict[case][building]
        plot_scatter(building, cop_building_in_all_case_dict, path_result_folder)
        print building, ': done plotting'
    return np.nan


def get_building_and_case_names(cases, path_result_folder, time_steps):
    case_names = []
    building_names_in_all_cases_dict = {}
    for case in cases:
        case_names.append(case.split('_')[4])
        path_district_result_folder = os.path.join(path_result_folder, case)
        el_compare_paths = path_to_el_compare_files(path_district_result_folder, time_steps)
        building_names = []
        for path in el_compare_paths:
            building_name_of_path = path.split('\\')[6].split('_')[0]
            building_names.append(building_name_of_path)
        building_names_in_all_cases_dict[case] = building_names
    length_of_keys = {}
    for key in building_names_in_all_cases_dict.keys():
        length_of_keys[key] = len(building_names_in_all_cases_dict[key])
    building_names_to_analyse = building_names_in_all_cases_dict[min(length_of_keys)]
    return building_names_to_analyse, case_names


def get_el_compare_from_each_building(path):
    building = path.split('\\')[6].split('_')[0]
    el_compare_df = pd.read_csv(path, index_col=0)
    list_of_labels = []
    for label in ['cop_system', 'el_total', 'qc_sys_total']:
        list_of_labels.append(el_compare_df.loc[label])
    building_result_df = pd.concat(list_of_labels, axis=1)
    building_result_df = building_result_df.sort_values(by=['el_total']).T
    return building, building_result_df, el_compare_df


def plot_scatter(building, all_cop_dict, path_result_folder):

    # get all the points
    look_up_first_level_key, second_level_key, value = get_all_points_from_dict(all_cop_dict)

    # x axis
    x = look_up_first_level_key
    label_list = []
    for key in all_cop_dict.keys():
        label_list.append(key.split('_')[4])
    x_labels = label_list
    x_values = list(range(len(x_labels)))
    # y axis
    y = value
    # y_values = np.arange(round(min(y)),round(max(y))+2)
    y_values = np.arange(4,9)
    y_minor_values = y_values + 0.5
    y_labels = [str(v) for v in y_values]
    # marker size
    anno = second_level_key
    area = tuple(map(lambda x: 100, anno))
    # marker colors
    color_codes = {'3for2': '#C96A50', 'coil': '#3E9AA3', 'ER0': '#E2B43F', 'IEHX': '#51443D', 'LD': '#6245A3'}
    anno_colors = tuple(map(lambda i: color_codes[i], anno))

    # format the plt
    plt.figure()
    plt.title(building, fontsize=18)
    plt.ylabel('COP', fontsize=18)
    plt.xticks(x_values, x_labels, fontsize=18)
    plt.yticks(y_values, y_labels, fontsize=18)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.2, max(y_values) + 0.2])
    plt.scatter(x, y, c=anno_colors, s=area)
    # plt.show()
    plt.savefig(path_to_save_compare_plots(building, path_result_folder))
    return np.nan


def get_all_points_from_dict(two_level_dict):
    fist_level_key = list(two_level_dict.keys())
    # lookup table mapping category
    lookup_table = dict((v, k) for k, v in enumerate(fist_level_key))
    # build a list of points (x,y,annotation)
    points = [(lookup_table[action], key, anno)
              for action, values in two_level_dict.items()
              for key, anno in (values if values else {}).items()]
    look_up_first_level_key, second_level_key, value = zip(*points)
    return look_up_first_level_key, second_level_key, value


def path_to_el_compare_files(path_district_result_folder, time_steps):
    """
    find files with _el_compare.csv and return a list of paths
    :param building:
    :return:
    """

    all_folders_in_path = os.listdir(path_district_result_folder)
    path_to_files = []
    for folder in all_folders_in_path:
        if '.csv' not in folder and '.png' not in folder:
            if '_' in folder and float(folder.split('_')[1]) == time_steps:
                    path_to_building_folder = os.path.join(path_district_result_folder,folder)
                    file_name = folder.split('_')[0] + '_' + 'el_compare.csv'
                    path_to_file = os.path.join(path_to_building_folder,file_name)
                    path_to_files.append(path_to_file)
    return path_to_files


def path_to_save_all_dirstrict_df(case, path_district_result_folder):
    filename = case + '_all_districts.csv'
    path_to_file = os.path.join(path_district_result_folder, filename)
    return path_to_file


def path_to_save_compare_plots(building, path_result_folder):
    filename = building + '_cop_all_cases.png'
    path_to_file = os.path.join(path_result_folder, filename)
    return path_to_file

if __name__ == '__main__':
    cases = ['WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_OFF']
    path_result_folder = "C:\\Users\\Shanshan\\Documents\\WP1_results"
    time_steps = 168
    main(path_result_folder, cases, time_steps)