from __future__ import division
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


def individual_activation_curve(data_frame, analysis_fields_loads, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph= calc_graph(analysis_fields, analysis_fields_loads, data_frame)

    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Power Generated [kW]', domain=[.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(analysis_fields, analysis_fields_loads, data_frame):

    # main data about technologies
    data = (data_frame['activation_units_data']/1000).round(2) # to kW
    graph = []
    for field in analysis_fields:
        y = data[field].values
        trace = go.Bar(x=data.index, y= y, name = field, marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)

   # data about demand
    data_demand = (data_frame['buildings_demand_W']/1000).round(2)  # to kW
    y = data_demand[analysis_fields_loads]
    trace = go.Scatter(x=data.index, y=y, name=analysis_fields_loads, line=dict(color=COLOR.get_color_rgb(analysis_fields_loads),width=1))

    graph.append(trace)

    return graph
