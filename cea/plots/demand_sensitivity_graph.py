# -*- coding: utf-8 -*-
"""
===========================
Dynamic demand graphs algorithm
===========================
J. Fonseca  script development          25.08.15

"""
from __future__ import division

import pandas as pd

import multiprocessing as mp
from plotly.offline import plot
import plotly.graph_objs as go


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def bubble_graph(locator, parameters, gv):

    # get name of files to map
    for parameter in parameters[:2]:
        #read the mustar of morris analysis
        data = pd.read_excel(locator.get_sensitivity_output(), parameter+'mu')
        y = list(data.index+1)
        x = list(data.columns)
        # create traces
        traces = []
        counter = 0
        for index, datarows in data.iterrows():
            value = y[counter]
            size = list(datarows.values)
            traces.append(go.Scatter(x = x, y = value, mode ='markers', marker = dict(sizemode='area' , size = size, sizeref=0.2,)))
            counter += 1
        print traces
        # Plot and embed in ipython notebook!
        fig = traces
        plot(fig, auto_open=False, filename=locator.get_sensitivity_plots_file(parameter))


def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Ef0_kW', 'QHf0_kW', 'QCf0_kW']
    bubble_graph(locator, output_parameters, gv)

if __name__ == '__main__':
    run_as_script()