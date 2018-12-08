from __future__ import division
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt




def main():
    building = 'B002'
    paths = path_to_elec_csv_files(building)
    el_dfs = {}
    compare_df = pd.DataFrame()
    for path in paths:
        tech = path.split('\\')[5].split('_')[2]
        el_dfs[tech] = pd.read_csv(path)
        compare_df[tech] = el_dfs[tech].ix[168][1:]
    # compare_df = compare_df.loc['el_chi_lt', 'el_aux_lcu', 'el_chi_oau', 'el_aux_oau', 'el_chi_ht', 'el_aux_scu', 'el_ct', 'el_total']
    compare_df.to_csv(path_to_save_compare_df(building))
    return


def path_to_elec_csv_files(building):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    all_files_in_path = os.listdir(path_to_folder)
    path_to_files = []
    file_name = 'el.csv'
    for file in all_files_in_path:
        if file_name in file:
            path_to_file = os.path.join(path_to_folder, file)
            path_to_files.append(path_to_file)
    return path_to_files

def path_to_save_compare_df(building):
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\results\\' + building
    path_to_file = os.path.join(path_to_folder, 'el_compare.csv')
    return path_to_file

if __name__ == '__main__':
    main()