from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Bhargava Sreepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def pie_chart(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # PLOT GRAPH
    layout = go.Layout(images=LOGO, title=title, showlegend=True)
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    labels = []
    values = []
    colors = []
    text = []
    for field in analysis_fields:
        text.append(str(data_frame[field]) + " [MWh/yr]")
        values.append(data_frame[field])
        labels.append(NAMING[field])
        colors.append(COLOR[field])

    trace = go.Pie(labels=labels, values=values, text=text, hoverinfo='label+percent+text', marker=dict(colors=colors))
    graph.append(trace)

    return graph
