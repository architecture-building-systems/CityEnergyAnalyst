from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def bar_chart_costs(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # PLOT GRAPH
    layout = go.Layout(images=LOGO, title=title, showlegend=True, barmode='relative',
                       yaxis=dict(title='Cost [USD$(2015) Mio/year]', domain=[0.0, 1.0]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # main data about technologies
    graph = []
    for field in analysis_fields:
        y = [data_frame[field] / 1000000]  # to convert to Millions
        name = NAMING[field]
        trace = go.Bar(x=["district"], y=y, name=name, marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph
