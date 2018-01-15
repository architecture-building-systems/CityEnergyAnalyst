"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def pareto_curve(data, title, output_path):

    # CALCULATE GRAPH
    traces_graph= calc_graph(data)

    # CALCULATE TABLE
    traces_table = calc_table(data)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(title=title,xaxis=dict(title='Annualized Costs [$/yr]', domain=[0, 1]),
                       yaxis=dict(title='GHG emissions [kg CO2]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(data):

    graph = []
    xs = [objectives[0] for objectives in data['population_fitness']]
    ys = [objectives[1] for objectives in data['population_fitness']]
    zs = [objectives[2] for objectives in data['population_fitness']]
    trace = go.Scatter(x=xs, y=ys, mode = 'markers',
                       marker=dict(size='12', color=zs,  # set color equal to a variable
                        colorbar=go.ColorBar(title='Primary Energy [MJ]',
                        titleside = 'bottom'), colorscale='Viridis', showscale=True ,opacity = 0.8))
    graph.append(trace)

    return graph

def calc_table(data):

    names = ['Individual ID', 'Annualized Costs [$/yr]', 'GHG emissions [kg CO2]', 'Primary Energy [MJ]']

    least_CO2, least_cost, least_prim = calc_individual_values(data)

    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                            header=dict(
                                values=['', 'Least Cost Individual', 'Least CO2 Individual', 'Least Primary Energy Individual']),
                            cells=dict(values=[names, least_cost, least_CO2, least_prim]))
    return table


def calc_individual_values(data):
    # create dataframe to look up in it
    x = ([objectives[0] for objectives in data['population_fitness']])
    y = ([objectives[1] for objectives in data['population_fitness']])
    z = ([objectives[2] for objectives in data['population_fitness']])
    individual_names = ['ind' + str(i) for i in range(len(x))]
    df = pd.DataFrame({'x': x, 'y': y, 'z': z, 'ind': individual_names})

    index_min_x = df.sort_values(by='x', ascending=True).index[:1]

    least_cost = [df.ix[index_min_x], df.loc['x',index_min_x], df.loc['y',index_min_x], df.loc['z',index_min_x]]
    least_CO2 = [df.ix[index_min_y], df.loc['x',index_min_y], df.loc['y',index_min_y], df.loc['z',index_min_y]]
    least_prim = [df.ix[index_min_z], df.loc['x',index_min_z], df.loc['y',index_min_z], df.loc['z',index_min_z]]

    return least_CO2, least_cost, least_prim