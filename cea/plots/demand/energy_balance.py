from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
import pandas as pd


def energy_balance(data_frame, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,title=title, barmode='relative', yaxis=dict(title='Energy balance [MWh/month]', domain=[0.35, 1.0]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def calc_graph(analysis_fields, data_frame):
    # calculate losses in data frame
    data_frame['Q_loss_heat_kWh'] = -abs(data_frame['Qhsf_kWh'] - data_frame['Qhs_kWh'])

    data_frame['Qcsf_sen_kWh'] = -(data_frame['Qcsf_kWh'] - data_frame['Qcsf_lat_kWh'])
    data_frame['Q_loss_cool_kWh'] = abs(data_frame['Qcsf_sen_kWh'] - data_frame['Qcs_sen_kWh'])

    data_frame['Q_trans_heat_wall_kWh'] = data_frame["Q_trans_wall_kWh"][data_frame["Q_trans_wall_kWh"] > 0]
    data_frame['Q_trans_cool_wall_kWh'] = data_frame["Q_trans_wall_kWh"][data_frame["Q_trans_wall_kWh"] < 0]
    data_frame['Q_trans_heat_vent_kWh'] = data_frame["Q_trans_vent_kWh"][data_frame["Q_trans_vent_kWh"] > 0]
    data_frame['Q_trans_cool_vent_kWh'] = data_frame["Q_trans_vent_kWh"][data_frame["Q_trans_vent_kWh"] < 0]
    data_frame['Q_trans_heat_wind_kWh'] = data_frame["Q_trans_wind_kWh"][data_frame["Q_trans_wind_kWh"] > 0]
    data_frame['Q_trans_cool_wind_kWh'] = data_frame["Q_trans_wind_kWh"][data_frame["Q_trans_wind_kWh"] < 0]
    data_frame['Q_trans_heat_roof_kWh'] = data_frame["Q_trans_roof_kWh"][data_frame["Q_trans_roof_kWh"] > 0]
    data_frame['Q_trans_cool_roof_kWh'] = data_frame["Q_trans_roof_kWh"][data_frame["Q_trans_roof_kWh"] < 0]
    data_frame['Q_trans_heat_base_kWh'] = data_frame["Q_trans_base_kWh"][data_frame["Q_trans_base_kWh"] > 0]
    data_frame['Q_trans_cool_base_kWh'] = data_frame["Q_trans_base_kWh"][data_frame["Q_trans_base_kWh"] < 0]

    analysis_fields.append('Q_trans_heat_wall_kWh')
    analysis_fields.append('Q_trans_cool_wall_kWh')
    analysis_fields.append('Q_trans_heat_vent_kWh')
    analysis_fields.append('Q_trans_cool_vent_kWh')
    analysis_fields.append('Q_trans_heat_wind_kWh')
    analysis_fields.append('Q_trans_cool_wind_kWh')
    analysis_fields.append('Q_trans_heat_roof_kWh')
    analysis_fields.append('Q_trans_cool_roof_kWh')
    analysis_fields.append('Q_trans_heat_base_kWh')
    analysis_fields.append('Q_trans_cool_base_kWh')
    analysis_fields.append('Qcsf_sen_kWh')

    # calculate graph
    graph = []
    data_frame.index = pd.to_datetime(data_frame.index)
    new_data_frame = (data_frame.resample("M").sum()/1000).round(2) # to MW
    new_data_frame["month"] = new_data_frame.index.strftime("%B")
    #total = new_data_frame[analysis_fields].sum(axis=1)
    for field in analysis_fields:
        y = new_data_frame[field]
        #total_perc = (y/total*100).round(2).values
        #total_perc_txt = ["("+str(x)+" %)" for x in total_perc]
        trace = go.Bar(x=new_data_frame["month"], y=y, name=field.split('_kWh', 1)[0]) #, text = total_perc_txt)
        graph.append(trace)

    return graph

def calc_table(analysis_fields, data_frame):

    data_frame.index = pd.to_datetime(data_frame.index)

    total = (data_frame[analysis_fields].sum(axis=0)/1000).round(2).tolist() # to MW
    total_perc = [str(x)+" ("+str(round(x/sum(total)*100,1))+" %)" for x in total]

    new_data_frame = (data_frame.resample("M").sum() / 1000).round(2)  # to MW
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