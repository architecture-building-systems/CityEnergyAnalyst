from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING


def emissions(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Green House Gas Emissions [ton CO2-eq/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Building Name'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        name = NAMING[field]
        total_perc = (y / total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=data_frame.index, y=y, name=name, text=total_perc_txt,
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def calc_table(analysis_fields, data_frame):
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str('{:20,.2f}'.format(x)) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

    # calculate graph
    anchors = []
    load_names = []
    for field in analysis_fields + ["total"]:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
    for field in analysis_fields:
        load_names.append(NAMING[field] + ' (' + field + ')')

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Category', 'Emissions for all buildings [ton CO2-eq/yr]',
                                         'Top 3 most polluting buildings']),
                     cells=dict(values=[load_names + ["TOTAL"],
                                        total_perc + [str('{:20,.2f}'.format(sum(total))) + " (100 %)"], anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
