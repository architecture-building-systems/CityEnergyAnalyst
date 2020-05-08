import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from matplotlib import rcParams
from cea.osmose.plots.general_plotting_functions import calc_T_ref, load_data_from_txt, \
    set_plot_parameters, calc_T_from_carnot, calc_carnot_factor

rcParams['mathtext.default'] = 'regular'
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['lines.linewidth'] = 2.0
rcParams['axes.linewidth'] = 2.0
COLOR_TABLE = {'base': sns.xkcd_rgb["pale red"], 'separated': sns.xkcd_rgb["sea blue"]}

Y_CARNOT_RANGE = [0.0, -0.1]
PLOT_SPECS = {'icc':{'ylabel':'Temperature [C]', 'xlabel':'Heat [kW]', 'ylim':(min(Y_CARNOT_RANGE),max(Y_CARNOT_RANGE)),
                     'xlim':(-200,1600), 'ylabel':'Carnot factor [-]', 'xlabel':'Heat [kW]'},
              'carnot':{'ylabel':'Carnot factor [-]', 'xlabel':'Heat [kW]'}}


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


def plot_loc2_to_loc3(path, t, plot_type, T_ref):
    T_ref_t = T_ref[t-1]
    # figure size
    plt.figure(figsize=(3.346, 3.346))
    ax1 = plt.subplot()
    # plot the loc2
    line_types = ['separated']
    model_name = 'loc2'
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref_t, y + 273.15)
        x_positive = x*(-1)
        ax1.plot(x_positive[16:], y_carnot[16:], '-', color='#000000', label='SCU', linestyle='--')
        x_max_loc2 = x.min()*(-1)
        y_min_loc2 = y_carnot[16]
        ## annotation
        ax1.plot([x_max_loc2, x_max_loc2], [-0.028, -0.04], ':', color='#707070')

    # plot the loc3
    line_types = ['separated']
    model_name = 'loc3'
    for line_type in line_types:
        x, y = load_data_from_txt(path, plot_type, line_type, model_name, t)
        y_carnot = np.vectorize(calc_carnot_factor)(T_ref_t, y + 273.15)
        ax1.plot(x, y_carnot, '-', color='#000000', label='RAU + OAU')

        ## annotation
        # vertical lines
        ax1.plot([0.0, 0.0], [-0.015, -0.04], ':', color='#707070')
        ax1.plot([x.max(), x.max()], [-0.018, -0.078], ':', color='#707070')
        # recovery in RAU + OAU
        idx_xmin = np.where(x==x.min())[0][0]
        ax1.text(-15, y_carnot[idx_xmin] + 0.002, 'A', horizontalalignment='right', fontsize=8, fontweight='bold',
                 bbox={'edgecolor':'none', 'facecolor': '#51183b', 'alpha': 0.7, 'pad': 1})
        ax1.annotate("",
                    xy=(x.min() - 15, y_carnot[idx_xmin]), xycoords='data',
                    xytext=(0.0 + 15, y_carnot[idx_xmin]), textcoords='data',
                    arrowprops=dict(arrowstyle="|-|,widthA=0.2,widthB=0.2",
                                    color='#51183b',
                                    lw=2),
                    )
        # recovery between SCU and RAU + OAU
        ax1.text(180, -0.02, 'B', horizontalalignment='right', fontsize=8, fontweight='bold',
                 bbox={'edgecolor':'none', 'facecolor': '#51183b', 'alpha': 0.7, 'pad': 1})
        ax1.annotate("",
                    xy=(x.max() + 20, -0.022), xycoords='data',
                    xytext=(0.0 - 20, -0.022), textcoords='data',
                    arrowprops=dict(arrowstyle="|-|,widthA=0.2,widthB=0.2",
                                    color='#51183b',#be915c
                                    lw=2),
                    )
        # cooling load from RAU + OAU
        ax1.text(200, -0.074, 'C', horizontalalignment='right', fontsize=8, fontweight='bold',
                 bbox={'edgecolor': 'none', 'facecolor': '#586748', 'alpha': 0.7, 'pad': 1})
        ax1.annotate("",
                    xy=(x.max() + 20, y_carnot[0]), xycoords='data',
                    xytext=(x[0] - 20, y_carnot[0]), textcoords='data',
                    arrowprops=dict(arrowstyle="|-|,widthA=0.2,widthB=0.2",
                                    color='#586748',
                                    lw=2),
                    )
        # cooling load from SCU
        ax1.text(900, y_min_loc2 + 0.001, 'D', horizontalalignment='right', fontsize=8, fontweight='bold',
                 bbox={'edgecolor':'none', 'facecolor': '#586748', 'alpha': 0.7, 'pad': 1})
        ax1.annotate("",
                    xy=(x_max_loc2 + 20, y_min_loc2), xycoords='data',
                    xytext=(x.max() - 20, y_min_loc2), textcoords='data',
                    arrowprops=dict(arrowstyle="|-|,widthA=0.2,widthB=0.2",
                                    color='#586748',#50adc7
                                    lw=2),
                    )

    # text box
    textstr = '\n'.join((
        'A: Heat recovery within RAU + OAU',
        'B: Heat recovery between SCU and RAU + OAU',
        'C: Cooling load from RAU + OAU',
        'D: Cooling load from SCU'))
    props = dict(boxstyle='Square', edgecolor='none', facecolor='#cdcbcb')
    ax1.text(0.12, 0.2, textstr, transform=ax1.transAxes, fontsize=8,
             verticalalignment='top', bbox=props)

    # show legend
    ax1.legend(bbox_to_anchor=[0.55, 0.83], loc='lower left', fontsize=8, frameon=False)

    # build second y-axis (Temperature)
    ax2 = ax1.twinx()
    ax2.set(ylim=calc_T_from_carnot(T_ref[t-1],Y_CARNOT_RANGE))
    ax2.set_ylabel(ylabel=u'Temperature [\u00B0C]', fontsize=8, fontname='Times New Roman', fontweight='normal')

    # save the figure
    set_plot_parameters(ax1, PLOT_SPECS[plot_type])
    # ax1.set_title('t = ' + str(t), fontdict={'fontsize': 16, 'fontweight': 'medium'}, pad=20)  # un-comment to show timesteps
    ax1.tick_params(direction='in', width=2, length=3) #unit in points
    ax2.tick_params(direction='in', width=2, length=3)
    fig1 = plt.gcf()
    os.chdir("..\\")
    print('saving fig to...', os.path.abspath(os.curdir))
    # fig1.tight_layout()
    fig_name = plot_type + '_loc2_to_loc3_t' + str(t) + '_DefaultHeatCascade.png'
    fig1.savefig(fig_name, transparent=True, bbox_inches='tight', dpi=300)
    return


def add_interval(ax, xdata, ydata, caps="  "):
    line = ax.add_line(mpl.lines.Line2D(xdata, ydata))
    anno_args = {
        'ha': 'center',
        'va': 'center',
        'size': 8,
        'color': line.get_color(),
    }
    a0 = ax.annotate(caps[0], xy=(xdata[0], ydata[0]), **anno_args)
    a1 = ax.annotate(caps[1], xy=(xdata[1], ydata[1]), **anno_args)
    return (line,(a0,a1))





if __name__ == '__main__':
    main()