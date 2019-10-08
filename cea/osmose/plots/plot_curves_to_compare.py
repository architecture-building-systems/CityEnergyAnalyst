# import packages
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters

rcParams['mathtext.default'] = 'regular'


COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}
COLOR_LIST = ['#f9c233', '#705860', sns.xkcd_rgb["pale red"], '#346830']  # Organic Forest Logo Color Palette
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat Load [kW]', 'ylim':(273,350)},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat Load [kW]'}}


def plot_multiple_techs(paths, t, plot_type, line_type, model_name):
    # figure size50
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()

    # plot the lines
    c = 0
    for tech in paths.keys():
        path = paths[tech]
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        ax1.plot(x, y, '-', color=COLOR_LIST[c], label=tech)
        c += 1

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS[plot_type])
    fig1 = plt.gcf()
    os.chdir("..\\"*6)
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.savefig(plot_type + '_' + model_name + '_t' + str(t) + '.png', transparent=True)
    return


def main():

    # get paths
    paths = {}
    for tech in ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2']:
        common_folder_layers = ['E:\\ipese_new\\osmose_mk\\results', tech,
                                'run_003_OFF_B005_1_24',
                                's_001', 'plots',
                                'icc', 'models']
        paths[tech] = os.path.join('', *common_folder_layers)

    # plot specifications
    plot_type = 'icc'
    model_name = 'all_chillers'
    line_type = 'base' # 'base' or 'separated'

    # plot
    for t in np.arange(1,25,1):
        plot_multiple_techs(paths, t, plot_type, line_type, model_name)



if __name__ == '__main__':
    main()