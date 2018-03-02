from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()


def solar_radiation_district_monthly(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='Solar radiation [MWh/month]',
                                                                             domain=[0.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    total = new_data_frame[analysis_fields].sum(axis=1)
    for field in analysis_fields:
        y = new_data_frame[field]
        total_perc = (y / total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=new_data_frame["month"], y=y, name=field, text=total_perc_txt,
                       marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)

    return graph


def calc_table(analysis_fields, data_frame):
    total = (data_frame[analysis_fields].sum(axis=0) / 1000).round(2).tolist()  # to MW
    total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

    new_data_frame = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    new_data_frame.set_index("month", inplace=True)
    # calculate graph
    anchors = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(new_data_frame, field))
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Top 3 most irradiated months']),
                     cells=dict(values=[analysis_fields, total_perc, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
