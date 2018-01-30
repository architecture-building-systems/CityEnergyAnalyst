from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def pareto_capacity_installed(data_frame, analysis_fields, renewable_sources_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, renewable_sources_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Power Capacity [MW]', domain=[.35, 1]),
                       xaxis=dict(title='Point in the Pareto Curve'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_table(analysis_fields, renewable_sources_fields, data_frame):
    # analysis of buildings connected
    data_connected = data_frame['network']
    data_connected['buildings connected'] = data_connected.network.apply(lambda x: calc_building_connected_share(x))

    #analysis of renewable energy share
    data_capacities = data_frame['capacities_W'].join(data_frame['disconnected_capacities_W']).join(data_connected)
    renewable_share = calc_renewable_share(analysis_fields, renewable_sources_fields, data_capacities)
    data_capacities['load base unit'] = calc_top_three_technologies(analysis_fields, data_capacities, analysis_fields)

    table = go.Table(domain=dict(x=[0, 1], y=[0, 0.2]),
                            header=dict(values=['Individual ID', 'Building connectivity [%]', 'Renewable share [%]', 'Load Base Unit']),
                            cells=dict(values=[data_capacities.index, data_connected['buildings connected'].values, renewable_share.values,
                                               data_capacities['load base unit'].values]))
    return table

def calc_graph(analysis_fields, data_frame):

    # CALCULATE GRAPH FOR CONNECTED BUILDINGS
    graph = []
    data = (data_frame['capacities_W'].join(data_frame['disconnected_capacities_W'])/1000000).round(2)  # convert to MW
    data['total'] = total = data[analysis_fields].sum(axis=1)
    data = data.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in analysis_fields:
        y = data[field]
        total_perc = (y/total*100).round(2).values
        total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x=data.index, y=y, name=field.split('_capacity', 1)[0], text = total_perc_txt)
        graph.append(trace)

    #CALCULATE GRAPH FOR DISCONNECTED BUILDINGS

    return graph

def calc_building_connected_share(network_string):
    share = round(sum([int(x) for x in network_string])/ len(network_string)*100,0)
    return share

def calc_renewable_share(all_fields, renewable_sources_fields, dataframe):

    nominator = dataframe[renewable_sources_fields].sum(axis=1)
    denominator = dataframe[all_fields].sum(axis=1)
    share = (nominator/denominator*100).round(2)
    return share

def calc_top_three_technologies(analysis_fields, data_frame, fields):

    top_values = []
    data = data_frame[analysis_fields]
    for individual in data.index:
        top_values.extend(data.ix[individual].sort_values(ascending=False)[:1].index.values)

    #change name
    top_values = [x.split('_capacity', 1)[0] for x in top_values]

    return top_values




