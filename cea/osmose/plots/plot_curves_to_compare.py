# import packages
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import rcParams
import matplotlib.colors as colors
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap, Normalize
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters

rcParams['mathtext.default'] = 'regular'


COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}
COLOR_LIST = ['#C96A50', '#3E9AA3', '#E2B43F', '#346830', '#51443D', '#6245A3', '#707070']  # Organic Forest Logo Color Palette
COLOR_CODES = {'HCS_base_3for2': '#C96A50', 'HCS_base_coil': '#3E9AA3', 'HCS_base_ER0': '#E2B43F',
               'HCS_base_IEHX': '#51443D', 'HCS_base_LD': '#6245A3',
               'HCS_base': '#707070'}
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(5,85)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]'}}
KEY_TABLE = {'BATCH2': 'no heatpipe', 'BATCH3': 'with heatpipe',
             'HCS_base_ER0': 'HCS_ER0', 'HCS_base_coil': 'HCS_coil', 'HCS_base_3for2': 'HCS_3for2',
             'HCS_base_IEHX': 'HCS_IEHX', 'HCS_base_LD': 'HCS_LD', 'HCS_base': 'HCS_base'}

def plot_multiple_techs(paths, t, plot_type, line_types, model_name):
    # figure size50
    # plt.figure()
    fig, ax1 = plt.subplots(figsize=(8, 7), constrained_layout=True)

    # plot the lines
    c = 0
    cmap = cm.tab20
    norm = Normalize(vmin=1, vmax=len(paths))
    label_list = []
    for key in paths.keys():
        path = paths[key]
        for line_type in line_types:
            x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
            if 'HCS' in key:
                color = COLOR_CODES[key]
            elif 'base' in line_type:
                color = '#000000'  # set base to black
            else:
                color = cmap(norm(c))
            if key in KEY_TABLE.keys():
                label = KEY_TABLE[key]
            elif key in label_list:
                label = '_nolegend_'
            else:
                label = key
                label_list.append(label)
            ax1.plot(x, y, '-', color=color, label=label)
        c += 1

    # save the figure
    ax1.set_title('t = '+str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'})
    set_plot_parameters(ax1, PLOT_SPECS[plot_type])
    # set legend location
    ncol = 1 if len(paths) <= 15 else int(len(paths)/15)
    # ax1.legend(loc='lower left', bbox_to_anchor=(1, 0), ncol=ncol)
    ax1.get_legend().remove()
    fig1 = plt.gcf()
    os.chdir("..\\"*6)
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig(plot_type + '_' + model_name + '_t' + str(t) + '.png', transparent=True)
    plt.cla()
    plt.clf()
    return


def main():

    # # get paths
    # paths = {}
    # ## Different techs
    # main_folder = 'E:\\OSMOSE_projects\\HCS_mk\\results'
    # # base_folder_layers = [main_folder, 'BATCH1', 'HCS_base',
    # #                         'run_001_OFF_B005_1_24',
    # #                         's_001', 'plots',
    # #                         'icc', 'models']
    # # paths['HCS_base'] = os.path.join('', *base_folder_layers)
    # for tech in ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']:
    # # for tech in ['HCS_base_coil']:
    #     common_folder_layers = [main_folder, tech,
    #                             'run_001_OFF_B005_1_24',
    #                             's_001', 'plots',
    #                             'icc', 'models']
    #     paths[tech] = os.path.join('', *common_folder_layers)

    ## Different batches
    # for batch in ['BATCH2', 'BATCH3']:
    #     building_use = 'OFF'
    #     common_folder_layers = ['E:\\HCS_results_1008\\WTP_CBD_m_WP1_'+building_use+'\\B005_1_24\\', batch, 'HCS_base_coil',
    #                             'run_001_'+building_use+'_B005_1_24',
    #                             's_001', 'plots',
    #                             'icc', 'models']
    #     paths[batch] = os.path.join('', *common_folder_layers)


    # # plot specifications
    # plot_type = 'icc'
    # model_name = 'all_chillers'
    # line_type = 'base' # 'base' or 'separated'
    #
    # # plot
    # for t in np.arange(1,25,1):
    #     plot_multiple_techs(paths, t, plot_type, line_type, model_name)

    # plot_multiple_techs(paths, 5, plot_type, line_type, model_name)


    ## Plot reruns from dakota ##
    # 1. Main folder
    main_folder = 'E:\\ipese_new\\osmose_mk\\results\\HCS_base_hps\\run_014_moga\\rerun'
    # 2. get paths
    paths = {}
    # runs_to_exclude = ['run_001394', 'run_001780', 'run_001822', 'run_001839',
    #                    'run_001100', 'run_001319', 'run_001713', 'run_001640', 'run_001645', 'run_001675', 'run_001676',
    #                    'run_001678', 'run_001702', 'run_001703']
    for run_folder in os.listdir(main_folder):
    # for run_folder in runs_to_exclude:
        if 'run' in run_folder:
            # if run_folder not in runs_to_exclude:
                folder_layers = [main_folder, run_folder, 's_001\\plots\\icc\\models']
                paths[run_folder] = os.path.join('', *folder_layers)
    # 3. plot
    plot_type = 'icc'
    model_name = 'hp'
    line_type = ['separated', 'base'] # 'base' or 'separated'
    t = 1
    plot_multiple_techs(paths, t, plot_type, line_type, model_name)

if __name__ == '__main__':
    main()