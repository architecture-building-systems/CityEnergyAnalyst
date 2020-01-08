# import packages
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters
from cea.osmose.post_process_osmose_results import read_file_as_df

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
Y_CARNOT_RANGE = [-0.1, 0.02]
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(273,350)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]', 'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE))},
              'carnot_fraction':{'ylabel':'Carnot factor [-]', 'xlabel':'Qc_load/Qsc [-]',
                                 'xlim':(0,1), 'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE))}
              }

def plot_carnot_from_icc_txt(path, t_list, T_ref_list, line_types, plot_type, model_name, total_df, exergy_df):

    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the lines
    if isinstance(t_list, int):
        label = 'line_type'
        t = t_list
        exergy_recovered = exergy_df.loc[t, 'exergy_recovered_total']
        exergy_usage = exergy_df.loc[t, 'exergy_use_total']
        exergy_percent_recovered = exergy_recovered / exergy_usage
        Qsc_t = total_df.loc[str(t), 'Qsc_theoretical']
        extra_values = {'ex_recovered': exergy_percent_recovered, 'Qsc_t': Qsc_t}
        get_data_and_plot_curves_of_t(T_ref_list, ax1, line_types, model_name, path, plot_type, t_list, label, extra_values)
        fig_name = 'carnot' + '_' + model_name + '_t' + str(t_list) + '_DefaultHeatCascade.png'
    else:
        for t in t_list:
            label = 't'
            get_data_and_plot_curves_of_t(T_ref_list, ax1, line_types, model_name, path, plot_type, t, label, '')
        fig_name = 'carnot' + '_' + model_name + '_' + str(t_list.min()) + '_' + str(t_list.max()) + '_DefaultHeatCascade.png'

    # build second y-axis (Temperature)
    ax2 = ax1.twinx()
    ax2.set(ylim=calc_T_from_carnot(T_ref_list[t-1],Y_CARNOT_RANGE))
    ax2.set_ylabel(ylabel='Temperature [C]' , fontsize=18, fontname = 'Times New Roman', fontweight='normal')

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS['carnot_fraction'])
    fig1 = plt.gcf()
    os.chdir("..\\")
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig(fig_name, transparent=True)
    return

