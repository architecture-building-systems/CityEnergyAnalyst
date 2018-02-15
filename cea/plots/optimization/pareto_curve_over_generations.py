from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO


def pareto_curve_over_generations(data, generations, title, output_path):
    # CALCULATE GRAPH
    traces_graph, range = calc_graph(data, generations)

    traces_table = calc_table(data, generations)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,
                       legend=dict(orientation="v", x=0.8, y=0.7), title=title,
                       xaxis=dict(title='Annualized Costs [$ Mio/yr]', domain=[0, 1], range=range[0]),
                       yaxis=dict(title='GHG emissions [x 10^3 ton CO2]', domain=[0.0, 0.7], range=range[1]))
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


def calc_table(data, generations):
    # least_cost = []
    # least_CO2 = []
    # least_prim = []
    individuals = []
    euclidean_distance = []
    spread = []
    for df in data:
        # x = [round(objectives[0] / 1000000, 2) for objectives in ]  # convert to millions
        # y = [round(objectives[1] / 1000000, 2) for objectives in df['population_fitness']]  # convert to tons x 10^3
        # z = [round(objectives[2] / 1000000, 2) for objectives in
        #       df['population_fitness']]  # convert to gigajoules x 10^3
        # individual_names = ['ind' + str(i) for i in range(len(x))]
        # data_clean = pd.DataFrame({'x': x, 'y': y, 'z': z, 'ind': individual_names})
        #
        # least_cost.extend(data_clean.sort_values(by='x', ascending=True).ind[:1])
        # least_CO2.extend(data_clean.sort_values(by='y', ascending=True).ind[:1])
        # least_prim.extend(data_clean.sort_values(by='z', ascending=True).ind[:1])
        individuals.append(len(df['population']))
        euclidean_distance.append(round(df['euclidean_distance'], 4))
        spread.append(round(df['spread'], 4))

    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                     header=dict(
                         values=['Generation', 'Number of Individuals', 'Euclidean distance [-]', 'Spread [-]']),
                     cells=dict(values=[generations, individuals, euclidean_distance, spread]))

    return table
