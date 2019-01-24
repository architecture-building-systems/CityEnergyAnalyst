from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def pareto_capacity_installed(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Power Capacity [kW]', domain=[.35, 1]),
                       xaxis=dict(title='Point in the Pareto Curve'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    # analysis of renewable energy share
    data_frame['load base unit'] = calc_top_three_technologies(analysis_fields, data_frame, analysis_fields)

    table = go.Table(domain=dict(x=[0, 1], y=[0, 0.2]),
                     header=dict(values=['Individual ID', 'Building connectivity [%]', 'Load Base Unit']),
                     cells=dict(values=[data_frame.index, data_frame['Buildings Connected Share'].values,
                                        data_frame['load base unit'].values]))
    return table


def calc_graph(analysis_fields, data):
    # CALCULATE GRAPH FOR CONNECTED BUILDINGS
    graph = []
    data['total'] = data[analysis_fields].sum(axis=1)
    data['Name'] = data.index.values
    data = data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data[field]
        flag_for_unused_technologies = all(v == 0 for v in y)
        if not flag_for_unused_technologies:
            name = NAMING[field]
            total_perc = (y / data['total'] * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace = go.Bar(x=data['Name'], y=y, text=total_perc_txt, name=name,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

    # CALCULATE GRAPH FOR DISCONNECTED BUILDINGS

    return graph


def calc_building_connected_share(network_string):
    share = round(sum([int(x) for x in network_string]) / len(network_string) * 100, 0)
    return share


def calc_renewable_share(all_fields, renewable_sources_fields, dataframe):
    nominator = dataframe[renewable_sources_fields].sum(axis=1)
    denominator = dataframe[all_fields].sum(axis=1)
    share = (nominator / denominator * 100).round(2)
    return share


def calc_top_three_technologies(analysis_fields, data_frame, fields):
    top_values = []
    data = data_frame[analysis_fields]
    for individual in data.index:
        top_values.extend(data.ix[individual].sort_values(ascending=False)[:1].index.values)

    # change name
    top_values = [x.split('_capacity', 1)[0] for x in top_values]

    return top_values
