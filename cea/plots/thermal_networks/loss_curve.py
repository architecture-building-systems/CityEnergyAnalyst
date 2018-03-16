from __future__ import division
from __future__ import print_function

import numpy as np
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def loss_curve(data_frame, analysis_fields, title, output_path):

    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        y = np.nan_to_num(y)
        if field in ["Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]: #secondary y axis
            trace = go.Scatter(x=data_frame.index, y= y, name = field.split('_', 1)[0],
                               marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                               mode = 'lines', yaxis='y2', opacity = 0.7)
        else: #primary y_axis
            trace = go.Scatter(x=data_frame.index, y= y, name = field.split('_', 1)[0],
                               marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                               mode = 'lines')

        traces.append(trace)

    if 'Epump_loss_kWh' in analysis_fields:
        y_axis_title = 'Loss [kWh]'
    else: #relative plot
        y_axis_title = 'Loss [% of Plant Heat Produced]'

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title=y_axis_title), yaxis2=dict(title='Load [kWh]', overlaying='y',
                   side='right'), xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date'))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}