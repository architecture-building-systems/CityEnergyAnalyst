import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

## Matplotlib

def set_plot_parameters(ax1, plot_specs):
    fontname = 'Times New Roman'
    fontsize = 8
    # set the legend
    # ax1.legend(loc='lower left', shadow=False, fancybox=True,
    #            fontsize=fontsize, prop={'family': 'Times New Roman', 'size': str(fontsize)})
    if 'show_legend' in plot_specs.keys():
        if plot_specs['show_legend']:
            ax1.legend(loc='lower left', bbox_to_anchor =(1,0), shadow=False, fancybox=True,
                       fontsize=fontsize, prop={'family': 'Times New Roman', 'size': str(fontsize)})
    # set x and y range
    # plt.set_xlim([-766.00311044128,8090.8964687342])
    if 'xlim' in plot_specs.keys():
        ax1.set(xlim=plot_specs['xlim'])
    ax1.set(ylim=plot_specs['ylim'])
    # format ticks
    plt.xticks(fontname=fontname, fontsize=fontsize)
    plt.yticks(fontname=fontname, fontsize=fontsize)
    for label in ax1.xaxis.get_majorticklabels():
        label.set_fontsize(fontsize)
        label.set_fontname(fontname)
    for label in ax1.yaxis.get_majorticklabels():
        label.set_fontsize(fontsize)
        label.set_fontname(fontname)
    # set the axis labels
    ax1.set_ylabel(plot_specs['ylabel'], fontsize=fontsize, color='black', fontname=fontname, fontweight='normal')
    ax1.set_xlabel(plot_specs['xlabel'], fontsize=fontsize, color='black', fontname=fontname, fontweight='normal')
    # tight layout prevents axis title overlapping
    # plt.tight_layout(pad=1, w_pad=3, h_pad=1.0)
    return

## Data

def load_data_from_txt(path, plot_type, line_type, txt_name, t):
    """
    reads '.txt' files that contains plot data
    :param path: path to the folder of the .txt file
    :param plot_type:
    :param line_type: "base" or "seperated"
    :param txt_name:
    :param t:
    :return:
    """
    os.chdir(path)
    if txt_name == '':
        file_name = plot_type + '_' + line_type + '_m_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    elif 'loc' in txt_name:
        file_name = plot_type + '_' + line_type + '_loc_' + txt_name + '_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    else:
        file_name = plot_type + '_' + line_type + '_m_' + txt_name + '_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    if os.path.isfile(os.path.join(path, file_name)):
        data = np.genfromtxt(file_name, delimiter=' ')
        # x and y axes
        x = data[:, 0]
        y = data[:, 1]
    else:
        x, y = 0, 0
    return x, y


## Calculation

def calc_T_ref(path_to_run_folder):
    """
    Get temperature of the reference environment.
    :param path_to_run_folder:
    :return: ndarray
    """
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


def calc_T_from_carnot(T_ref, carnot):
    """
    calculates the corresponding temperatures from carnot factors
    :param T_ref:
    :param carnot:
    :return:
    """
    T_max = T_ref/(1-max(carnot)) #carnot = 0.1
    T_min = T_ref/(1-min(carnot)) #carnot = -0.1
    delta_T = max(T_max-T_ref, T_ref-T_min)
    return (T_min - 273.15, T_max - 273.15)


def calc_carnot_factor(T_ref, T):
    """
    calculates carnot factor using the reference temperature.
    :param T_ref: temperature of the reference environment
    :param T: temperature of interest
    :return:
    """
    carnot = 1 - T_ref/T
    return carnot