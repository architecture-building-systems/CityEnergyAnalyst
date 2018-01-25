from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import NAMING, LOGO, COLOR


def energy_demand_district(data_frame, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Energy Demand [MWh/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Building Name'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_table(analysis_fields, data_frame):
    median = data_frame[analysis_fields].median().round(2).tolist()
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str(x)+" ("+str(round(x/sum(total)*100,1))+" %)" for x in total]
    # calculate graph
    anchors = []
    load_names = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
        load_names.append(NAMING[field.split('_', 1)[0]] + ' (' + field.split('_', 1)[0] + ')')

    table = go.Table(domain=dict(x=[0, 1.0], y=[0, 0.2]),
                            header=dict(values=['Load Name', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 Consumers']),
                            cells=dict(values=[load_names, total_perc, median, anchors ]))

    return table

def calc_graph(analysis_fields, data_frame):

    # calculate graph
    graph = []
    data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        total_perc = (y/total*100).round(2).values
        total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x=data_frame["Name"], y=y, name=field.split('_', 1)[0], text = total_perc_txt, orientation ='v',
                       marker=dict(color=COLOR[field.split('_', 1)[0]]))
        graph.append(trace)

    return graph

def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].Name.values
    return anchor_list