# -*- coding: utf-8 -*-
"""
Graphs for sensitivity_demand.py
"""
from __future__ import division

import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import EllipseCollection
from matplotlib.backends.backend_pdf import PdfPages


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def graph(locator, parameters, method, samples):
    """

    :param locator: locator class
    :param parameters: list of output parameters to analyse
    :param method: 'morris' or 'sobol' methods
    :param samples: number of samples to calculate
    :return: .pdf file per output_parameter stored in locator.get_sensitivity_plots_file()

    """
    if method is 'sobol':
        result = ['ST', 'ST_conf', 'S1']
    else:
        result = ['mu_star', 'sigma', 'mu_star_conf']

    for parameter in parameters:
        pdf = PdfPages(locator.get_sensitivity_plots_file(parameter))

        # read the mustar of morris analysis
        data_mu = pd.read_excel(locator.get_sensitivity_output(method, samples), (parameter + result[0]))
        data_sigma = pd.read_excel(locator.get_sensitivity_output(method, samples), (parameter + result[1]))
        var_names = data_mu.columns.values

        # normalize data to maximum value
        data_mu[var_names] = data_mu[var_names].div(data_mu[var_names].max(axis=1), axis=0)
        data_sigma[var_names] = data_sigma[var_names].div(data_sigma[var_names].max(axis=1), axis=0)
        # get x_names and y_names
        # columns
        x_names = data_mu.columns.tolist()
        # rows
        y_names = ['config '+str(i) for i in list(data_mu.index+1)]

        # get counter (integer to create the graph)
        x = range(len(x_names))
        y = range(len (y_names))

        X, Y = np.meshgrid(x,y)
        XY = np.hstack((X.ravel()[:, np.newaxis], Y.ravel()[:, np.newaxis]))
        ww = data_mu.values.tolist()
        hh = data_sigma.values.tolist()
        aa = X*0

        fig, ax = plt.subplots(dpi=150, figsize=(len(x_names)+2, len(y_names)+2)) #
        ec = EllipseCollection(ww, hh, aa, units='x', offsets=XY, transOffset=ax.transData, cmap='Blues')
        ec.set_array(np.array(ww).ravel())
        ec.set_alpha(0.8)
        ax.add_collection(ec)
        ax.autoscale_view()
        plt.xticks(np.arange(-1, max(x) + 1, 1.0))
        plt.yticks(np.arange(-1, max(y) + 1, 1.0))
        ax.set_xlabel('variables [-]')
        ax.set_ylabel('configurations [-]')
        ax.set_xticklabels([""]+x_names)
        ax.set_yticklabels([""]+y_names)
        cbar = plt.colorbar(ec)
        cbar.set_label(result[0])
        plt.title('GRAPH OF '+parameter+' PARAMETER', fontsize=14, fontstyle='italic', fontweight='bold')
        pdf.savefig()
        plt.close()
        plt.clf()
        pdf.close()

def run_as_script():
    import cea.globalvar
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'QEf_MWhyr']
    method = 'sobol' # method
    samples = 1000
    graph(locator, output_parameters, method, samples)

if __name__ == '__main__':
    run_as_script()