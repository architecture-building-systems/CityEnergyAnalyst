from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO, COLOR, NAMING


def all_tech_district_hourly(data_frame, all_tech_analysis_fields, title, output_path):
    traces = []
    for tech in all_tech_analysis_fields:
        analysis_fields = all_tech_analysis_fields[tech]
        for field in analysis_fields:
            y = data_frame[field].values
            name = field.split('_kWh', 1)[0]
            if tech == 'PV':
                trace = go.Scatter(x=data_frame.index, y=y, name=name, marker=dict(color=COLOR[field]))
            else:
                trace = go.Scatter(x=data_frame.index, y=y, name=name, visible='legendonly',
                                   marker=dict(color=COLOR[field]))
            traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Hourly production [kWh]'),
                  xaxis=dict(rangeselector=dict(buttons=list([
                      dict(count=1, label='1d', step='day', stepmode='backward'),
                      dict(count=1, label='1w', step='week', stepmode='backward'),
                      dict(count=1, label='1m', step='month', stepmode='backward'),
                      dict(count=6, label='6m', step='month', stepmode='backward'),
                      dict(count=1, label='1y', step='year', stepmode='backward'),
                      dict(step='all')])), rangeslider=dict(), type='date'))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}
