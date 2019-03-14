from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def loss_curve(data_frame, analysis_fields, title, output_path):
    traces = []
    x = data_frame.index
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        if field in ['Q_dem_cool', 'Q_dem_heat']:  # demand data on secondary y axis
            trace = go.Scatter(x=x, y=y, name=name,
                               marker=dict(color=COLOR[field]),
                               yaxis='y2', opacity=0.6)
        else:  # primary y_axis
            trace = go.Scatter(x=x, y=y, name=name,
                               marker=dict(color=COLOR[field]))

        traces.append(trace)

    if 'P_loss_kWh' in analysis_fields:  # used to differentiate between absolute and relative values plot
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
            dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.index[0],
                                                                         data_frame.index[168]],
            fixedrange=False))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
