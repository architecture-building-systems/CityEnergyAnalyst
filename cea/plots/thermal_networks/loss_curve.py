from __future__ import division
from __future__ import print_function

import numpy as np
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import NAMING, LOGO, COLOR


def loss_curve(data_frame, analysis_fields, title, output_path):
    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        y = np.nan_to_num(y)
        if field in ['cooling_demand', 'heating_demand']:  # demand data on secondary y axis
            trace = go.Scatter(x=data_frame.index, y=y, name=field,
                               marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                               mode='lines', yaxis='y2', opacity=0.7)
        else:  # primary y_axis
            A = field.split('_')[0]
            B = field.split('_')[1]
            C = A + '_' + B
            trace = go.Scatter(x=data_frame.index, y=y, name=C,
                               marker=dict(color=COLOR[field]),
                               mode='lines')

        traces.append(trace)

    if 'Epump_loss_kWh' in analysis_fields:  # used to differentiate between absolute and relative values plot
        y_axis_title = 'Loss [kWh]'
    else:  # relative plot
        y_axis_title = 'Loss [% of Plant Heat Produced]'

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title=y_axis_title),
                  yaxis2=dict(title='Demand [kWh]', overlaying='y',
                              side='right'), xaxis=dict(rangeselector=dict(buttons=list([
            dict(count=1, label='1d', step='day', stepmode='backward'),
            dict(count=1, label='1w', step='week', stepmode='backward'),
            dict(count=1, label='1m', step='month', stepmode='backward'),
            dict(count=6, label='6m', step='month', stepmode='backward'),
            dict(count=1, label='1y', step='year', stepmode='backward'),
            dict(step='all')])), rangeslider=dict(), type='date'))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
