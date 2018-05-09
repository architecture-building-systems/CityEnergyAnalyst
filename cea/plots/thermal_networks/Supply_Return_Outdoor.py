from __future__ import division
from __future__ import print_function

import numpy as np
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO, NAMING, COLOR


def supply_return_ambient_temp_plot(data_frame, data_frame_2, analysis_fields, title, output_path):
    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        # sort by ambient temperature, needs some helper variables
        y_old = np.vstack((np.array(data_frame_2.values.T), y))
        y_new = np.vstack((np.array(data_frame_2.values.T), y))
        y_new[0, :] = y_old[0, :][
            y_old[0, :].argsort()]  # y_old[0, :] is the ambient temperature which we are sorting by
        y_new[1, :] = y_old[1, :][y_old[0, :].argsort()]
        trace = go.Scatter(x=y_new[0], y=y_new[1], name=NAMING[field.split('_', 1)[0]],
                           marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                           mode='markers')
        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Temperature [deg C]'),
                  xaxis=dict(title='Ambient Temperature [deg C]'))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
