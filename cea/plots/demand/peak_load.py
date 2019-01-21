from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def peak_load_building(data_frame, analysis_fields, title, output_path):
    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    area = data_frame["GFA_m2"]
    data_frame = data_frame[analysis_fields]
    x = ["Absolute [kW] ", "Relative [W/m2]"]
    for field in analysis_fields:
        y = [data_frame[field], data_frame[field] / area * 1000]
        name = NAMING[field]
        trace = go.Bar(x=x, y=y, name=name,
                       marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title, barmode='group', yaxis=dict(title='Peak Load'), showlegend=True)
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def peak_load_district(data_frame_totals, analysis_fields, title, output_path):
    traces = []
    data_frame_totals['total'] = data_frame_totals[analysis_fields].sum(axis=1)
    data_frame_totals = data_frame_totals.sort_values(by='total',
                                                      ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame_totals[field]
        total_perc = (y / data_frame_totals['total'] * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        name = NAMING[field]
        trace = go.Bar(x=data_frame_totals["Name"], y=y, name=name,
                       marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(title=title, barmode='group', yaxis=dict(title='Peak Load [kW]'), showlegend=True)
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def diversity_factor(data_frame_timeseries, data_frame_totals, analysis_fields, title, output_path):
    traces = []
    x = ["Aggregated [MW] ", "System [MW]"]
    for field in analysis_fields:
        y1 = data_frame_totals[field + '0_kW'].sum() / 1000
        y2 = data_frame_timeseries[field + '_kWh'].max() / 1000
        y = [y1, y2]
        trace = go.Bar(x=x, y=y, name=field.split('0', 1)[0])
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack', yaxis=dict(title='Peak Load [MW]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)
