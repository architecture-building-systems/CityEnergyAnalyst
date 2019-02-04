from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def solar_radiation_curve(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    layout = dict(images=LOGO, title=title,
                  yaxis=dict(domain=dict(x=[0, 1], y=[0.0, 0.7]), title='Solar Radiation [kW]'),
                  yaxis2=dict(title='Temperature [C]', overlaying='y',
                              side='right'), xaxis=dict(rangeselector=dict(buttons=list([
            dict(count=1, label='1d', step='day', stepmode='backward'),
            dict(count=1, label='1w', step='week', stepmode='backward'),
            dict(count=1, label='1m', step='month', stepmode='backward'),
            dict(count=6, label='6m', step='month', stepmode='backward'),
            dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.DATE[0],
                                                                         data_frame.DATE[168]],
            fixedrange=False))

    fig = dict(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    graph = []
    x = data_frame.DATE
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        if field == "T_ext_C":
            trace = go.Scatter(x=x, y=y, name=name, yaxis='y2', opacity=0.2)
        else:
            trace = go.Scatter(x=x, y=y, name=name,
                               marker=dict(color=COLOR[field]))
        graph.append(trace)
    return graph
