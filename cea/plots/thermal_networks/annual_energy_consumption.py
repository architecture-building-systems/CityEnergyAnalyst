from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd

from cea.plots.variable_naming import NAMING, LOGO, COLOR


def annual_energy_consumption_plot(data_frame, analysis_fields, title, output_path):

    # CALCULATE GRAPH
    traces_graph_1 = calc_graph(analysis_fields, data_frame)
    #traces_graph_2 = calc_graph(analysis_fields, data_frame, substation_plot_flag)
    # PLOT GRAPH
    #traces_graph_1.append(traces_graph_2)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Energy consumption [kWh/yr]', domain=[0, 0.45]),
                       xaxis=dict(domain = [0, 0.45]),
                       yaxis2 = dict(domain = [0.55, 1]),
                       xaxis2 = dict(domain = [0, 0,45]))
    fig = go.Figure(data=traces_graph_1, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph_1, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    # format demand values
    data_1 = {}
    data_1['Q_dem_kWh'] = data_frame[0]
    data_1['P_loss_substations_kWh'] = data_frame[1].sum().sum()
    data_1['P_loss_kWh'] = data_frame[2].sum().sum()
    data_1['Q_loss_kWh'] = data_frame[3].sum().sum()
    total_energy = sum(data_1.values())

    data_2 = {}
    total_pipe_length = data_frame[4]
    data_2['Q_dem_kWh'] = data_frame[0]/total_pipe_length
    data_2['P_loss_substations_kWh'] = data_frame[1].sum().sum()/total_pipe_length
    data_2['P_loss_kWh'] = data_frame[2].sum().sum()/total_pipe_length
    data_2['Q_loss_kWh'] = data_frame[3].sum().sum()/total_pipe_length


    # iterate through data_1 to plot
    for field in analysis_fields:
        x = ['annual consumption']
        y = data_1[field]
        total_perc = (y / total_energy * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " kWh (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt, marker=dict(color=COLOR[field]))
        graph.append(trace)

    for field in analysis_fields:
        x = ['consumption per length']
        y = data_2[field]
        total_perc = (y / total_energy * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " kWh/m (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt, marker=dict(color=COLOR[field]),
                       xaxis = 'x2', yaxis = 'y2')
        graph.append(trace)

    return graph

