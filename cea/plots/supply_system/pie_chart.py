from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR


def pie_chart(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # PLOT GRAPH
    layout = go.Layout(images=LOGO, title=title,showlegend=True)
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}

def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    labels = []
    values = []
    colors = []
    for field in analysis_fields:
        values.append(data_frame[field].values[0])
        labels.append(NAMING[field])
        colors.append(COLOR[field])

    trace = go.Pie(labels=labels, values=values, hoverinfo = 'label+percent', marker=dict(colors=colors))
    graph.append(trace)

    return graph
