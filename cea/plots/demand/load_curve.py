from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def load_curve(data_frame, analysis_fields, title, output_path):

    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        if field in ["T_int_C", "T_ext_C"]:
            trace = go.Scatter(x=data_frame.index, y= y, name = name, yaxis='y2', opacity = 0.2)
        else:
            trace = go.Scatter(x=data_frame.index, y= y, name = name,
                               marker=dict(color=COLOR[field]))

        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Load [kW]'), yaxis2=dict(title='Temperature [C]', overlaying='y',
                   side='right'),xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date',range= [data_frame.index[0],
                                                                                 data_frame.index[168]],
                                                                          fixedrange=False))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}