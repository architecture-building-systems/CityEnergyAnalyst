from __future__ import division
from __future__ import print_function

import numpy as np
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def distance_loss_curve(data_frame, data_frame_2, analysis_fields, title, output_path, axis_title):

    traces = []
    for field in analysis_fields:
        for distance in data_frame_2.index.values:
            y = data_frame[field].values
            #sort by distance
            y = np.vstack((np.array(data_frame_2.ix[distance]), y))
            y[0,:] = y[0,:][y[0,:].argsort()]
            y[1, :] = y[1, :][y[0, :].argsort()]
            trace = go.Scatter(x=y[0], y= y[1], name = field.split('_', 1)[0],
                                   marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))

            traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title=axis_title), xaxis=dict(title='Distance from plant [m]'))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def loss_curve_relative(data_frame, analysis_fields, title, output_path):

    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        trace = go.Scatter(x=data_frame.index, y= y, name = field.split('_', 1)[0],
                               marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))

        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Relative Loss [%]'),
                    xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date'))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}