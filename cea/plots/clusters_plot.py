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

def clusters_day_mean(input_path, output_path, labelx, labely, save_to_disc, show_in_screen ,show_legend):

    data = pd.read_csv(input_path)

    #create figure
    fig = plt.figure()
    ax = data.plot(grid=True, legend=show_legend)
    ax.set_xlabel(labelx)
    ax.set_ylabel(labely)
    if show_legend:
        ax.legend(loc='best', prop={'size':12})

    # get formatting
    plt.rcParams.update({'font.size': 24})
    plt.tight_layout()
    if save_to_disc:
        plt.savefig(output_path)
    if show_in_screen:
        plt.show()
    plt.close(fig)