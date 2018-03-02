"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO

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
    traces_graph, ranges = calc_graph(data)

    # CALCULATE TABLE
    traces_table = calc_table(data)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, legend=dict(orientation="v", x=0.8, y=0.7), title=title,
                       xaxis=dict(title='Annualized Costs [$ Mio/yr]', domain=[0, 1], range=ranges[0]),
                       yaxis=dict(title='GHG emissions [x 10^3 ton CO2-eq]', domain=[0.0, 0.7], range=ranges[1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(data):
    xs = data['population']['costs_Mio'].values
    ys = data['population']['emissions_ton'].values
    zs = data['population']['prim_energy_GJ'].values

    xmin = min(xs)
    ymin = min(ys)
    zmin = min(zs)
    xmax = max(xs)
    ymax = max(ys)
    zmax = max(zs)

    ranges = [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
    ranges_some_room_for_graph = [[xmin - ((xmax - xmin) * 0.1), xmax + ((xmax - xmin) * 0.1)],
                                  [ymin - ((ymax - ymin) * 0.1), ymax + ((ymax - ymin) * 0.1)], [zmin, zmax]]

    graph = []
    individual_names = ['ind' + str(i) for i in range(len(xs))]
    trace = go.Scatter(x=xs, y=ys, mode='markers', name='data', text=individual_names,
                       marker=dict(size='12', color=zs,  # set color equal to a variable
                                   colorbar=go.ColorBar(title='Primary Energy [x 10^3 GJ]',
                                                        titleside='bottom'), colorscale='Viridis', showscale=True,
                                   opacity=0.8))
    graph.append(trace)

    # insert polynomial
    sorted_values = sorted(xs)
    z = np.polyfit(xs, ys, 3)
    f = np.poly1d(z)
    x_new = np.linspace(sorted_values[0], sorted_values[-1], 50)
    y_new = f(x_new)
    graph.append(go.Scatter(x=x_new, y=y_new, mode='lines', name='Fit X vs Y', line=dict(
        color='black')))

    return graph, ranges_some_room_for_graph


def calc_table(data):
    names = ['Individual ID', 'Annualized Costs [$ Mio/yr]', 'GHG emissions [x 10^3 ton CO2-eq]',
             'Primary Energy [x 10^3 GJ]']
    xs = data['population']['costs_Mio'].values
    ys = data['population']['emissions_ton'].values
    zs = data['population']['prim_energy_GJ'].values
    least_CO2, least_cost, least_prim = calc_individual_values(xs, ys, zs)

    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                     header=dict(
                         values=['', 'Least Cost Individual', 'Least CO2 Individual',
                                 'Least Primary Energy Individual']),
                     cells=dict(values=[names, least_cost, least_CO2, least_prim]))
    return table


def calc_individual_values(x, y, z):
    # create dataframe to look up in it
    individual_names = ['ind' + str(i) for i in range(len(x))]
    df = pd.DataFrame({'x': x, 'y': y, 'z': z, 'ind': individual_names})

    index_min_x = df.sort_values(by='x', ascending=True).x.idxmin(axis=0, skipna=True)
    index_min_y = df.sort_values(by='y', ascending=True).y.idxmin(axis=0, skipna=True)
    index_min_z = df.sort_values(by='z', ascending=True).z.idxmin(axis=0, skipna=True)

    least_cost = [df.loc[index_min_x, 'ind'], df.loc[index_min_x, 'x'], df.loc[index_min_x, 'y'],
                  df.loc[index_min_x, 'z']]
    least_CO2 = [df.loc[index_min_y, 'ind'], df.loc[index_min_y, 'x'], df.loc[index_min_y, 'y'],
                 df.loc[index_min_y, 'z']]
    least_prim = [df.loc[index_min_z, 'ind'], df.loc[index_min_z, 'x'], df.loc[index_min_z, 'y'],
                  df.loc[index_min_z, 'z']]

    return least_CO2, least_cost, least_prim
