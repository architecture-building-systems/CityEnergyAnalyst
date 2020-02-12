import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.plot_curves_from_osmose_outputs import load_data_from_txt, set_plot_parameters
from cea.osmose.plots.plot_carnot_from_icc import calc_T_from_carnot, calc_T_ref, calc_carnot_factor

rcParams['mathtext.default'] = 'regular'
COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}

Y_CARNOT_RANGE = [0.0, -0.1]
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat [kW]', 'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE)),
                     'xlim':(-200,1600), 'ylabel':'Carnot factor [-]', 'xlabel':'Heat [kW]'},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat [kW]'}}


def plot_loc2_to_loc3(path, t, plot_type, T_ref):
    T_ref_t = T_ref[t-1]
    # figure size
    plt.figure(figsize=(8, 7))
    ax1 = plt.subplot()
    # plot the loc2
    line_types = ['separated']
    model_name = 'loc2'
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref_t, y + 273.15)
        ax1.plot(x*(-1), y_carnot, '-', color='#707070', label=line_type, linestyle='--')

    # plot the loc3
    line_types = ['separated']
    model_name = 'loc3'
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref_t, y + 273.15)
        ax1.plot(x, y_carnot, '-', color='#707070', label=line_type)

    # build second y-axis (Temperature)
    ax2 = ax1.twinx()
    ax2.set(ylim=calc_T_from_carnot(T_ref[t-1],Y_CARNOT_RANGE))
    ax2.set_ylabel(ylabel='Temperature [C]' , fontsize=24, fontname = 'Times New Roman', fontweight='normal')

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS[plot_type])
    ax1.set_title('t = ' + str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'}, pad=20)
    fig1 = plt.gcf()
    os.chdir("..\\")
    print('saving fig to...', os.path.abspath(os.curdir))
    fig1.tight_layout()
    fig1.savefig(plot_type + '_loc2_to_loc3_t' + str(t) + '_DefaultHeatCascade.png', transparent=True)
    return




def main():
    plot_type = 'icc'
    base_folder_path = 'C:\\Users\\Shanshan\\Documents\\WP1_results\\WP1_results_1130\\'
    tech = 'HCS_base_locs'
    run_folder_path = 'run_009_RET_B005_1_168'

    folder_layers = [base_folder_path, tech, run_folder_path,'s_001\\plots\\' + plot_type, 'locations']
    path_to_folder = os.path.join('', *folder_layers)

    # load temperatures
    T_ref = calc_T_ref(os.path.join('', *[base_folder_path, 'HCS_base', 'run_003_OFF_B005_1_168'])) # fixed parameters

    # plotting
    # for t in np.arange(73,73+25,1):
    for t in [85]:
        plot_loc2_to_loc3(path_to_folder, t, plot_type, T_ref)



if __name__ == '__main__':
    main()