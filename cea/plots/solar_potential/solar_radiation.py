from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


def solar_radiation_district(data_frame, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph, x_axis = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)

    # CREATE BUTTON
    annotations = list([dict(text='Building:', x=-0.15, y=1.05, xref='paper', yref='paper', align='left', showarrow=False)])
    list_buttons = [dict(label='None', method='relayout', args=['xaxis.range[0]', -0.5])]
    labels = x_axis
    for i, label in enumerate(labels):
        left = (i + 1) - 1.5
        right = left + 1
        new_button = dict(label=label, method='relayout', args=['xaxis.range', [left, right]])
        list_buttons.append(new_button)
    updatemenus = list([dict(buttons=list_buttons)])

    layout = go.Layout(images=LOGO,title=title, barmode='stack', updatemenus=updatemenus,annotations=annotations,
                       yaxis=dict(title='Solar radiation [MWh/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Building'))
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
                       marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)

    return graph, data_frame.index,

def calc_table(analysis_fields, data_frame):
    median = data_frame[analysis_fields].median().round(2).tolist()
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str(x)+" ("+str(round(x/sum(total)*100,1))+" %)" for x in total]

    # calculate graph
    anchors = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                            header=dict(values=['Surface', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 most irradiated']),
                            cells=dict(values=[analysis_fields, total_perc, median, anchors ]))

    return table

def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list