from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Bhargava Sreepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def individual_activation_curve(data_frame, analysis_fields_loads, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, analysis_fields_loads, data_frame)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, barmode='relative', yaxis=dict(title='Power generation [kW]'),
                  xaxis=dict(rangeselector=dict(buttons=list([
                      dict(count=1, label='1d', step='day', stepmode='backward'),
                      dict(count=1, label='1w', step='week', stepmode='backward'),
                      dict(count=1, label='1m', step='month', stepmode='backward'),
                      dict(count=6, label='6m', step='month', stepmode='backward'),
                      dict(count=1, label='1y', step='year', stepmode='backward'),
                      dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.index[0],
                                                                                   data_frame.index[168]],
                      fixedrange=False))

    # layout = go.Layout(images=LOGO, title=title, barmode='relative',
    #                    yaxis=dict(title='Power Generated [MWh]', domain=[0.0, 1.0]))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, analysis_fields_loads, data_frame):
    # main data about technologies
    data = data_frame
    graph = []
    for field in analysis_fields:
        y = (data[field].values) / 1000  # into kW
        trace = go.Bar(x=data.index, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
        graph.append(trace)

    # data about demand
    for field in analysis_fields_loads:
        y = (data[field].values) / 1000  # into kW
        trace = go.Scatter(x=data.index, y=y, name=NAMING[field],
                           line=dict(color=COLOR[field], width=1))

        graph.append(trace)

    return graph
