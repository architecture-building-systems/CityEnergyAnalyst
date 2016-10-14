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
    num_parameters = len(parameters)
    if num_parameters > 1:
        if 2 <= num_parameters < 4:
            rows, columns = 1, num_parameters
        elif 4 <= num_parameters < 7:
            rows, columns = 2, int(num_parameters/2)
        fig = tools.make_subplots(rows=rows, cols=columns, print_grid=False , subplot_titles=parameters)

    if type is 'heatmap':
        fig = heatmap(parameters, locator, rows, columns, fig, num_parameters)
    else:
        fig = bubbles(parameters, locator, rows, columns, fig, num_parameters)

    plot(fig, auto_open=False, filename=locator.get_sensitivity_plots_file('sensitivity_anlaysis'))


def bubbles(parameters, locator, rows, columns, fig, num_parameters):
    counter = 0
    for row in range(1, rows+1):
        for column in range(1, columns+1):
            traces = []
        for parameter in parameters:
            #read the mustar of morris analysis
            data = pd.read_excel(locator.get_sensitivity_output(), parameter+'mu')
            var_names = data.columns.values

            #notmalize to max
            data[var_names] = data[var_names].div(data[var_names].max(axis=1), axis=0)
            # print each diagram
            y = ['opt '+str(x) for x in list(data.index+1)]
            x = list(data.columns)

            counter2 = 0
            for index, datarow in data.iterrows():
                values = list(datarow)
                traces = go.Scatter(x =x, y=y[counter2], mode='markers',
                                         marker = dict(size=values, sizeref=0.2, sizemode='area',))

                fig.append_trace(traces, row, columns)
                print y[counter2], counter, counter2
                counter2 +=1

                fig['layout']['xaxis' + str(counter + 1)].update(title='Variables')
                fig['layout']['yaxis' + str(counter + 1)].update(title='Options')
            counter = +1
            if counter is num_parameters:
                break

    return fig

def heatmap(parameters, locator, rows, columns, fig, num_parameters):
    traces = []
    for parameter in parameters:
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

    # check layout
    counter = 0
    for row in range(1, rows+1):
        for column in range(1, columns+1):
            fig.append_trace(traces[counter], row, column)
            fig['layout']['xaxis'+str(counter+1)].update(title='Variables')
            fig['layout']['yaxis' + str(counter + 1)].update(title='Options')
            counter = +1
            if counter is num_parameters:
                break
    fig['layout'].update(title='sensitivity_analysis')

    return fig

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Ef0_kW', 'QHf0_kW', 'QCf0_kW']
    type = 'bubbles' # heatmpa of bubbles
    graph(locator, output_parameters, type)

if __name__ == '__main__':
    run_as_script()