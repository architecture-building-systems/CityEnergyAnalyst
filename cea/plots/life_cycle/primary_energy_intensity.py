from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


def primary_energy_intensity(data_frame, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Consumption of Fossil Fuels per Gross Floor Area [MJ Oil-eq/m2.yr]'),
                       xaxis=dict(title='Building Name'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        total_perc = (y/total*100).round(2).values
        total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x=data_frame.index, y=y, name=field, text = total_perc_txt,
                       marker=dict(color=COLOR.get_color_rgb(field.split('_MJm2', 1)[0])))
        graph.append(trace)

    return graph
