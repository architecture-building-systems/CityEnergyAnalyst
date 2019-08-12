from __future__ import division
from __future__ import print_function

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

def energy_supply_mix(data_frame, analysis_fields, title, yaxis_title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title=yaxis_title, domain=[1, 1]),
                       xaxis=dict(title='Scenario Name'), showlegend=True)
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}

def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = data_frame[analysis_fields].sum(axis=1)
    data_frame['Name'] = data_frame.index.values
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        y_percentage = (y / data_frame['total'] * 100).round(2).values
        total_MWh_txt = ["(" + str(x) + " %)" for x in y]
        name = NAMING[field]
        trace = go.Bar(x=data_frame['Name'], y=y_percentage, name=name, text=total_MWh_txt, orientation ='h',
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph
