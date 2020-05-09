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
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['lines.linewidth'] = 2.0
rcParams['axes.linewidth'] = 2.0

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
CONFIG_TABLE = {'HCS_base_coil':'Config.1', 'HCS_base_ER0':'Config.2',
                'HCS_base_3for2': 'Config.3', 'HCS_base_IEHX':'Config.5'}
Y_CARNOT_RANGE = [0.0, -0.1]
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Cooling Load [kW]', 'ylim':(273,350)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Cooling Load [kW]',
                        'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE)),
                        'show_legend': False},
              'carnot_fraction':{'ylabel':'Carnot factor [-]', 'xlabel':'Qc_load/Qsc [-]',
                                 'xlim':(0,1), 'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE))}
              }


def main():
    # 1. base folder path
    path_to_base_folder = 'C:\\Users\\Shanshan\\Documents\\WP1_results\\WP1_results_1130\\'

    # 2. folders to compare
    # setting for figure in paper
    run_folders_to_compare = {
                            'HCS_base_coil': 'run_013_RET_B005_1_168',
                            'HCS_base_ER0': 'run_013_RET_B005_1_168',
                            'HCS_base_3for2': 'run_013_RET_B005_1_168',
                            'HCS_base_IEHX': 'run_013_RET_B005_1_168',
                          }

    ## collect data and paths
    paths_to_model_folder, annual_ratio_increase_dict, T_max_dict, T_ref_dict = {}, {}, {}, {}

    path_to_ref_run_folder = os.path.join('', *[path_to_base_folder, 'HCS_base', 'run_013_RET_B005_1_168'])
    path_to_ref_total_csv = [path_to_ref_run_folder, 'total.csv']
    total_df = pd.read_csv(os.path.join('', *path_to_ref_total_csv), usecols=['exergy_kWh', 'Af_m2'])
    exergy_ref_df = total_df.filter(like='exergy_kWh')
    Af_m2 = total_df.loc[0, 'Af_m2']
    annual_exergy_ref_kWh_m2 = round((exergy_ref_df.values.sum()) * 52 / Af_m2, 1)

    for tech in run_folders_to_compare.keys():
        run_folder = run_folders_to_compare[tech]
        path_to_run_folder = os.path.join('', *[path_to_base_folder, tech, run_folder])
        model_folder = [path_to_base_folder, tech, run_folder, 's_001\\plots\\icc\\models']
        paths_to_model_folder[tech] = os.path.join('', *model_folder)
        annual_ratio_increase_dict[tech] = calc_annual_exergy(annual_exergy_ref_kWh_m2, path_to_base_folder, run_folder, tech, Af_m2)
        T_max_dict[tech] = calc_T_max(path_to_run_folder)
        T_ref_dict[tech] = calc_T_ref(path_to_run_folder)

    ## plotting
    for t in [85]:
        line_types = ['base'] # 'base', 'separated'
        exergy_ref_Wh_m2 = round(exergy_ref_df.iloc[t-1]['exergy_kWh'] * 1000 / Af_m2,2)
        plot_carnot_from_icc_txt_techs(paths_to_model_folder, t, T_ref_dict, line_types, 'icc', 'all_chillers',
                                       annual_ratio_increase_dict, exergy_ref_Wh_m2, annual_exergy_ref_kWh_m2, Af_m2)





##===================
## plotting scripts
##===================

