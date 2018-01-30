from __future__ import division
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def peak_load_building(data_frame, analysis_fields, title, output_path):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    area = data_frame["Af_m2"]
    data_frame = data_frame[analysis_fields]
    x = ["Absolute [kW] ", "Relative [W/m2]"]
    for field in analysis_fields:
        y = [data_frame[field], data_frame[field]/area*1000]
        trace = go.Bar(x = x, y= y, name = field.split('0', 1)[0],
                       marker=dict(color=COLOR.get_color_rgb(field.split('0', 1)[0])))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='Peak Load'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def peak_load_district(data_frame_totals, analysis_fields, title, output_path):

    traces = []
    data_frame_totals['total'] = total = data_frame_totals[analysis_fields].sum(axis=1)
    data_frame_totals = data_frame_totals.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame_totals[field]
        total_perc = (y/total*100).round(2).values
        total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x = data_frame_totals["Name"], y= y, name = field.split('0', 1)[0],  text = total_perc_txt,
                       marker=dict(color=COLOR.get_color_rgb(field.split('0', 1)[0])))
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack', yaxis=dict(title='Peak Load [kW]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def diversity_factor(data_frame_timeseries, data_frame_totals, analysis_fields, title, output_path):

    traces = []
    x = ["Aggregated [MW] ", "System [MW]"]
    for field in analysis_fields:
        y1 = data_frame_totals[field+'0_kW'].sum()/1000
        y2 = data_frame_timeseries[field+'_kWh'].max()/1000
        y = [y1,y2]
        trace = go.Bar(x = x, y= y, name = field.split('0', 1)[0])
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack', yaxis=dict(title='Peak Load [MW]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)