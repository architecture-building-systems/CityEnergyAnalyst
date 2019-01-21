from __future__ import division
from __future__ import print_function

import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, NAMING, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
        trace = go.Scatter(x=y_new[0], y=y_new[1], name=NAMING[field],
                           marker=dict(color=COLOR[field]),
                           mode='markers')
        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Temperature [deg C]'),
                  xaxis=dict(title='Ambient Temperature [deg C]'))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
