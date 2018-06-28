from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd
import numpy as np

from cea.plots.variable_naming import NAMING, LOGO, COLOR


def likelihood_chart(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # PLOT GRAPH
    # traces_graph['layout'].update(images=LOGO, title=title, showlegend=True,
    #                               yaxis=dict(title='Frequency [hours/yr]'),
    #                               xaxis=dict(title='Ramp-up[MW] (-), Ramp-down[MW] (+)')
    #                               )
    # plot(traces_graph, auto_open=False, filename=output_path)

    layout = go.Layout(images=LOGO, title=title, barmode='overlay',
                       yaxis=dict(title='Load [MW]'),
                       xaxis=dict(title='Hour of the day'), showlegend=True)
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}

def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    datetime = pd.DatetimeIndex(data_frame["DATE"].values)
    hours = datetime.hour

    for field in analysis_fields:
        y = data_frame[field]/1000000 #in MWh
        name = NAMING[field]
        trace = go.Box(x=hours, y=y, name=name, marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph
