"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import numpy as np
import pandas as pd
import json
import cea.config
import cea.inputlocator
from cea.plots.building.energy_use_intensity import energy_use_intensity_district
from cea.plots.building.load_curve import load_curve
from cea.plots.building.load_duration_curve import load_duration_curve
from cea.plots.building.peak_load import peak_load_district
from cea.plots.district.energy_demand import energy_demand_district
from cea.utilities import epwreader
import plotly.graph_objs as go
from plotly.offline import plot
from cea.plots.variable_naming import NAMING
import pandas as pd
from cea.plots.optimization.pareto_curve import pareto_curve

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def pareto_curve_over_generations(data, generations, title, output_path):

    # CALCULATE GRAPH
    traces_graph, range = calc_graph(data, generations)

    traces_table = calc_table(data, generations)



    #PLOT GRAPH

    traces_graph.append(traces_table)
    layout = go.Layout(title=title,xaxis=dict(title='Annualized Costs [$/yr]', domain=[0, 1], range = range[0]),
                       yaxis=dict(title='GHG emissions [kg CO2]', domain=[0.0, 0.7], range = range[1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(data, generations):

    graph = []
    x = []
    y =[]
    z = []
    xmin = []
    ymin = []
    zmin = []
    xmax = []
    ymax = []
    zmax = []

    for gen, df in enumerate(data):
        x.extend([objectives[0] for objectives in df['population_fitness']])
        y.extend([objectives[1] for objectives in df['population_fitness']])
        z.extend([objectives[2] for objectives in df['population_fitness']])

    xmin = min(x)
    ymin = min(y)
    zmin = min(z)
    xmax = max(x)
    ymax = max(y)
    zmax = max(z)

    range = [[xmin, xmax], [ymin, ymax], [zmin, zmax]]

    for gen, df in enumerate(data):
        xs = [objectives[0] for objectives in df['population_fitness']]
        ys = [objectives[1] for objectives in df['population_fitness']]
        zs = [objectives[2] for objectives in df['population_fitness']]
        trace = go.Scatter(x=xs, y=ys, name='generation ' + str(generations[gen]), mode = 'markers',
                           marker=dict(
                               size='12',
                               color=zs,  # set color equal to a variable
                               colorbar=go.ColorBar(
                                   title='Primary Energy [MJ]',
                                   titleside = 'bottom',
                                   tickvals = range[2]
                               ),
                               colorscale='Viridis',
                               showscale=True,
                               opacity = 0.8
                           ))
        graph.append(trace)

    return graph, range

def calc_table(data, generations):
    graph = []
    x = []
    y =[]
    z = []
    least_cost = []
    least_CO2 = []
    least_prim = []
    for gen, df in enumerate(data):
        x = ([objectives[0] for objectives in df['population_fitness']])
        y = ([objectives[1] for objectives in df['population_fitness']])
        z = ([objectives[2] for objectives in df['population_fitness']])
        individual = df['population']
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


def dashboard(locator, config):

    # Local Variables
    final_generation = [499]
    generations = [200, 300 , 499]

    if generations == []:
        generations = [config.ngen]

    data = []
    for i in generations:

        with open(locator.get_optimization_checkpoint(i), "rb") as fp:
            data.append(json.load(fp))

    # Create Pareto Curve multiple generations
    output_path = locator.get_timeseries_plots_file("District" + '_Pareto_curve')
    title = 'Pareto Curve for District'
    pareto_curve_over_generations(data, generations, title, output_path)


    # CREATE PARETO CURVE FINAL GENERATION
    with open(locator.get_optimization_checkpoint(final_generation), "rb") as fp:
        data.append(json.load(fp))
    output_path = locator.get_timeseries_plots_file("District" + '_Pareto_curve')
    title = 'Pareto Curve for District'
    pareto_curve(data, final_generation, title, output_path)





def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
