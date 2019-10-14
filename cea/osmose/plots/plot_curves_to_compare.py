# import packages
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters

rcParams['mathtext.default'] = 'regular'


COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}
COLOR_LIST = ['#C96A50', '#3E9AA3', '#E2B43F', '#346830', '#51443D', '#6245A3', '#707070']  # Organic Forest Logo Color Palette
COLOR_CODES = {'HCS_base_3for2': '#C96A50', 'HCS_base_coil': '#3E9AA3', 'HCS_base_ER0': '#E2B43F',
               'HCS_base_IEHX': '#51443D', 'HCS_base_LD': '#6245A3',
               'HCS_base': '#707070'}
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(280,305)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]'}}
KEY_TABLE = {'BATCH2': 'no heatpipe', 'BATCH3': 'with heatpipe',
             'HCS_base_ER0': 'HCS_ER0', 'HCS_base_coil': 'HCS_coil', 'HCS_base_3for2': 'HCS_3for2',
             'HCS_base_IEHX': 'HCS_IEHX', 'HCS_base_LD': 'HCS_LD', 'HCS_base': 'HCS_base'}
DT_DICT = {'HCS_base_ER0': 0, 'HCS_base_coil': -1, 'HCS_base_3for2': 0,
           'HCS_base_IEHX': 0, 'HCS_base_LD': 0, 'HCS_base': -1}

def plot_multiple_techs(paths, t, plot_type, line_type, model_name):
    # figure size50
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()

    # plot the lines
    c = 0
    for key in paths.keys():
        path = paths[key]
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        if 'HCS' in key:
            color = COLOR_CODES[key]
            dT = DT_DICT[key]
        else:
            color = COLOR_LIST[c]
            dT = 0
        ax1.plot(x, y - dT, '-', color=color, label=KEY_TABLE[key])
        c += 1

    # save the figure
    ax1.set_title('t = '+str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'})
    set_plot_parameters(ax1, PLOT_SPECS[plot_type])
    fig1 = plt.gcf()
    os.chdir("..\\"*7)
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig(plot_type + '_' + model_name + '_t' + str(t) + '.png', transparent=True)
    return


def main():

    # get paths
    paths = {}
    ## Different techs
    main_folder = 'E:\\HCS_results_1008\\WTP_CBD_m_WP1_OFF\\B005_1_24'
    base_folder_layers = [main_folder, 'BATCH1', 'HCS_base',
                            'run_001_OFF_B005_1_24',
                            's_001', 'plots',
                            'icc', 'models']
    paths['HCS_base'] = os.path.join('', *base_folder_layers)
    # for tech in ['HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']:
    for tech in ['HCS_base_coil']:
        common_folder_layers = ['E:\\HCS_results_1008\\WTP_CBD_m_WP1_OFF\\B005_1_24\\BATCH2', tech,
                                'run_001_OFF_B005_1_24',
                                's_001', 'plots',
                                'icc', 'models']
        paths[tech] = os.path.join('', *common_folder_layers)

    ## Different batches
    # for batch in ['BATCH2', 'BATCH3']:
    #     building_use = 'OFF'
    #     common_folder_layers = ['E:\\HCS_results_1008\\WTP_CBD_m_WP1_'+building_use+'\\B005_1_24\\', batch, 'HCS_base_coil',
    #                             'run_001_'+building_use+'_B005_1_24',
    #                             's_001', 'plots',
    #                             'icc', 'models']
    #     paths[batch] = os.path.join('', *common_folder_layers)


    # plot specifications
    plot_type = 'icc'
    model_name = 'all_chillers'
    line_type = 'base' # 'base' or 'separated'

    # plot
    for t in np.arange(1,25,1):
        plot_multiple_techs(paths, t, plot_type, line_type, model_name)

    # plot_multiple_techs(paths, 5, plot_type, line_type, model_name)


if __name__ == '__main__':
    main()