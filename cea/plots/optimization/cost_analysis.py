from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def cost_analysis(data, generations, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(data, generations)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = go.Layout(images=LOGO, title=title, barmode='relative',
                       yaxis=dict(title='Power Generated [MWh]', domain=[0.0, 1.0]))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(data, generations):
    graph = []
    x = []
    y = []
    z = []
    for df in data:
        x.extend(df['population']['costs_Mio'].values)
        x.extend(df['halloffame']['costs_Mio'].values)
        y.extend(df['population']['emissions_ton'].values)
        y.extend(df['halloffame']['emissions_ton'].values)
        z.extend(df['population']['prim_energy_GJ'].values)
        z.extend(df['halloffame']['prim_energy_GJ'].values)

    xmin = min(x)
    ymin = min(y)
    zmin = min(z)
    xmax = max(x)
    ymax = max(y)
    zmax = max(z)

    ranges = [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
    ranges_some_room_for_graph = [[xmin - ((xmax - xmin) * 0.1), xmax + ((xmax - xmin) * 0.1)],
                                  [ymin - ((ymax - ymin) * 0.1), ymax + ((ymax - ymin) * 0.1)], [zmin, zmax]]

    for gen, df in enumerate(data):
        xs = df['population']['costs_Mio'].values
        ys = df['population']['emissions_ton'].values
        zs = df['population']['prim_energy_GJ'].values
        individual_names = ['ind' + str(i) for i in range(len(xs))]
        trace = go.Scatter(x=xs, y=ys, name='generation ' + str(generations[gen]), text=individual_names,
                           mode='markers',
                           marker=dict(
                               size='12',
                               color=zs,  # set color equal to a variable
                               colorbar=go.ColorBar(
                                   title='Primary Energy [x 10^3 GJ]',
                                   titleside='bottom',
                                   tickvals=ranges[2]
                               ),
                               colorscale='Viridis',
                               showscale=True,
                               opacity=0.8
                           ))
        graph.append(trace)

    # add hall of fame
    x_hall = df['halloffame']['costs_Mio'].values
    y_hall = df['halloffame']['emissions_ton'].values
    z_hall = df['halloffame']['prim_energy_GJ'].values
    individual_names = ['ind' + str(i) for i in range(len(x_hall))]
    trace = go.Scatter(x=x_hall, y=y_hall, name='hall of fame', text=individual_names, mode='markers',
                       marker=dict(
                           size='12',
                           color=z_hall,  # set color equal to a variable
                           colorbar=go.ColorBar(
                               title='Primary Energy [x 10^3 GJ]',
                               titleside='bottom',
                               tickvals=ranges[2]
                           ),
                           colorscale='Viridis',
                           showscale=True,
                           opacity=0.8
                       ))
    graph.append(trace)

    return graph, ranges_some_room_for_graph
