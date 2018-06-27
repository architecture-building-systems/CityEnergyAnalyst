from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd
import os

from cea.plots.variable_naming import NAMING, LOGO, COLOR


def annual_energy_consumption_plot(data_frame, analysis_fields, title, output_path):

    # CALCULATE GRAPH
    traces_graph_1 = calc_graph(analysis_fields, data_frame)


    #traces_graph_2 = calc_graph(analysis_fields, data_frame, substation_plot_flag)
    # PLOT GRAPH
    # splitted_path = os.path.split(output_path)[0]
    # network_type_name = os.path.split(output_path)[1].split('annual')[0]
    # file_name = network_type_name + 'network_layout.png'
    # network_image_path = os.path.join(splitted_path, file_name)
    # image_network = [dict(source=network_image_path, xref="paper", yref="paper",
    # x=0.95, y=0.5, sizex=0.5, sizey=0.5, xanchor="right", yanchor="middle")]

    #traces_graph_1.append(traces_graph_2)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Energy consumption [MWh/yr]'),
                       xaxis=dict(domain = [0.05, 0.4]),
                       yaxis2 = dict(title = 'Energy consumption per length [MWh/yr/m]', anchor = 'x2'),
                       xaxis2 = dict(domain = [0.55, 0.95]))
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
    total_energy_MWh = sum(data_1.values())/1000

    data_2 = {}
    total_pipe_length = data_frame[4]
    data_2['Q_dem_kWh'] = data_frame[0]/total_pipe_length
    data_2['P_loss_substations_kWh'] = data_frame[1].sum().sum()/total_pipe_length
    data_2['P_loss_kWh'] = data_frame[2].sum().sum()/total_pipe_length
    data_2['Q_loss_kWh'] = data_frame[3].sum().sum()/total_pipe_length
    total_energy_MWhperm = sum(data_2.values()) / 1000

    # iterate through data_1 to plot
    for field in analysis_fields:
        x = ['annual consumption']
        y = data_1[field]/1000
        total_perc = (y / total_energy_MWh * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " MWh (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt, marker=dict(color=COLOR[field]), width = 0.4)
        graph.append(trace)

    for field in analysis_fields:
        x = ['consumption per length']
        y = data_2[field]/1000
        total_perc = (y / total_energy_MWhperm * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " MWh/m (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt, marker=dict(color=COLOR[field]),
                       xaxis = 'x2', yaxis = 'y2', width = 0.4, showlegend = False)
        graph.append(trace)

    return graph

