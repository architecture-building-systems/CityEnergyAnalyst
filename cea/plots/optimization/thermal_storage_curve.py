from __future__ import division

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()


def thermal_storage_activation_curve(data_frame, analysis_fields_charging, analysis_fields_discharging,
                                     analysis_fields_status, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields_charging, analysis_fields_discharging,
                              analysis_fields_status, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields_charging, analysis_fields_discharging,
                              analysis_fields_status, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, barmode='relative',
                  yaxis=dict(title='Power charged/discharged [kW]', domain=[0.45, 1.0]),
                  xaxis=dict(rangeselector=dict(buttons=list([
                      dict(count=1, label='1d', step='day', stepmode='backward'),
                      dict(count=1, label='1w', step='week', stepmode='backward'),
                      dict(count=1, label='1m', step='month', stepmode='backward'),
                      dict(count=6, label='6m', step='month', stepmode='backward'),
                      dict(count=1, label='1y', step='year', stepmode='backward'),
                      dict(step='all')])), rangeslider=dict(), type='date'))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields_charging, analysis_fields_discharging, analysis_fields_status, data_frame):
    # main data about technologies
    data = (data_frame / 1000).round(2)  # to kW
    graph = []
    for field in analysis_fields_charging:
        y = data[field].values
        trace = go.Bar(x=data.index, y=y, name=field, marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)

    for field in analysis_fields_discharging:
        y = -data[field].values  # negative
        trace = go.Bar(x=data.index, y=y, name=field, marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)

    # data about the status of the storage
    for field in analysis_fields_status:
        y = data[field]
        trace = go.Scatter(x=data.index, y=y, name=field,
                           line=dict(color=COLOR.get_color_rgb(field), width=1))

    graph.append(trace)

    return graph


def calc_table(analysis_fields_charging, analysis_fields_discharging, analysis_fields_status, data_frame):
    """
    draws table of monthly energy balance

    :param data_frame_month: data frame of monthly building energy balance
    :return:
    """

    # translate results into monthly
    data_frame.index = pd.to_datetime(data_frame.index)
    data_frame_month = (data_frame.resample("M").sum() / 1000000).round(2)  # to MW
    data_frame_month["month"] = data_frame_month.index.strftime("%B")

    # create table arrays
    name_month = np.append(data_frame_month['month'].values, ['YEAR'])
    status = np.append(data_frame_month[analysis_fields_status].sum(axis=1), ['-'])
    total_heat = np.append(data_frame_month[analysis_fields_charging].sum(axis=1),
                           data_frame_month[analysis_fields_charging].sum(axis=1).sum(axis=0))
    total_cool = np.append(data_frame_month[analysis_fields_discharging].sum(axis=1),
                           data_frame_month[analysis_fields_discharging].sum(axis=1).sum(axis=0))
    balance = np.append((total_heat - total_cool), (total_heat - total_cool).sum().round(2))

    # draw table
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Month', 'Total in [MWh]', 'Total out [MWh]', 'Balance [MWh]',
                                         'Status Storage [MWh]']),
                     cells=dict(values=[name_month, total_heat, total_cool, balance, status]))

    return table
