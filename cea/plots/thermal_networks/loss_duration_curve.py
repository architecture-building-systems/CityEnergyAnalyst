from __future__ import division

import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def loss_duration_curve(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                       yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)
    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    # calculate variables for the analysis
    loss_peak = data_frame[analysis_fields].max().round(2).tolist()  # save maximum value of loss
    loss_total = (data_frame[analysis_fields].sum() / 1000).round(2).tolist()  # save total loss value

    # calculate graph
    load_utilization = []
    loss_names = []
    # data = ''
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        field_1 = field.split('_')[0]
        field_2 = field.split('_')[1]
        field_3 = field_1 + '_' + field_2
        data_frame_new = data_frame.sort_values(by=field, ascending=False)
        y = data_frame_new[field].values
        load_utilization.append(evaluate_utilization(x, y))
        loss_names.append(NAMING[field] + ' (' + field_3 + ')')
    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                     header=dict(
                         values=['Name', 'Peak Load [kW]', 'Yearly Demand [MWh]', 'Utilization [-]']),
                     cells=dict(values=[loss_names, loss_peak, loss_total, load_utilization]))
    return table


def calc_graph(analysis_fields, data_frame):
    graph = []
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]  # calculate relative values
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        trace = go.Scatter(x=x, y=y, name=field, fill='tozeroy', opacity=0.8,
                           marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def evaluate_utilization(x, y):
    dataframe_util = pd.DataFrame({'x': x, 'y': y})
    if 0 in dataframe_util['y'].values:
        index_occurrence = dataframe_util['y'].idxmin(axis=0, skipna=True)
        utilization_perc = round(dataframe_util.loc[index_occurrence, 'x'], 1)
        utilization_days = int(utilization_perc * 8760 / (24 * 100))
        return str(utilization_perc) + '% or ' + str(utilization_days) + ' days a year'
    else:
        return 'all year'
