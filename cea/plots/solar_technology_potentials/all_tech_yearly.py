from __future__ import division
from __future__ import print_function

import math

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def all_tech_district_yearly(data_frame, pv_analysis_fields, pvt_analysis_fields, sc_fp_analysis_fields,
                             sc_et_analysis_fields, title,
                             output_path):
    # get fields to analyse
    E_analysis_fields = []
    Q_analysis_fields = []
    pv_E_analysis_fields_used = data_frame.columns[data_frame.columns.isin(pv_analysis_fields)].tolist()
    E_analysis_fields.extend(pv_E_analysis_fields_used)
    sc_fp_Q_analysis_fields_used = data_frame.columns[data_frame.columns.isin(sc_fp_analysis_fields)].tolist()
    Q_analysis_fields.extend(sc_fp_Q_analysis_fields_used)
    sc_et_Q_analysis_fields_used = data_frame.columns[data_frame.columns.isin(sc_et_analysis_fields)].tolist()
    Q_analysis_fields.extend(sc_et_Q_analysis_fields_used)
    pvt_E_analysis_fields_used = data_frame.columns[data_frame.columns.isin(pvt_analysis_fields[0:5])].tolist()

    if pvt_E_analysis_fields_used:  # checking if PVT is present, in some cooling cases PVT is not necessary to run
        E_analysis_fields.extend(pvt_E_analysis_fields_used)
        pvt_Q_analysis_fields_used = data_frame.columns[data_frame.columns.isin(pvt_analysis_fields[5:10])].tolist()
        Q_analysis_fields.extend(pvt_Q_analysis_fields_used)
    else:
        pvt_analysis_fields = []

    data_frame_MWh = data_frame / 1000  # to MWh

    # CALCULATE GRAPH
    traces_graph, x_axis = calc_graph(E_analysis_fields, Q_analysis_fields, data_frame_MWh)

    # CALCULATE TABLE
    traces_table = calc_table(E_analysis_fields, Q_analysis_fields, data_frame_MWh)

    # PLOT GRAPH
    traces_graph.append(traces_table)

    # CREATE BUTTON
    annotations = list(
        [dict(
            text='<b>In this plot, users can explore the combined potentials of all solar technologies.</b><br>'
                 'Instruction:'
                 'Click on the technologies to install on each building surface.<br>'
                 'Example: PV_walls_east_E + PVT_walls_south_E/Q + SC_FP_roofs_top_Q <br><br>'
            , x=0.8, y=1.1,
            xanchor='left', xref='paper', yref='paper', align='left', showarrow=False, bgcolor="rgb(254,220,198)")])

    range = calc_range(data_frame_MWh, pv_analysis_fields, pvt_analysis_fields, sc_fp_analysis_fields,
                       sc_et_analysis_fields)

    layout = go.Layout(images=LOGO, title=title, barmode='stack', annotations=annotations,
                       yaxis=dict(title='Electricity/Thermal Potential [MWh/yr]', domain=[0.35, 1], range=range),
                       yaxis2=dict(overlaying='y', anchor='x', domain=[0.35, 1], range=range),
                       xaxis=dict(title='Building'), legend=dict(x=1, y=0.1, xanchor='left'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_range(data_frame, pv_analysis_fields, pvt_analysis_fields, sc_fp_analysis_fields,
               sc_et_analysis_fields):
    """
    Determines the highest range of y-axis.
    This is a work-around to fix the range for both y-axes so they can overlap.
    :param data_frame: annual energy production of each technology on each surface
    :param pv_analysis_fields: list of surface names that install pv
    :param pvt_analysis_fields: list of surface names that install pvt
    :param sc_fp_analysis_fields: list of surface names that install sc_fp
    :param sc_et_analysis_fields: list of surface names that install sc_et
    :return:
    """

    # find the building with the highest electricity production from all surfaces
    range_pv_E = data_frame[pv_analysis_fields].sum(axis=1).max()
    range_pvt_E = data_frame[pvt_analysis_fields[0:5]].sum(axis=1).max()
    E_max = max(range_pv_E, range_pvt_E)
    # find the building with the highest heat production from all surfaces
    range_pvt_Q = data_frame[pvt_analysis_fields[5:10]].sum(axis=1).max()
    range_sc_fp_Q = data_frame[sc_fp_analysis_fields].sum(axis=1).max()
    range_sc_et_Q = data_frame[sc_et_analysis_fields].sum(axis=1).max()
    Q_max = max(range_pvt_Q, max(range_sc_fp_Q, range_sc_et_Q))
    # determine the maximum range of yaxis
    y_axis_max = math.ceil(max(Q_max, E_max))
    return [0, y_axis_max]


def calc_graph(E_analysis_fields, Q_analysis_fields, data_frame):
    # calculate graph
    graph = []

    data_frame['total_E'] = total_E = data_frame[E_analysis_fields].sum(axis=1)
    data_frame['total_Q'] = total_Q = data_frame[Q_analysis_fields].sum(axis=1)
    # data_frame = data_frame.sort_values(by='total', ascending=False) # this will get the maximum value to the left
    for field in E_analysis_fields:
        y = data_frame[field]
        if field.split('_')[0] == 'PVT':
            trace1 = go.Bar(x=data_frame.index, y=y, name=field.split('_kWh', 1)[0],
                            marker=dict(color=COLOR[field]), visible='legendonly',
                            width=0.3, offset=-0.35, legendgroup='PVT' + field.split('_')[2])
        else:
            trace1 = go.Bar(x=data_frame.index, y=y, name=field.split('_kWh', 1)[0],
                            marker=dict(color=COLOR[field]), visible='legendonly',
                            width=0.3, offset=-0.35)
        graph.append(trace1)

    for field in Q_analysis_fields:
        y = data_frame[field]
        if field.split('_')[0] == 'PVT':
            trace2 = go.Bar(x=data_frame.index, y=y, yaxis='y2', name=field.split('_kWh', 1)[0],
                            marker=dict(color=COLOR[field], line=dict(
                                color="rgb(105,105,105)", width=1)), opacity=1, visible='legendonly',
                            width=0.3, offset=0, legendgroup='PVT' + field.split('_')[2])
        elif field.split('_')[1] == 'FP':
            trace2 = go.Bar(x=data_frame.index, y=y, yaxis='y2', name=field.split('_kWh', 1)[0],
                            marker=dict(color=COLOR[field], line=dict(
                                color="rgb(105,105,105)", width=1)), opacity=1, visible='legendonly',
                            width=0.3, offset=0)
        elif field.split('_')[1] == 'ET':
            trace2 = go.Bar(x=data_frame.index, y=y, name=field.split('_kWh', 1)[0],
                            marker=dict(color=COLOR[field], line=dict(
                                color="rgb(105,105,105)", width=1)), opacity=1, visible='legendonly',
                            width=0.3, offset=0)
        else:
            raise ValueError('the specified analysis field is not in the right form: ', field)

        graph.append(trace2)

    return graph, data_frame.index,


def calc_table(E_analysis_fields, Q_analysis_fields, data_frame):
    analysis_fields = []
    total_perc = []
    median = []
    # find the three highest
    anchors = []
    load_names = []

    E_median = data_frame[E_analysis_fields].median().round(2).tolist()
    E_total = data_frame[E_analysis_fields].sum().round(2).tolist()
    if sum(E_total) > 0:
        E_total_perc = [str(x) + " (" + str(round(x / sum(E_total) * 100, 1)) + " %)" for x in E_total]
        for field in E_analysis_fields:
            anchors.append(calc_top_three_anchor_loads(data_frame, field))
            load_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        E_total_perc = ['0 (0%)'] * len(E_total)
        for field in E_analysis_fields:
            anchors.append('-')
            load_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
    analysis_fields.extend(E_analysis_fields)
    total_perc.extend(E_total_perc)
    median.extend(E_median)

    Q_median = (data_frame[Q_analysis_fields].median() / 1000).round(2).tolist()  # to MWh
    Q_total = data_frame[Q_analysis_fields].sum().round(2).tolist()
    if sum(Q_total) > 0:
        Q_total_perc = [str(x) + " (" + str(round(x / sum(Q_total) * 100, 1)) + " %)" for x in Q_total]
        for field in Q_analysis_fields:
            anchors.append(calc_top_three_anchor_loads(data_frame, field))
            load_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        Q_total_perc = ['0 (0%)'] * len(Q_total)
        for field in Q_analysis_fields:
            anchors.append('-')
            load_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')

    analysis_fields.extend(Q_analysis_fields)
    total_perc.extend(Q_total_perc)
    median.extend(Q_median)

    analysis_fields = filter(None, [x for field in analysis_fields for x in field.split('_kWh', 1)])

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 most irradiated']),
                     cells=dict(values=[load_names, total_perc, median, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list