def plot_carnot_from_icc_txt_techs(paths, t, T_ref_dict, line_types, plot_type, txt_name,
                                   annual_ratio_increase_dict, exergy_ref_Wh_m2, annual_exergy_ref_kWh_m2, Af_m2):
    """
    plot icc from txt with both carnot and temperature axis
    :param paths:
    :param t:
    :param T_ref_dict:
    :param line_types:
    :param plot_type:
    :param txt_name:
    :return:
    """
    case = 'B005'
    # figure size
    fig1 = plt.figure(figsize=(3.346, 3.346))
    ax1 = plt.subplot()
    # initialize table
    table_data = {}

    # plot the lines
    # for tech in paths.keys():
    for tech in ['HCS_base_coil', 'HCS_base_ER0', 'HCS_base_3for2', 'HCS_base_IEHX']:
        path = paths[tech]
        T_ref = T_ref_dict[tech][t - 1]
        for line_type in line_types:
            print(path)
            if case == '':
                case = 'B' + path.split('run_')[1].split('_B')[0]
            x, y = load_data_from_txt(path, plot_type, line_type, txt_name, t)
            # plot x,y
            y_carnot = np.vectorize(calc_carnot_factor)(T_ref, y + 273.15)
            ax1.plot(x, y_carnot, '-', color=COLOR_CODES[tech], label=CONFIG_TABLE[tech])
            # fill area
            y_origin = np.zeros(len(y))
            ax1.fill_between(x, y_carnot, y_origin, facecolor=COLOR_CODES[tech], alpha=0.4)
            # calculate exergy
            area = np.round(np.trapz(y_carnot, x))
            exergy_Wh_m2 = np.round(area*1000/Af_m2,2)
            ratio_increase = (exergy_Wh_m2 - exergy_ref_Wh_m2) / exergy_ref_Wh_m2
            table_data[tech] = '+ {:.0%}'.format(ratio_increase)

    ## add legend
    ax1.legend(bbox_to_anchor=[0.03, 0.03], loc='lower left', fontsize=8, frameon=False)
    # ax1.legend(bbox_to_anchor=[0.02, -0.54], loc='lower left', fontsize=8, frameon=False,
    #            columnspacing=0.8, labelspacing=0.4, handletextpad=0.5)

    ## build second y-axis (Temperature)
    ax2 = ax1.twinx()
    ax2.set(ylim=calc_T_from_carnot(T_ref, Y_CARNOT_RANGE))
    ax2.set_ylabel(ylabel=u'Temperature [\u00B0C]', fontsize=8, fontname='Times New Roman', fontweight='normal')

    ## exergy table
    # input data of exergy table in the right order
    table_rows = [[exergy_ref_Wh_m2, annual_exergy_ref_kWh_m2]]
    row_labels = ['Ref.']
    for tech in ['HCS_base_coil', 'HCS_base_ER0', 'HCS_base_3for2', 'HCS_base_IEHX']:
        table_rows.append([table_data[tech], annual_ratio_increase_dict[tech]])
        row_labels.append(CONFIG_TABLE[tech])

    # make exergy table
    col_widths = [0.3]
    bbox_width = sum(col_widths)
    col_labels = ['1 p.m.\n[Wh/m2]','annual\n[kWh/m2/yr]']
    table = plt.table(cellText=table_rows, cellLoc='center', colLabels=col_labels, rowLabels=row_labels,
                      bbox=[0.22, -0.6, bbox_width * 2, 0.4],) # [x,y,width,height])
    table.scale(1, 1)
    ax1.text(820, -0.118, 'Exergy Requirement', horizontalalignment='left', fontsize=8, fontweight='bold',
             bbox={'edgecolor': 'none', 'facecolor': '#586748','alpha': 0.01, 'pad': 1})
    set_table_fontsize(table, 8)
    set_table_row_height(table, col_labels, 0.34, table_rows, 0.2)
    # set_table_linewidth(table, 2)  # if remove line: 0, if default: comment out

    ## save the figure
    # ax1.set_title('t = ' + str(t), fontdict={'fontsize': 8, 'fontweight': 'medium'}, pad=20)
    set_plot_parameters(ax1, PLOT_SPECS['carnot'])
    ax1.set(xlim=(0,2500)) #TODO: force use

    ax1.tick_params(direction='in', width=2, length=3) #unit in points
    ax2.tick_params(direction='in', width=2, length=3)
    # fig1 = plt.gcf()
    os.chdir("..\\"*6)
    fig_name = case + '_carnot' + '_techs_' + str(t) + '_exergy_icc.png'
    # fig1.tight_layout()
    # set_size(2.7, 2.7, ax1)
    fig1.savefig(fig_name, transparent=True, bbox_inches='tight', dpi=300)
    print(fig_name, 'saved to...', os.path.abspath(os.curdir))
    return


def set_table_row_height(table, col_labels, title_height, table_rows, row_height):
    cellDict = table.get_celld()
    for i in range(0, len(col_labels)):
        cellDict[(0, i)].set_height(title_height)   # header
        for j in range(1, len(table_rows) + 1):
            cellDict[(j, i)].set_height(row_height)  # data
    for k in range(1, len(table_rows) + 1): # row label
        cellDict[(k, -1)].set_height(row_height)


##===================
## general functions
##===================

def calc_carnot_factor(T_ref, T):
    """
    calculates carnot factor using the reference temperature.
    :param T_ref: temperature of the reference environment
    :param T: temperature of interest
    :return:
    """
    carnot = 1 - T_ref/T
    return carnot

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

def calc_T_max(path_to_run_folder):
    """
    Calculates the maximum temperature of all streams.
    :param path_to_folder: string
    :return: list
    """
    # get streams_df
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

def calc_annual_exergy(annual_exergy_ref_kWh_m2, path_to_base_folder, run_folder, tech, Af_m2):
    # get total exergy
    path_to_total_csv = [path_to_base_folder, tech, run_folder, 'total.csv']
    exergy_df = pd.read_csv(os.path.join('', *path_to_total_csv), usecols=['exergy_kWh'])
    annual_exergy_kWh_m2 = round((exergy_df.values.sum()) * 52 / Af_m2, 1)
    ratio_increase = (annual_exergy_kWh_m2 - annual_exergy_ref_kWh_m2) / (annual_exergy_kWh_m2)
    return '+ {:.0%}'.format(ratio_increase)


#=============
## matplotlib
#=============

#  Returns tuple of handles, labels for axis ax, after reordering them to conform to the label order `order`, and if unique is True, after removing entries with duplicate labels.
def reorderLegend(ax=None,order=None,unique=False):
    # Conflicting with other legend settings, not in use.
    if ax is None: ax=plt.gca()
    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0])) # sort both labels and handles by labels
    if order is not None: # Sort according to a given list (not necessarily complete)
        keys=dict(zip(order,range(len(order))))
        labels, handles = zip(*sorted(zip(labels, handles), key=lambda t,keys=keys: keys.get(t[0],np.inf)))
    if unique:  labels, handles= zip(*unique_everseen(zip(labels,handles), key = labels)) # Keep only the first of each handle
    ax.legend(handles, labels)
    return(handles, labels)


def unique_everseen(seq, key=None):
    seen = set()
    seen_add = seen.add
    return [x for x,k in zip(seq,key) if not (k in seen or seen_add(k))]

def set_size(w,h, ax=None):
    """ w, h: width, height in inches """
    if not ax: ax=plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w)/(r-l)
    figh = float(h)/(t-b)
    ax.figure.set_size_inches(figw, figh)

def set_table_fontsize(table, font_size):
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)

def set_table_linewidth(table, line_width):
    for key, cell in table.get_celld().items():
        cell.set_linewidth(line_width)


if __name__ == '__main__':
    main()