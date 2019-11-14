import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt
from cea.osmose.plots.plot_carnot_from_icc import calc_carnot_factor, calc_T_ref

COLOR_LIST = ['#43444b', '#5c5d67', '#2a2b2f',
              '#590c12', '#771119', '#95141e', '#ab2b35', '#bc555d', '#3c080c',
              '#ae961a', '#574b0d', '#837014',  '#dacb20', '#f0d137',
              '#032323', '#053534', '#064646', '#085857',  '#4b8b8a',
              '#333452', '#1e6e6d', '#474863', '#5c5c74', '#707186', '#848597']


def calc_exergy_from_plot(paths_to_folder, t, line_type, T_ref, plot_type, models_to_plot):

    # load and prepare data
    x, y = load_data_from_txt(paths_to_folder, plot_type, line_type, models_to_plot, t)
    y_carnot = np.vectorize(calc_carnot_factor)(T_ref[t-1], y + 273.15)
    # get indices of exergy use and exergy gain
    ix_ascending, ix_descending = get_exergy_use_gain_indices(x)
    # calculate exergy recovered
    exergy_dict, total_exergy_recovered = calculate_exergy_recovered(T_ref[t-1], ix_ascending, ix_descending, t, x, y, y_carnot)
    exergy_dict['exergy_recovered_total'] = total_exergy_recovered
    # calculate total exergy usage
    exergy_dict['exergy_use_total'] = np.trapz(y_carnot,x)
    exergy_dict['Q_total'] = max(x)

    return exergy_dict, total_exergy_recovered


def calculate_exergy_recovered(T_ref_K, ix_ascending, ix_descending, t, x, y, y_carnot):
    total_exergy_recovered = 0
    exergy_dict = {}
    # find the section of energy recovery
    ix_intersection = list(set(ix_ascending).intersection(set(ix_descending)))
    ix_intersection.sort()
    for i in range(len(ix_intersection) / 2):
        ix_search = ix_intersection[2 * i]    # the index when the curve bends
        ix_start = ix_intersection[2 * i + 1] # the index to start searching
        ix_end = len(x)                       # the index to end searching
        if x[ix_search] >= 0:                 # ignore the negative heat loads
            for ix in np.arange(ix_start, ix_end, 1):
                # identify the temperature (y) when the heat load is equal ot ix_search
                if x[ix] <= x[ix_search] <= x[ix + 1] or x[ix] >= x[ix_search] >= x[ix + 1]:
                    # print ('time', t, 'found:', x[ix_search], 'between:', x[ix], x[ix + 1])
                    # find T from interpolation
                    x_ratio = (x[ix] - x[ix_search]) / (x[ix] - x[ix + 1])
                    T = y[ix] - x_ratio * (y[ix] - y[ix + 1])
                    print ('time', t, 'matched temperature is: ', T)
                    carnot_T = calc_carnot_factor(T_ref_K, T + 273.15)
                    # calculate exergy gained in the intersection
                    exergy_gain = abs(np.trapz(y_carnot[ix_search:ix_start + 1], x[ix_search:ix_start + 1]))
                    # calculate exergy used in the intersection
                    y_exergy_use = np.append(y_carnot[ix_start:ix + 1], carnot_T)
                    x_exergy_use = np.append(x[ix_start:ix + 1], x[ix_search])
                    exergy_use = np.trapz(y_exergy_use, x_exergy_use)
                    if exergy_use < 0.0:
                        print(exergy_use, 'should be positive')
                    # calculate exergy recovered
                    total_exergy_recovered = total_exergy_recovered + (exergy_gain - exergy_use)
                    exergy_dict[str(ix_search) + '_' + str(ix_start)] = exergy_gain - exergy_use
                    exergy_dict[str(ix_search) + '_' + str(ix_start) + '_Q'] = abs(x[ix_search] - x[ix_start])
                    break
    return exergy_dict, total_exergy_recovered


def get_exergy_use_gain_indices(x):
    ix_descending = []
    ix_ascending = []
    for ix, Q in enumerate(x):
        if ix == 1:  # log the first index
            dQ = Q - x[ix - 1]
            if dQ > 0:
                ascending = True
                ix_ascending.append(ix - 1)
            else:
                ascending = False
                ix_descending.append(ix - 1)
        if len(x) - 1 > ix > 1:  # start from index = 1
            dQ = Q - x[ix - 1]
            if dQ >= 0:  # heat load increasing
                if ascending == False:
                    # print(ix - 1)
                    ix_ascending.append(ix - 1)
                    ix_descending.append(ix - 1)
                    ascending = True
            else:
                if ascending == True:
                    # print(ix - 1)
                    ix_ascending.append(ix - 1)
                    ix_descending.append(ix - 1)
                    ascending = False
        if ix == len(x) - 1:
            if ascending == True:
                ix_ascending.append(ix)
            else:
                ix_descending.append(ix)
    return ix_ascending, ix_descending


def main():
    # case
    tech = 'HCS_base'
    path_to_base_folder = 'E:\\OSMOSE_projects\\HCS_mk\\results\\'
    # path_to_base_folder = "E:\\HCS_results_1022\\HCS_base_m_out_dP"

    # all_run_folders = os.listdir(os.path.join(path_to_base_folder, tech))
    all_run_folders = ['run_036_RET_B005_1_24', 'run_037_HOT_B005_1_24', 'run_038_OFF_B005_1_24']
    for run_folder in all_run_folders:
        if 'run' in run_folder:
            print(run_folder)
            line_types = ['base']  # 'base'
            # combine paths
            model_folder = [path_to_base_folder, tech, run_folder, 's_001\\plots\\icc\\models']
            paths_to_model_folder = os.path.join('', *model_folder)
            path_to_run_folder = os.path.join('', *[path_to_base_folder, tech, run_folder])
            T_ref = calc_T_ref(path_to_run_folder)

            for line_type in line_types:
                exergy_df = pd.DataFrame()
                # for t in [1]:
                for t in np.arange(1,25,1):
                # for t in np.arange(73,73+24,1):
                    exergy_dict, total_exergy_recovered = calc_exergy_from_plot(paths_to_model_folder, t, line_type, T_ref, 'icc', 'all_chillers')
                    for key in exergy_dict.keys():
                        exergy_df.loc[t, key] = exergy_dict[key]
                file_name = 'exergy_from_plot_' + line_type + '.csv'
                exergy_df.to_csv(os.path.join(path_to_run_folder, file_name), na_rep='NaN')

if __name__ == '__main__':
    main()