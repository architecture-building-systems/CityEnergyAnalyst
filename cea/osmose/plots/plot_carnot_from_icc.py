# import packages
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters

rcParams['mathtext.default'] = 'regular'

# # fix on times new roman font
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()

COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}
COLOR_LIST = ['#C96A50', '#3E9AA3', '#3E9BA3']
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(273,350)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]', 'ylim':(-0.1,0.1)}}

def plot_carnot_from_icc_txt(path, t, T_max, T_ref, plot_type, model_name):
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the lines
    line_types = ['base', 'separated']
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        dT = T_max - y.max()
        y_original = y + dT if line_type == 'base' else y - dT
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y_original)
        ax1.plot(x, y_carnot, '-', color=COLOR_TABLE[line_type], label=line_type)

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS['carnot'])
    fig1 = plt.gcf()
    os.chdir("..\\")
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig('carnot' + '_' + model_name + '_t' + str(t) + '_DefaultHeatCascade.png', transparent=True)
    return

##===================
## general functions
##===================

def calc_carnot_factor(T_ref, T):
    carnot = 1 - T_ref/T
    return carnot

def calc_T_max(path_to_folder, run_folder):
    # get streams_df
    path_to_run_folder = os.path.join(path_to_folder, run_folder)
    files_in_path = os.listdir(path_to_run_folder)
    file_name = [file for file in files_in_path if 'streams' in file][0]
    path_to_file = os.path.join(path_to_run_folder, file_name)
    streams_df = pd.read_csv(path_to_file, header=None).T
    streams_df.columns = streams_df.iloc[0]
    streams_df = streams_df[1:]

    T_max_list = []
    for idx in range(streams_df.shape[0]):
        Hin_list = streams_df.filter(like='Hin').iloc[idx]
        valid_index_list = Hin_list[Hin_list > 0.0].index
        T_list = []
        for index in valid_index_list:
            new_index = index.split('Hin')[0] + 'Tin'
            T_list.append(streams_df.iloc[idx][new_index])
        T_max = max(T_list)
        T_max_list.append(T_max)
    return T_max_list

def calc_T_ref(path_to_folder, run_folder):
    # get output_df
    path_to_run_folder = os.path.join(path_to_folder, run_folder)
    files_in_path = os.listdir(path_to_run_folder)
    file_name = [file for file in files_in_path if 'output' in file][0]
    path_to_file = os.path.join(path_to_run_folder, file_name)
    outputs_df = pd.read_csv(path_to_file, header=None).T
    outputs_df.columns = outputs_df.iloc[0]
    outputs_df = outputs_df[1:]
    T_ref_list = outputs_df['T_OA'] + 273.15
    return T_ref_list.values

def main():
    path_to_base_folder = 'E:\\ipese_new\\osmose_mk\\results\\HCS_base'
    run_folder = 'run_005'
    model_folder = [path_to_base_folder, run_folder, 's_001\\plots\\icc\\models']
    path_to_folder = os.path.join('', *model_folder)

    # plotting
    T_max_list = calc_T_max(path_to_base_folder, run_folder)
    T_ref_list = calc_T_ref(path_to_base_folder, run_folder)
    for t in np.arange(1,25,1):
        T_max = T_max_list[t-1]
        T_ref = T_ref_list[t-1]
        plot_carnot_from_icc_txt(path_to_folder, t, T_max, T_ref, 'icc', 'all_chillers')



if __name__ == '__main__':
    main()