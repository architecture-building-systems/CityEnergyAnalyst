from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


def operation_costs_district(data_frame, analysis_fields, analysis_fields_m2, title, output_path):

    #CALCULATE GRAPH
    axis_x = 'x1'
    axis_y = 'y1'
    traces_graph_1 = calc_graph(axis_x, axis_y, analysis_fields, data_frame)
    axis_x = 'x2'
    axis_y = 'y2'
    traces_graph_2 = calc_graph(axis_x, axis_y, analysis_fields_m2, data_frame)
    traces_graph_1.extend(traces_graph_2)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph_1.append(traces_table)

    layout = go.Layout(images=LOGO, title=title, barmode ='stack',
                       yaxis1=dict(title='Absolute yearly costs [$/yr]', domain=[0.35, 1], anchor = 'x1'),
                       xaxis1=dict(title='Building', domain=[0.0, 0.45], anchor = 'y1'),
                       yaxis2=dict(title='Relative yearly costs [$/m2.yr]', domain=[0.35, 1], anchor = 'x2'),
                       xaxis2=dict(title='Building', domain=[0.55, 1], anchor = 'y2')
                       )

    fig = go.Figure(data=traces_graph_1, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def calc_graph(axis_x, axis_y, analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        total_perc = (y/total*100).round(2).values
        total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x=data_frame.index, y=y, name=field, text = total_perc_txt, xaxis=axis_x, yaxis=axis_y,
                       marker=dict(color=COLOR.get_color_rgb(field.split('_cost', 1)[0])))
        graph.append(trace)

    return graph

def calc_table(analysis_fields, data_frame):
    median = data_frame[analysis_fields].median().round(2).tolist()
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str(x)+" ("+str(round(x/sum(total)*100,1))+" %)" for x in total]

    # calculate graph
    anchors = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                            header=dict(values=['Service', 'Costs for all buildings [$/yr]', 'Median per building [$/yr]', 'Top 3 most costly buildings']),
                            cells=dict(values=[analysis_fields, total_perc, median, anchors ]))

    return table

def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list