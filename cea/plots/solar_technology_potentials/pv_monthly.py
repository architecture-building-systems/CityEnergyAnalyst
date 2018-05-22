from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import numpy as np

from cea.plots.variable_naming import LOGO, COLOR, NAMING


def pv_district_monthly(data_frame, analysis_fields, title, output_path):
    analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields)].tolist()

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields_used, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields_used, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='PV Electricity [MWh]',
                                                                             domain=[0.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    total = new_data_frame[analysis_fields].sum(axis=1)
    for field in analysis_fields:
        y = new_data_frame[field]
        total_perc = (y.divide(total) * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=new_data_frame["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def calc_table(analysis_fields, data_frame):
    total = (data_frame[analysis_fields].sum(axis=0) / 1000).round(2).tolist()  # to MW
    if sum(total)>0:
        total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
    else: total_perc = ['0 (0%)']*len(total)
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    new_data_frame.set_index("month", inplace=True)
    # calculate graph
    anchors = []
    load_names= []
    for field in analysis_fields:
        load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
        anchors.append(calc_top_three_anchor_loads(new_data_frame, field))
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']),
                     cells=dict(values=[load_names, total_perc, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
