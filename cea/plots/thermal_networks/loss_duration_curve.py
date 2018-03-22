from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import NAMING, LOGO

COLOR = ColorCodeCEA()

def loss_duration_curve(data_frame, analysis_fields, title, output_path):

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title,xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                       yaxis=dict(title='Thermal Losses / Pumping Energy [kWh / h]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)
    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    # calculate variables for the analysis
    loss_peak = data_frame[analysis_fields].max().round(2).tolist()
    loss_total = (data_frame[analysis_fields].sum() / 1000).round(2).tolist()

    # calculate graph
    loss_names = []
    # data = ''
    for field in analysis_fields:
        loss_names.append(NAMING[field.split('_', 1)[0]] + ' (' + field.split('_', 1)[0] + ')')
    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                            header=dict(
                                values=['Name', 'Peak [kW]', 'Yearly [MWh]']),
                            cells=dict(values=[loss_names, loss_peak, loss_total]))
    return table

def calc_graph(analysis_fields, data_frame):

    graph = []
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        trace = go.Scatter(x=x, y=y, name=field.split('_', 1)[0], fill='tozeroy', opacity=0.8,
                           marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))
        graph.append(trace)

    return graph