def plot_carnot_from_icc_txt_techs(paths, t, T_ref_dict, line_types, plot_type, txt_name):
    case = 'B005'
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the lines
    for tech in paths.keys():
        path = paths[tech]
        T_ref = T_ref_dict[tech][t - 1]
        for line_type in line_types:
            print(path)
            if case == '':
                case = 'B' + path.split('run_')[1].split('_B')[0]
            x, y = load_data_from_txt(path, plot_type, line_type, txt_name, t)
            # plot x,y
            y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y + 273.15)
            ax1.plot(x, y_carnot, '-', color=COLOR_CODES[tech], label=KEY_TABLE[tech])
            # fill area
            y_origin = np.zeros(len(y))
            ax1.fill_between(x, y_carnot, y_origin, facecolor=COLOR_CODES[tech], alpha=0.4)
    # build second y-axis (Temperature)
    ax2 = ax1.twinx()
    ax2.set(ylim=calc_T_from_carnot(T_ref,Y_CARNOT_RANGE))
    ax2.set_ylabel(ylabel='Temperature [C]' , fontsize=18, fontname = 'Times New Roman', fontweight='normal')

    # save the figure
    ax1.set_title('t = ' + str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'})
    set_plot_parameters(ax1, PLOT_SPECS['carnot'])
    ax1.set(xlim=(0,1600)) #TODO: delete
    fig1 = plt.gcf()
    os.chdir("..\\"*6)
    print('saving fig to...', os.path.abspath(os.curdir))
    fig_name = case + '_carnot' + '_techs_' + str(t) + '_DefaultHeatCascade.png'
    fig1.savefig(fig_name, transparent=True)
    return


def get_data_and_plot_curves_of_t(T_ref_list, ax1, line_types, model_name, path, plot_type, t, label, extra_values):
    T_ref = T_ref_list[t - 1]
    c = 0
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y + 273.15)
        # format figure
        if label == 't':
            label_name = t
            color = COLOR_LIST[c]
            c += 1
        else:
            label_name = line_type
            color = COLOR_TABLE[line_type]
        # plotting
        if extra_values != '':
            x_new = x/extra_values['Qsc_t']
            exergy_recovered = str(round(extra_values['ex_recovered'] * 100, 1))
            Qc_load = 'Qc_load : ' + str(round(max(x),1))
            Qsc = 'Qsc : ' + str(round(extra_values['Qsc_t'],1))
            ax1.annotate('exergy recovery: ' + exergy_recovered + '% \n' + Qc_load + '\n' + Qsc,
                         xy=(0.57,0.15), xycoords='figure fraction', fontsize=18)
                         # bbox=dict(boxstyle="round", fc="none", ec="gray"))
            ax1.plot(x_new, y_carnot, '-', color=color, label=label_name)
        else:
            ax1.plot(x, y_carnot, '-', color=color, label=label_name)
        ax1.set_title('t = ' + str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'})


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
    return (T_min - 273.15, T_max - 273.15)

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
        if len(valid_index_list) <= 0:
            print (idx, 'no valid index')
        T_list = []
        for index in valid_index_list:
            new_index = index.split('Hin')[0] + 'Tin'
            T_list.append(streams_df.iloc[idx][new_index])
            if T_list != []:
                T_max = max(T_list)
            else:
                print(idx, 'no T_list')
        T_max_list.append(T_max)
    return T_max_list

def calc_T_ref(path_to_run_folder):
    # get output_df
    # path_to_run_folder = os.path.join(path_to_folder, run_folder)
    files_in_path = os.listdir(path_to_run_folder)
    file_name = [file for file in files_in_path if 'output' in file][0]
    path_to_file = os.path.join(path_to_run_folder, file_name)
    outputs_df = pd.read_csv(path_to_file, header=None).T
    outputs_df.columns = outputs_df.iloc[0]
    outputs_df = outputs_df[1:]
    T_ref_list = outputs_df['T_OA'] + 273.15
    return T_ref_list.values




def plot_iccc_for_one_tech(path_to_base_folder, run_folder, tech):
    ## plot one tech
    plot_type = 'models'   #'locations' #'models'
    model_folder = [path_to_base_folder, tech, run_folder, 's_001\\plots\\icc\\', plot_type]
    path_to_models_folder = os.path.join('', *model_folder)
    # T_max_list = calc_T_max(path_to_base_folder + tech, run_folder)
    path_to_folder = os.path.join('', *[path_to_base_folder, tech, run_folder])
    T_ref_list = calc_T_ref(path_to_folder)
    line_types = ['base']  # 'separated',

    # get total_df
    files_in_path = os.listdir(path_to_folder)
    file_name = [file for file in files_in_path if 'total' in file][0]
    total_df = pd.read_csv(os.path.join(path_to_folder, file_name), index_col=0)
    # get exergy_df
    file_name = [file for file in files_in_path if 'exergy_from_plot' in file][0]
    exergy_df = pd.read_csv(os.path.join(path_to_folder, file_name), index_col=0)

    #
    # ## plotting one t at a time
    for t in np.arange(25, 48, 1):
    # for t in [12]:
        txt_name = 'all_chillers' #'all_chillers', 'loc4'
        plot_carnot_from_icc_txt(path_to_models_folder, t, T_ref_list, line_types, 'icc', txt_name, total_df, exergy_df)
    ## plot multiple t in one figure
    # t_list = np.arange(96+3,96+24,6)
    # model_folder = ['E:\\HCS_results_1015\\base\\', 'HCS_base', 'run_005_RET_B005_1_168', 's_001\\plots\\icc\\models']
    # path_to_folder = os.path.join('', *model_folder)
    # plot_carnot_from_icc_txt(path_to_folder, t_list, T_max_list, T_ref_list, line_types, 'icc', 'all_chillers')


def main():
    tech = 'HCS_base_coil'
    # path_to_base_folder = 'E:\\OSMOSE_projects\\HCS_mk\\results\\'
    path_to_base_folder = 'E:\\results_1130\\'
    path_to_base_folder = 'C:\\Users\\Zhongming\\Documents\\HCS_mk\\results\\'
    # path_to_base_folder = 'E:\\OSMOSE_projects\\HCS_mk\\results\\'
    run_folder = 'run_003_OFF_B005_1_168'
    folders_to_compare = {#'HCS_base': 'run_003_OFF_B005_1_168',
                          # 'HCS_base_ER0': 'run_003_OFF_B005_1_168',
                          'HCS_base_coil': 'run_003_OFF_B005_1_168',
                          'HCS_base_3for2': 'run_003_OFF_B005_1_168',
                          'HCS_base_LD': 'run_003_OFF_B005_1_168' }

    # plot one tech (with x axis = Qc/Qsc
    # run_folders = os.listdir(os.path.join(path_to_base_folder, tech))
    # for run_folder in ['run_003_OFF_B005_1_168']:
    #     if 'run' in run_folder:
    #         plot_iccc_for_one_tech(path_to_base_folder, run_folder, tech)


    ## plot multiple techs in one figure
    paths_to_folder, T_max_dict, T_ref_dict = {}, {}, {}
    # for tech in ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']:
    for tech in folders_to_compare.keys():
        run_folder = folders_to_compare[tech]
        model_folder = [path_to_base_folder, tech, run_folder, 's_001\\plots\\icc\\models']
        paths_to_folder[tech] = os.path.join('', *model_folder)
        T_max_dict[tech] = calc_T_max(path_to_base_folder + tech, run_folder)
        path_to_folder = os.path.join('', *[path_to_base_folder, tech, run_folder])
        T_ref_dict[tech] = calc_T_ref(path_to_folder)
    #
    # for t in np.arange(25,48,1):
    for t in np.arange(73,73+24,1):
    # for t in [83]:
        line_types = ['base'] # 'base'
        plot_carnot_from_icc_txt_techs(paths_to_folder, t, T_ref_dict, line_types, 'icc', 'all_chillers')



if __name__ == '__main__':
    main()