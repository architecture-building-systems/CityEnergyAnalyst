from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


def energy_use_intensity(data_frame, analysis_fields, title, output_path):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    area = data_frame["Af_m2"]
    x = ["Absolute [MWh/yr]", "Relative [kWh/m2.yr]"]
    for field in analysis_fields:
        y = [data_frame[field], data_frame[field]/area*1000]
        trace = go.Bar(x = x, y= y, name = field.split('_', 1)[0],
                       marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title, barmode='stack')
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def energy_use_intensity_district(data_frame, analysis_fields, title, output_path):

    traces = []
    x = data_frame["Name"].tolist()
    for field in analysis_fields:
        data_frame[field] = data_frame[field]*1000/data_frame["GFA_m2"] # in kWh/m2y
    data_frame['total'] = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        trace = go.Bar(x = x, y= y, name = field.split('_', 1)[0],
                       marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))
        traces.append(trace)

    layout = go.Layout(images=LOGO,title=title, barmode='stack', yaxis=dict(title='Energy Use Intensity [kWh/m2.yr]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)