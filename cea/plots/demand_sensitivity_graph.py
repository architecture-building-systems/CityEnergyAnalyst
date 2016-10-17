# -*- coding: utf-8 -*-
"""
===========================
Dynamic demand graphs algorithm
===========================
J. Fonseca  script development          25.08.15

"""
from __future__ import division

import pandas as pd

from plotly.offline import plot
import plotly.graph_objs as go
from plotly import tools


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def graph(locator, parameters, type):

    # create figure in plotlib with subplots

    if type is 'heatmap':
        heatmap(parameters, locator)
    else:
        bubbles(parameters, locator)

def bubbles2(parameters, locator):

    for parameter in parameters:
        #read the mustar of morris analysis
        data = pd.read_excel(locator.get_sensitivity_output(), parameter+'mu')
        var_names = data.columns.values

        #notmalize to max
        data[var_names] = data[var_names].div(data[var_names].max(axis=1), axis=0)*1000
        # print each diagram
        y = ['opt '+str(x) for x in list(data.index+1)]
        x = list(data.columns)

        counter2 = 0
        traces = []
        for index, datarow in data.iterrows():
            z = list(datarow)
            print z
            y_trace = [y[counter2]]*len(z)
            traces.append(go.Scatter(x =x, y= y_trace, mode='markers',
                                     marker = dict(size=z, sizeref=0.1, sizemode='area',
                                                   colorscale='Viridis', showscale= True)))
            counter2 +=1
        print 'end'
        plot(traces, auto_open=False, filename=locator.get_sensitivity_plots_file(parameter))

def bubbles(parameters, locator):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Ellipse
    from matplotlib import cm
    import numpy as np

    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.collections import EllipseCollection

    for parameter in parameters:
        #read the mustar of morris analysis
        data_mu = pd.read_excel(locator.get_sensitivity_output(), parameter+'mu')
        data_sigma = pd.read_excel(locator.get_sensitivity_output(), parameter + 's')
        var_names = data_mu.columns.values

        # normalize data to maximum value
        data_mu[var_names] = data_mu[var_names].div(data_mu[var_names].max(axis=1), axis=0)
        data_sigma[var_names] = data_sigma[var_names].div(data_sigma[var_names].max(axis=1), axis=0)
        # get x_names and y_names
        # columns
        x_names = data_mu.columns.tolist()
        # rows
        y_names = ['opt '+str(i) for i in list(data_mu.index+1)]

        # get counter (integer to create the graph)
        x = range(len(x_names))
        y = range(len (y_names))

        X, Y = np.meshgrid(x,y)
        XY = np.hstack((X.ravel()[:, np.newaxis], Y.ravel()[:, np.newaxis]))
        ww = data_mu.values.tolist()
        hh = data_sigma.values.tolist()
        aa = X*0

        fig, ax = plt.subplots()
        ec = EllipseCollection(ww, hh, aa, units='x', offsets=XY, transOffset=ax.transData)
        ec.set_array(np.array(ww).ravel())
        ec.set_alpha(0.9)
        ax.add_collection(ec)
        ax.autoscale_view()
        plt.xticks(np.arange(-1, max(x) + 1, 1.0))
        plt.yticks(np.arange(-1, max(y) + 1, 1.0))
        ax.set_xlabel('variables')
        ax.set_ylabel('configurations')
        ax.set_xticklabels([""]+x_names)
        ax.set_yticklabels([""]+y_names)
        cbar = plt.colorbar(ec)
        cbar.set_label('mu_star')
        plt.show()

        # #get ellipses
        # ells = [Ellipse(xy=(i,j), width=data_mu.ix[j, i], height=data_sigma.ix[j, i], angle=0) for i in x for j in y]
        # fig = plt.figure(0)
        # ax = fig.add_subplot(111, aspect='equal')
        # for e in ells:
        #     ax.add_artist(e)
        #     e.set_clip_box(ax.bbox)
        #     e.set_linewidth(1)
        #
        #     if e.width > 0.8:
        #         e.set_alpha(1)
        #     elif 0.6 < e.width <= 0.8:
        #         e.set_alpha(0.8)
        #     elif 0.4 < e.width <= 0.6:
        #         e.set_alpha(0.6)
        #     elif 0.2 < e.width <= 0.4:
        #         e.set_alpha(0.4)
        #     else:
        #         e.set_alpha(0.2)
        #
        # ax.set_xlim(-1, len(x_names))
        # ax.set_ylim(-1, len(y_names))
        # ax.set_xlabel('Variables')
        # ax.set_ylabel('Configuration')
        #
        # plt.show()

def heatmap(parameters, locator):
    for parameter in parameters:
        traces = []

        #read the mustar of morris analysis
        data = pd.read_excel(locator.get_sensitivity_output(), parameter+'mu')
        var_names = data.columns.values

        #notmalize to max
        data[var_names] = data[var_names].div(data[var_names].max(axis=1), axis=0)

        # print each diagram
        y = ['opt '+str(x) for x in list(data.index+1)]
        x = list(data.columns)
        matrix = data.values.tolist()

        traces.append(go.Heatmap(z = matrix, x =x, y=y, colorscale = 'Viridis'))

        plot(traces, auto_open=False, filename=locator.get_sensitivity_plots_file(parameter))

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Ef0_kW', 'QHf0_kW', 'QCf0_kW']
    type = 'bubbles'  # heatmap of bubbles
    graph(locator, output_parameters, type)

if __name__ == '__main__':
    run_as_script()