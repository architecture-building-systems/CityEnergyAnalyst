from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import NAMING, LOGO

COLOR = ColorCodeCEA()


def energy_loss_bar_plot(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Energy Loss [kWh/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Edge Name'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    data = data_frame[0].fillna(value=0)
    data = pd.DataFrame(data.sum(axis=0), columns=[analysis_fields[0]])
    data1 = data_frame[1].fillna(value=0)
    data1 = pd.DataFrame(data1.sum(axis=0), columns=[analysis_fields[1]])
    total = pd.DataFrame(data.values+data1.values, index=data1.index, columns=['total'])
    data_frame = data.join(data1)
    data_frame = data_frame.join(total)
    anchors = []
    load_names = []
    median = []
    peak = []
    total_perc = []
    for field in analysis_fields:
        # calculate graph
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
        load_names.append(NAMING[field.split('_', 1)[0]] + ' (' + field.split('_', 1)[0] + ')')
        median.append(round(data_frame[field].median(), 2))
        peak.append(round(data_frame[field].abs().max(), 2))
        local_total = [round(data_frame[field].sum(), 2)]
        total_perc .append(str(local_total) + " (" + str(round(local_total / total.sum().values * 100, 1)) + " %)")

    table = go.Table(domain=dict(x=[0, 1.0], y=[0, 0.2]),
                     header=dict(values=['Load Name', 'Total [kWh/yr]', 'Peak [kW]', 'Median [kWh]', 'Top 3 Consumers']),
                     cells=dict(values=[load_names, total_perc, peak, median, anchors]))

    return table


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data = data_frame[0].fillna(value=0)
    data = pd.DataFrame(data.sum(axis=0), columns=[analysis_fields[0]])
    data1 = data_frame[1].fillna(value=0)
    data1 = pd.DataFrame(data1.sum(axis=0), columns=[analysis_fields[1]])
    total = pd.DataFrame(data.values+data1.values, index=data1.index, columns=['total'])
    data_frame = data.join(data1)
    data_frame = data_frame.join(total)
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        total_perc = (data_frame[field].values.reshape(1, len(total.index)) / data_frame['total'].values.reshape(1, len(total.index)) * 100).round(2)[0]
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=data_frame.index, y=data_frame[field].values, name=field.split('_', 1)[0], text=total_perc_txt, orientation='v',
                           marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))
        graph.append(trace)

    return graph


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
