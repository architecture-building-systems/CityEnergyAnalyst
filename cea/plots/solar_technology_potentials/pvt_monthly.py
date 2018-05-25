from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import plotly.tools as tls

from cea.plots.variable_naming import LOGO, COLOR, NAMING


def pvt_district_monthly(data_frame, analysis_fields, title, output_path):
    E_analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields[0:5])].tolist()
    Q_analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields[5:10])].tolist()

    # CALCULATE GRAPH
    traces_graphs = calc_graph(E_analysis_fields_used, Q_analysis_fields_used, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(E_analysis_fields_used, Q_analysis_fields_used, data_frame)

    # PLOT GRAPH
    traces_graphs.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='PVT Electricity/Heat production [MWh]',
                                  domain=[0.35, 1]))

    fig = go.Figure(data=traces_graphs, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graphs, 'layout': layout}


def calc_graph(E_analysis_fields_used, Q_analysis_fields_used, data_frame):
    # calculate graph
    Q_graph = []
    E_graph = []
    graph = []
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    E_total = new_data_frame[E_analysis_fields_used].sum(axis=1)
    Q_total = new_data_frame[Q_analysis_fields_used].sum(axis=1)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    for field in Q_analysis_fields_used:
        y = new_data_frame[field]
        total_perc = (y.divide(Q_total) * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]

        trace1 = go.Bar(x=x, y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR[field], line=dict(
                            color="rgb(105,105,105)", width=1)), opacity=0.7, width=0.3, offset=0)
        Q_graph.append(trace1)
        graph.append(trace1)

    for field in E_analysis_fields_used:
        y = new_data_frame[field]
        total_perc = (y / E_total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace2 = go.Bar(x=x, y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR[field]), width=0.3, offset=-0.35)
        E_graph.append(trace2)
        graph.append(trace2)
    fig = tls.make_subplots(rows=2, cols=1, shared_xaxes = True, shared_yaxes=True )
    fig.append_trace(Q_graph,1,1)
    fig.append_trace(E_graph,2,1)
    plot(fig, auto_open=True)
    return graph


def calc_table(E_analysis_fields_used, Q_analysis_fields_used, data_frame):
    analysis_fields_used = []
    total_perc = []

    # calculation for electricity production
    E_total = (data_frame[E_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    # calculate top three potentials
    anchors = []
    load_names = []
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    new_data_frame.set_index("month", inplace=True)

    if sum(E_total)>0:
        E_total_perc = [str(x) + " (" + str(round(x / sum(E_total) * 100, 1)) + " %)" for x in E_total]
        for field in E_analysis_fields_used:
            anchors.append(calc_top_three_anchor_loads(new_data_frame, field))
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        E_total_perc = ['0 (0%)']*len(E_total)
        for field in E_analysis_fields_used:
            anchors.append('-')
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')


    analysis_fields_used.extend(E_analysis_fields_used)
    total_perc.extend(E_total_perc)

    # calculation for heat production
    Q_total = (data_frame[Q_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    if sum(Q_total) > 0:
        Q_total_perc = [str(x) + " (" + str(round(x / sum(Q_total) * 100, 1)) + " %)" for x in Q_total]
        for field in Q_analysis_fields_used:
            anchors.append(calc_top_three_anchor_loads(new_data_frame, field))
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        Q_total_perc = ['0 (0%)']*len(Q_total)
        for field in Q_analysis_fields_used:
            anchors.append('-')
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')

    analysis_fields_used.extend(Q_analysis_fields_used)
    total_perc.extend(Q_total_perc)

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']),
                     cells=dict(values=[load_names, total_perc, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
