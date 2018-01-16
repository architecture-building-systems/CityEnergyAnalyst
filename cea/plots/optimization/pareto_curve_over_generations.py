from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
from cea.plots.variable_naming import LOGO
import pandas as pd


def pareto_curve_over_generations(data, generations, title, output_path):

    # CALCULATE GRAPH
    traces_graph, range = calc_graph(data, generations)

    traces_table = calc_table(data, generations)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,
        legend=dict(orientation="v", x=0.8, y=0.7), title=title,xaxis=dict(title='Annualized Costs [$ Mio/yr]', domain=[0, 1], range = range[0]),
                       yaxis=dict(title='GHG emissions [x 10^3 ton CO2]', domain=[0.0, 0.7], range = range[1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(data, generations):

    graph = []
    x = []
    y =[]
    z = []
    for gen, df in enumerate(data):
        x.extend([round(objectives[0] / 1000000, 2) for objectives in df['population_fitness']])
        y.extend([round(objectives[1] / 1000000, 2) for objectives in df['population_fitness']])
        z.extend([round(objectives[2] / 1000000, 2) for objectives in
              df['population_fitness']])

    xmin = min(x)
    ymin = min(y)
    zmin = min(z)
    xmax = max(x)
    ymax = max(y)
    zmax = max(z)

    ranges = [[xmin, xmax], [ymin, ymax], [zmin, zmax]]

    for gen, df in enumerate(data):
        xs = [round(objectives[0] / 1000000, 2) for objectives in df['population_fitness']]  # convert to millions
        ys = [round(objectives[1] / 1000000, 2) for objectives in df['population_fitness']]  # convert to tons x 10^3
        zs = [round(objectives[2] / 1000000, 2) for objectives in
              df['population_fitness']]  # convert to gigajoules x 10^3
        individual_names = ['ind' + str(i) for i in range(len(xs))]

        trace = go.Scatter(x=xs, y=ys, name='generation ' + str(generations[gen]), text = individual_names, mode = 'markers',
                           marker=dict(
                               size='12',
                               color=zs,  # set color equal to a variable
                               colorbar=go.ColorBar(
                                   title='Primary Energy [x 10^3 GJ]',
                                   titleside = 'bottom',
                                   tickvals = ranges[2]
                               ),
                               colorscale='Viridis',
                               showscale=True,
                               opacity = 0.8
                           ))
        graph.append(trace)

    return graph, ranges

def calc_table(data, generations):

    least_cost = []
    least_CO2 = []
    least_prim = []
    for df in data:
        x = [round(objectives[0] / 1000000, 2) for objectives in df['population_fitness']]  # convert to millions
        y = [round(objectives[1] / 1000000, 2) for objectives in df['population_fitness']]  # convert to tons x 10^3
        z = [round(objectives[2] / 1000000, 2) for objectives in
              df['population_fitness']]  # convert to gigajoules x 10^3
        individual_names = ['ind' + str(i) for i in range(len(x))]
        df = pd.DataFrame({'x': x, 'y': y, 'z': z, 'ind': individual_names})

        least_cost.extend(df.sort_values(by='x', ascending=True).ind[:1])
        least_CO2.extend(df.sort_values(by='y', ascending=True).ind[:1])
        least_prim.extend(df.sort_values(by='z', ascending=True).ind[:1])

    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                            header=dict(
                                values=['Generation', 'Least Cost Individual', 'Least CO2 Individual', 'Least Primary Energy Individual']),
                            cells=dict(values=[generations, least_cost, least_CO2, least_prim]))

    return table