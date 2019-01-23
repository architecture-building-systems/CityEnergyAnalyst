from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def cost_analysis_curve_centralized(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = go.Layout(images=LOGO, title=title, barmode='relative',
                       yaxis=dict(title='Cost [USD$(2015)/year]', domain=[0.0, 1.0]))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # main data about technologies
    data = (data_frame)
    graph = []
    for field in analysis_fields:
        y = data[field].values
        flag_for_unused_technologies = all(v == 0 for v in y)
        if not flag_for_unused_technologies:
            trace = go.Bar(x=data.index, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
            graph.append(trace)

    return graph
