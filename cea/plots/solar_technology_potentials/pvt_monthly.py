from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()


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


def calc_graph(E_analysis_fields_used, Q_analysis_fields_used, data_frame):
    # calculate graph
    graph = []
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    E_total = new_data_frame[E_analysis_fields_used].sum(axis=1)
    Q_total = new_data_frame[Q_analysis_fields_used].sum(axis=1)

    for field in Q_analysis_fields_used:
        y = new_data_frame[field]
        total_perc = (y / Q_total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace1 = go.Bar(x=new_data_frame["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR.get_color_rgb(field.split('_kWh', 1)[0]), line=dict(
                            color="rgb(105,105,105)", width=1)),opacity=0.7, base=0, width=0.3, offset=0)
        graph.append(trace1)

    for field in E_analysis_fields_used:
        y = new_data_frame[field]
        total_perc = (y / E_total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace2 = go.Bar(x=new_data_frame["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR.get_color_rgb(field.split('_kWh', 1)[0])), width=0.3, offset=-0.35)
        graph.append(trace2)



    return graph


def calc_table(E_analysis_fields_used, Q_analysis_fields_used, data_frame):

    analysis_fields_used = []
    total_perc = []

    # calculation for electricity production
    E_total = (data_frame[E_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    E_total_perc = [str(x) + " (" + str(round(x / sum(E_total) * 100, 1)) + " %)" for x in E_total]
    analysis_fields_used.extend(E_analysis_fields_used)
    total_perc.extend(E_total_perc)

    # calculation for heat production
    Q_total = (data_frame[Q_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    Q_total_perc = [str(x) + " (" + str(round(x / sum(Q_total) * 100, 1)) + " %)" for x in Q_total]
    analysis_fields_used.extend(Q_analysis_fields_used)
    total_perc.extend(Q_total_perc)

    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    new_data_frame.set_index("month", inplace=True)

    # calculate top three potentials
    anchors = []
    for field in E_analysis_fields_used:
        anchors.append(calc_top_three_anchor_loads(new_data_frame, field))
    for field in Q_analysis_fields_used:
        anchors.append(calc_top_three_anchor_loads(new_data_frame, field))

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']),
                     cells=dict(values=[analysis_fields_used, total_perc, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
