from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

PATH_TO_FOLDER = 'C:\\Users\\Shanshan\\Documents\\0_Shanshan_Hsieh\\WP1\\results\\'


def main():
    building = 'B007'
    paths = path_to_elec_csv_files(building)
    chiller_paths = path_to_chiller_csv_files(building)
    el_dfs = {}
    cop_mean = {}
    compare_df = pd.DataFrame()
    for path in paths:
        file_name = path.split('\\')
        tech = [x for x in file_name if 'HCS' in x][0].split('_')[2]
        el_dfs[tech] = pd.read_csv(path)
        index = el_dfs[tech].shape[0] - 1
        cop_mean[tech] = el_dfs[tech]['cop_system'].replace(0, np.nan).mean()
        compare_df[tech] = el_dfs[tech].ix[index][1:]
    # compare_df = compare_df.loc['el_chi_lt', 'el_aux_lcu', 'el_chi_oau', 'el_aux_oau', 'el_chi_ht', 'el_aux_scu', 'el_ct', 'el_total']

    # T_low_C = 8.1
    # T_high_C = 14.1
    # T_interval = 0.65  # 0.5
    # T_OAU_offcoil = np.arange(T_low_C, T_high_C, T_interval)
    #chiller_df = pd.DataFrame(columns=T_OAU_offcoil)
    i = 0
    for path in chiller_paths:
        if i == 0:
            chiller_df = pd.read_csv(path)
            chiller_df = chiller_df.set_index(chiller_df.columns[0])
            i = i + 1
        else:
            chiller = pd.read_csv(path)
            chiller = chiller.set_index(chiller.columns[0])
            chiller_df = chiller_df.append(chiller)

    float_columns = [float(x) for x in chiller_df.columns]
    float_columns.sort()
    string_columns = [str(x) for x in float_columns]
    chiller_df = chiller_df.reindex(string_columns,axis=1)
    chiller_df = chiller_df.fillna(0)
    plot_chiller_temperatures(chiller_df, building)

    compare_df.to_csv(path_to_save_compare_df(building))
    return


def plot_chiller_temperatures(chiller_df, building):
    X = np.arange(chiller_df.columns.size)
    fig, ax = plt.subplots()
    width = 0.00
    for i in range(chiller_df.index.size):
        ax.bar(X + width, chiller_df.loc[chiller_df.index[i]][:], width=0.25, label=chiller_df.index[i])
        width = width + 0.25
    #ax.bar(X + 0.25, chiller_df.loc[chiller_df.index[1]][:], width=0.25, label=chiller_df.index[1])
    ax.legend(loc='upper right')
    ax.set_xticks(X + width / 2)
    ax.set_xticklabels(tuple(chiller_df.columns))
    #ax.set_xticks(chiller_df.columns)
    ax.set(xlabel='Temperature [C]', ylabel='Frequency', ylim=(0, 1))
    #plt.show()
    fig.savefig(path_to_save_chiller_t(building))
    return np.nan

def path_to_elec_csv_files(building):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(path_to_folder)
    path_to_files = []
    file_name = 'el.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(path_to_folder, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_chiller_csv_files(building):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    path_to_folder = PATH_TO_FOLDER + building
    all_files_in_path = os.listdir(path_to_folder)
    path_to_files = []
    file_name = 'chiller.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(path_to_folder, file)
            path_to_files.append(path_to_file)
    return path_to_files


def path_to_save_compare_df(building):
    path_to_folder = PATH_TO_FOLDER + building
    filename = building + '_el_compare.csv'
    path_to_file = os.path.join(path_to_folder, filename)
    return path_to_file

def path_to_save_chiller_t(building):
    path_to_folder = PATH_TO_FOLDER + building
    filename = building + '_chiller.png'
    path_to_file = os.path.join(path_to_folder, filename)
    return path_to_file


if __name__ == '__main__':
    main()
