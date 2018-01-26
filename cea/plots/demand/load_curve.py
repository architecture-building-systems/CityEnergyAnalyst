from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO, COLOR

def load_curve(data_frame, analysis_fields, title, output_path):

    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        if field in ["T_int_C", "T_ext_C"]:
            trace = go.Scatter(x=data_frame.index, y= y, name = field.split('_C', 1)[0], yaxis='y2', opacity = 0.2)
        else:
            trace = go.Scatter(x=data_frame.index, y= y, name = field.split('_', 1)[0],
                               marker=dict(color=COLOR[field.split('_', 1)[0]]))

        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Load [kW]'), yaxis2=dict(title='Temperature [C]', overlaying='y',
                   side='right'),xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date'))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)


def plot_div(data_frame, analysis_fields, title):

    traces = []
    x = data_frame.index.values
    for field in analysis_fields:
        y = data_frame[field].values
        if field in ["T_int_C", "T_ext_C"]:
            trace = go.Scatter(x= x, y= y, name = field.split('_C', 1)[0], yaxis='y2', opacity = 0.2)
        else:
            trace = go.Scatter(x= x, y= y, name = field.split('_', 1)[0])
        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(title=title,
                  yaxis=dict(title='Load [kW]'),
                  yaxis2=dict(title='Temperature [C]', overlaying='y', side='right'),
                  xaxis=dict(rangeselector=dict(buttons=list([
                      dict(count=1, label='1d', step='day', stepmode='backward'),
                      dict(count=1, label='1w', step='week', stepmode='backward'),
                      dict(count=1, label='1m', step='month', stepmode='backward'),
                      dict(count=6, label='6m', step='month', stepmode='backward'),
                      dict(count=1, label='1y', step='year', stepmode='backward'),
                      dict(step='all')])), rangeslider=dict(), type='date'))

    fig = dict(data=traces, layout=layout)
    return plot(fig,  auto_open=False, output_type='div')