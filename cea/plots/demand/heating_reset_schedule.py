from __future__ import division
from __future__ import print_function

import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR



def heating_reset_schedule(data_frame, analysis_fields, title, output_path):
    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    x = data_frame["T_ext_C"].values
    data_frame = data_frame.replace(0, np.nan)
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        trace = go.Scatter(x=x, y=y, name=name, mode='markers',
                           marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title,
                       xaxis=dict(title='Outdoor Temperature [C]'),
                       yaxis=dict(title='HVAC System Temperature [C]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
