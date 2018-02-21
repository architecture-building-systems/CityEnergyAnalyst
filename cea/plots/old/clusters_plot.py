from __future__ import division

import matplotlib
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def plot_day(data, output_path, labelx, labely, save_to_disc, show_in_screen, show_legend):

    plt.rcParams.update({'font.size': 18})

    #create figure
    fig = plt.figure()
    ax = data.plot(grid=True, legend=show_legend)
    ax.set_xlabel(labelx)
    ax.set_ylabel(labely)
    if show_legend:
        ax.legend(loc='upper right', prop={'size':12}, ncol=2)

    # get formatting
    plt.tight_layout()
    if save_to_disc:
        plt.savefig(output_path)
    if show_in_screen:
        plt.show()
    plt.close(fig)