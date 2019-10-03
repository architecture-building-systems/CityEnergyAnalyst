# import packages
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.ticker as mticker
from matplotlib import gridspec
from matplotlib import rcParams

rcParams['mathtext.default'] = 'regular'

# # fix on times new roman font
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()


def plot_icc_base_and_separated(path, t, plot_type, model_name):
    os.chdir(path)
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # load data
    if model_name == '':
        file_name_base = plot_type + '_base_m_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    else:
        file_name_base = plot_type + '_base_m_' + model_name + '_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'

    data = np.genfromtxt(file_name_base, delimiter=' ')
    # x and y axes
    x = data[:, 0]
    y = data[:, 1]
    # plot the figure
    ax1.plot(x, y, '-', color=sns.xkcd_rgb["pale red"])
    # load data
    if model_name == '':
        file_name_separated = plot_type + '_separated_m_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    else:
        file_name_separated = plot_type + '_separated_m_'+ model_name +'_loc_loc1_t' + str(t) + '_c1_DefaultHeatCascade.txt'
    data = np.genfromtxt(file_name_separated, delimiter=' ')
    # x and y axes
    x = data[:, 0]
    y = data[:, 1]
    # plot the figure
    ax1.plot(x, y, '-', color=sns.xkcd_rgb["sea blue"])
    # set the legend
    ax1.legend(["base", "separated", ],
               loc='upper right', shadow=False, fancybox=True,
               fontsize=18, prop={'family': 'Times New Roman', 'size': '18'})
    # set x and y range
    # plt.set_xlim([-766.00311044128,8090.8964687342])
    # plt.set_ylim([-70.151355125,914.40992288125])
    # format ticks
    plt.xticks(fontname='Times New Roman', fontsize=18)
    plt.yticks(fontname='Times New Roman', fontsize=18)
    for label in ax1.xaxis.get_majorticklabels():
        label.set_fontsize(18)
        label.set_fontname('Times New Roman')
    for label in ax1.yaxis.get_majorticklabels():
        label.set_fontsize(18)
        label.set_fontname('Times New Roman')
    # set the axis labels
    ax1.set_ylabel('Temperature [C]', fontsize=20, color='black', fontname='Times New Roman', fontweight='normal')
    ax1.set_xlabel('Heat Load [kW]', fontsize=20, color='black', fontname='Times New Roman', fontweight='normal')
    # tight layout prevents axis title overlapping
    plt.tight_layout(pad=1, w_pad=3, h_pad=1.0)
    # show the figure and hold it for saving
    # plt.show(block=False)
    # save the figure
    fig1 = plt.gcf()
    plt.draw()
    fig1.savefig(plot_type + '_' + model_name + '_t' + str(t) + '_Clu_DefaultHeatCascade.png', transparent=True)




def main():
    plot_type = 'carnot'
    model_name = ''
    folder = 'air_systems'
    # change directory
    path_to_scenario = 'E:\\ipese_new\\osmose_mk\\results\\HCS_base\\run_001\\s_001'
    path_to_models = path_to_scenario + '\\plots\\' + plot_type + '\\' + folder


    for t in np.arange(1,25,1):
        plot_icc_base_and_separated(path_to_models, t, plot_type, model_name)



if __name__ == '__main__':
    main()