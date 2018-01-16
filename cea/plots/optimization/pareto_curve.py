"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
from cea.plots.variable_naming import LOGO
import pandas as pd
import numpy as np

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
    layout = go.Layout(images=[dict(
        source="https://github.com/architecture-building-systems/CityEnergyAnalyst/blob/master/cea_logo.png",
        x=0, y=0.7,
        sizex=0.2, sizey=0.2,
        xanchor="left", yanchor="bottom"
      )],legend=dict(orientation="v", x=0.8, y=0.7), title=title,xaxis=dict(title='Annualized Costs [$ Mio/yr]', domain=[0, 1]),
                       yaxis=dict(title='GHG emissions [x 10^3 ton CO2-eq]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(data):

    least_CO2, least_cost, least_prim = calc_individual_values(data)

    graph = []
    xs = [round(objectives[0]/1000000,2) for objectives in data['population_fitness']] #convert to millions
    ys = [round(objectives[1]/1000000,2) for objectives in data['population_fitness']] # convert to tons x 10^3
    zs = [round(objectives[2]/1000000,2) for objectives in data['population_fitness']] # convert to gigajoules x 10^3
    individual_names = ['ind' + str(i) for i in range(len(xs))]
    trace = go.Scatter(x=xs, y=ys, mode = 'markers', name = 'data', text=individual_names,
                       marker=dict(size='12', color=zs,  # set color equal to a variable
                        colorbar=go.ColorBar(title='Primary Energy [x 10^3 GJ]',
                        titleside = 'bottom'), colorscale='Viridis', showscale=True ,opacity = 0.8))
    graph.append(trace)

    #insert polynomial
    sorted_values = sorted(xs)
    z = np.polyfit(xs, ys, 3)
    f = np.poly1d(z)
    x_new = np.linspace(sorted_values[0], sorted_values[-1], 50)
    y_new = f(x_new)
    graph.append(go.Scatter(x=x_new, y=y_new, mode='lines', name = 'Fit', line = dict(
        color ='black')))

    return graph

def calc_table(data):

    names = ['Individual ID', 'Annualized Costs [$ Mio/yr]', 'GHG emissions [x 10^3 ton CO2-eq]', 'Primary Energy [x 10^3 GJ]']

    least_CO2, least_cost, least_prim = calc_individual_values(data)

    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                            header=dict(
                            values=['', 'Least Cost Individual', 'Least CO2 Individual', 'Least Primary Energy Individual']),
                            cells=dict(values=[names, least_cost, least_CO2, least_prim]))
    return table


def calc_individual_values(data):
    # create dataframe to look up in it
    x = [round(objectives[0]/1000000,2) for objectives in data['population_fitness']] #convert to millions
    y = [round(objectives[1]/1000000,2) for objectives in data['population_fitness']] # convert to tons x 10^3
    z = [round(objectives[2]/1000000,2) for objectives in data['population_fitness']] # convert to gigajoules x 10^3
    individual_names = ['ind' + str(i) for i in range(len(x))]
    df = pd.DataFrame({'x': x, 'y': y, 'z': z, 'ind': individual_names})

    index_min_x = df.sort_values(by='x', ascending=True).x.idxmin(axis=0, skipna=True)
    index_min_y = df.sort_values(by='y', ascending=True).y.idxmin(axis=0, skipna=True)
    index_min_z = df.sort_values(by='z', ascending=True).z.idxmin(axis=0, skipna=True)

    least_cost = [df.loc[index_min_x, 'ind'], df.loc[index_min_x, 'x'], df.loc[index_min_x, 'y'], df.loc[index_min_x, 'z']]
    least_CO2 = [df.loc[index_min_y, 'ind'], df.loc[index_min_y, 'x'], df.loc[index_min_y, 'y'], df.loc[index_min_y, 'z']]
    least_prim = [df.loc[index_min_z, 'ind'], df.loc[index_min_z, 'x'], df.loc[index_min_z, 'y'], df.loc[index_min_z, 'z']]

    return least_CO2, least_cost, least_prim