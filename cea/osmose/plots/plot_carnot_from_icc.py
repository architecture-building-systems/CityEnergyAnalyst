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
COLOR_LIST = ['#43444b', '#5c5d67', '#2a2b2f',
              '#590c12', '#771119', '#95141e', '#ab2b35', '#bc555d', '#3c080c',
              '#ae961a', '#574b0d', '#837014',  '#dacb20', '#f0d137',
              '#032323', '#053534', '#064646', '#085857',  '#4b8b8a',
              '#333452', '#1e6e6d', '#474863', '#5c5c74', '#707186', '#848597']
COLOR_CODES = {'HCS_base_3for2': '#C96A50', 'HCS_base_coil': '#3E9AA3', 'HCS_base_ER0': '#E2B43F',
               'HCS_base_IEHX': '#51443D', 'HCS_base_LD': '#6245A3',
               'HCS_base': '#707070'}
KEY_TABLE = {'HCS_base_ER0': 'HCS_ER0', 'HCS_base_coil': 'HCS_coil', 'HCS_base_3for2': 'HCS_3for2',
             'HCS_base_IEHX': 'HCS_IEHX', 'HCS_base_LD': 'HCS_LD', 'HCS_base': 'HCS_base'}
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(273,350)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]', 'ylim':(-0.1,0.1)}}

def plot_carnot_from_icc_txt(path, t_list, T_max_list, T_ref_list, line_types, plot_type, model_name):
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the lines
    if isinstance(t_list, int):
        label = 'line_type'
        get_data_and_plot_curves_of_t(T_max_list, T_ref_list, ax1, line_types, model_name, path, plot_type, t_list, label)
        fig_name = 'carnot' + '_' + model_name + '_t' + str(t_list) + '_DefaultHeatCascade.png'
    else:
        for t in t_list:
            label = 't'
            get_data_and_plot_curves_of_t(T_max_list, T_ref_list, ax1, line_types, model_name, path, plot_type, t, label)
        fig_name = 'carnot' + '_' + model_name + '_' + str(t_list.min()) + '_' + str(t_list.max()) + '_DefaultHeatCascade.png'

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS['carnot'])
    fig1 = plt.gcf()
    os.chdir("..\\")
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig(fig_name, transparent=True)
    return

def plot_carnot_from_icc_txt_techs(paths, t, T_max_dict, T_ref_dict, line_types, plot_type, model_name):
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the lines

    for tech in paths.keys():
        path = paths[tech]
        T_max = T_max_dict[tech][t - 1]
        T_ref = T_ref_dict[tech][t - 1]
        for line_type in line_types:
            print(path)
            _, y_base = load_data_from_txt(path, plot_type, 'base', model_name, t)
            dT = T_max - y_base.max()
            x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
            y_original = y + dT if line_type == 'base' else y - dT
            y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y_original)
            ax1.plot(x, y_carnot, '-', color=COLOR_CODES[tech], label=KEY_TABLE[tech])
    ax2 = ax1.twinx()
    # ax2.plot(x, y_original, color='#333452')
    ax2.set(ylim=calc_T_from_carnot(T_ref,[-0.1,0.1]))
    ax2.set_ylabel(ylabel='Temperature [C]' , fontsize=18, fontname = 'Times New Roman', fontweight='normal')

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS['carnot'])
    ax1.set_title('t = ' + str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'})
    fig1 = plt.gcf()
    os.chdir("..\\"*7)
    print('saving fig to...', os.path.abspath(os.curdir))
    fig_name = 'carnot' + '_techs_' + str(t) + '_DefaultHeatCascade.png'
    fig1.savefig(fig_name, transparent=True)
    return


def get_data_and_plot_curves_of_t(T_max_list, T_ref_list, ax1, line_types, model_name, path, plot_type, t, label):
    T_max = T_max_list[t - 1]
    T_ref = T_ref_list[t - 1]
    for line_type in line_types:
        # _, y_base = load_data_from_txt(path, plot_type, 'base', model_name, t)
        # dT = T_max - y_base.max()
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        dT = 0
        y_original = y + dT if line_type == 'base' else y - dT
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y_original)
        if label == 't':
            label_name = t
            color = COLOR_LIST[t]
        else:
            label_name = line_type
            color = COLOR_TABLE[line_type]
        ax1.plot(x, y_carnot, '-', color=color, label=label_name)


##===================
## general functions
##===================

def calc_carnot_factor(T_ref, T):
    carnot = 1 - T_ref/T
    return carnot

def calc_T_from_carnot(T_ref, carnot):
    T_max = T_ref/(1-max(carnot)) #carnot = 0.1
    T_min = T_ref/(1-min(carnot)) #carnot = -0.1
    delta_T = max(T_max-T_ref, T_ref-T_min)
    return (T_ref - delta_T, T_ref + delta_T)

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
    tech = 'HCS_base'
    # path_to_base_folder = 'E:\\HCS_results_1008\\WTP_CBD_m_WP1_OFF\\B005_1_24\\BATCH2\\'
    path_to_base_folder = 'E:\\ipese_new\\osmose_mk\\results\\'
    # run_folder = 'run_001_OFF_B005_1_24'
    run_folder = 'run_002'

    model_folder = [path_to_base_folder, tech,  run_folder, 's_001\\plots\\icc\\models']
    path_to_folder = os.path.join('', *model_folder)

    T_max_list = calc_T_max(path_to_base_folder + tech, run_folder)
    T_ref_list = calc_T_ref(path_to_base_folder + tech, run_folder)
    line_types = ['separated', 'base']
    #
    ## plotting one t at a time
    for t in np.arange(1,25,1):
        plot_carnot_from_icc_txt(path_to_folder, t, T_max_list, T_ref_list, line_types, 'icc', 'all_chillers')

    ## plot multiple t in one figure
    # t_list = np.arange(3,25,6)
    # plot_carnot_from_icc_txt(path_to_folder, t_list, T_max_list, T_ref_list, line_types, 'icc', 'all_chillers')

    ## plot multiple techs in one figure
    # paths_to_folder, T_max_dict, T_ref_dict = {}, {}, {}
    # for tech in ['HCS_base', 'HCS_base_coil']:
    # # for tech in ['HCS_base_3for2', 'HCS_base_coil']:
    #     model_folder = [path_to_base_folder, tech, run_folder, 's_001\\plots\\icc\\models']
    #     paths_to_folder[tech] = os.path.join('', *model_folder)
    #     T_max_dict[tech] = calc_T_max(path_to_base_folder + tech, run_folder)
    #     T_ref_dict[tech] = calc_T_ref(path_to_base_folder + tech, run_folder)
    # for t in np.arange(1,25,1):
    # # for t in [20]:
    #     line_types = ['separated'] # 'base'
    #     plot_carnot_from_icc_txt_techs(paths_to_folder, t, T_max_dict, T_ref_dict, line_types, 'icc', 'all_chillers')


if __name__ == '__main__':
    main()