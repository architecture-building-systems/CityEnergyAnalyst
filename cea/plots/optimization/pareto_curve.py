"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, NAMING

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def pareto_curve(data, objectives, analysis_fields, title, output_path):
    # CALCULATE GRAPH

    traces_table, table = calc_table(data, analysis_fields)

    traces_graph, ranges = calc_graph(data, objectives, table)

    # CALCULATE TABLE

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, legend=dict(orientation="v", x=0.8, y=0.7), title=title,
                       xaxis=dict(title='Total annualized costs [USD$(2015) Mio/yr]', domain=[0, 1], range=ranges[0]),
                       yaxis=dict(title='GHG emissions [kton CO2-eq]', domain=[0.3, 1.0], range=ranges[1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(data, objectives, table):
    xs = data[objectives[0]].values
    ys = data[objectives[1]].values
    zs = data[objectives[2]].values
    individual_names = data['individual'].values

    xmin = min(xs)
    ymin = min(ys)
    zmin = min(zs)
    xmax = max(xs)
    ymax = max(ys)
    zmax = max(zs)
    ranges_some_room_for_graph = [[xmin - ((xmax - xmin) * 0.1), xmax + ((xmax - xmin) * 0.1)],
                                  [ymin - ((ymax - ymin) * 0.1), ymax + ((ymax - ymin) * 0.1)], [zmin, zmax]]

    graph = []
    trace = go.Scatter(x=xs, y=ys, mode='markers', name='data', text=individual_names,
                       marker=dict(size='12', color=zs,
                                   colorbar=go.ColorBar(title='Primary Energy [TJ]',
                                                        titleside='bottom'), colorscale='Jet', showscale=True,
                                   opacity=0.8))
    graph.append(trace)

    # Insert scatter points of MCDA assessment.
    xs = table[objectives[0]].values
    ys = table[objectives[1]].values
    name = table["Attribute"].values
    trace = go.Scatter(x=xs, y=ys, mode='markers', name="multi-criteria-analysis", text=name,
                       marker=dict(size='20', color='white', line=dict(
                           color='black',
                           width=2)))
    graph.append(trace)

    return graph, ranges_some_room_for_graph


def calc_table(data_frame, analysis_fields):
    least_annualized_cost = data_frame.loc[
        data_frame["TAC_rank"] < 2]  # less than two because in the case there are two individuals MCDA calculates 1.5
    least_emissions = data_frame.loc[data_frame["emissions_rank"] < 2]
    least_primaryenergy = data_frame.loc[data_frame["prim_rank"] < 2]
    user_defined_mcda = data_frame.loc[data_frame["user_MCDA_rank"] < 2]

    # do a check in the case more individuals had the same ranking.
    if least_annualized_cost.shape[0] > 1:
        individual = str(least_annualized_cost["individual"].values)
        least_annualized_cost = least_annualized_cost.reset_index(drop=True)
        least_annualized_cost = least_annualized_cost[0]
        least_annualized_cost["individual"] = individual

    if least_emissions.shape[0] > 1:
        individual = str(least_emissions["individual"].values)
        least_emissions = least_emissions.reset_index(drop=True)
        least_emissions = least_emissions.loc[0]
        least_emissions["individual"] = individual

    if least_primaryenergy.shape[0] > 1:
        individual = str(least_primaryenergy["individual"].values)
        least_primaryenergy = least_primaryenergy.reset_index(drop=True)
        least_primaryenergy = least_primaryenergy.loc[0]
        least_primaryenergy["individual"] = individual

    if user_defined_mcda.shape[0] > 1:
        individual = str(user_defined_mcda["individual"].values)
        user_defined_mcda = user_defined_mcda.reset_index(drop=True)
        user_defined_mcda = user_defined_mcda.loc[0]
        user_defined_mcda["individual"] = individual

    # Now extend all dataframes
    final_dataframe = least_annualized_cost.append(least_emissions).append(least_primaryenergy).append(
        user_defined_mcda)
    final_dataframe.reset_index(drop=True, inplace=True)
    final_dataframe["Attribute"] = ["least annualized costs", "least emissions", "least primary energy",
                                    "user defined MCDA"]
    headers = ["Attribute"] + analysis_fields
    cells = []
    for field in headers:
        if field in ["Attribute", "individual"]:
            cells.append(final_dataframe[field].values)
        else:
            cells.append(np.round(final_dataframe[field].values, 2))

    headers = ["Attribute"] + [NAMING[field] for field in analysis_fields]
    table_trace = go.Table(domain=dict(x=[0, 1.0], y=[0, 0.2]),
                           header=dict(values=headers),
                           cells=dict(values=cells))

    return table_trace, final_dataframe
