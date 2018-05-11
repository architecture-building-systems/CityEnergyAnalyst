from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()


def cost_analysis_curve(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Cost [$ per year]', domain=[0.0, 1.0]))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # main data about technologies
    data = (data_frame)  # to kW
    graph = []
    for field in analysis_fields:
        y = data[field].values
        trace = go.Bar(x=data.index, y=y, name=field, marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)


    return graph
