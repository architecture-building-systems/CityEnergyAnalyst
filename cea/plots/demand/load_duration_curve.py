from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot
from cea.plots.variable_naming import NAMING, LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()
import pandas as pd



def load_duration_curve(data_frame, analysis_fields, title, output_path):

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH

    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title,xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                       yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def calc_table(analysis_fields, data_frame):
    # calculate variables for the analysis
    load_peak = data_frame[analysis_fields].max().round(2).tolist()
    load_total = (data_frame[analysis_fields].sum() / 1000).round(2).tolist()

    # calculate graph
    load_utilization = []
    load_names = []
    # data = ''
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        # analysis_text = 'The peak demand registered for ' + NAMING[field.split('_', 1)[0]] + ' (' + \
        #                 field.split('_', 1)[0]+') ' +  'is equal to <b>' + str(max_value[field]) + ' kW'+'</b>. This value differs in <b>' + \
        #                 str(round((max_value[field] - mean_value) / mean_value * 100, 1)) +' %</b> with respect to the mean of the other peak demands. \n'
        # data = data+analysis_text
        load_utilization.append(evaluate_utilization(x, y))
        load_names.append(NAMING[field.split('_', 1)[0]] + ' (' + field.split('_', 1)[0] + ')')
    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                            header=dict(
                                values=['Load Name', 'Peak Load [kW]', 'Yearly Demand [MWh]', 'Utilization [-]']),
                            cells=dict(values=[load_names, load_peak, load_total, load_utilization]))
    return table

def calc_graph(analysis_fields, data_frame):

    graph = []
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        trace = go.Scatter(x=x, y=y, name=field.split('_', 1)[0], fill='tozeroy', opacity=0.8,
                           marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))
        graph.append(trace)

    return graph

def evaluate_utilization(x,y):
    dataframe = pd.DataFrame({'x':x, 'y':y})
    if 0 in dataframe['y'].values:
        index_occurrence = dataframe['y'].idxmin(axis=0, skipna=True)
        utilization_perc = round(dataframe.loc[index_occurrence,'x'],1)
        utilization_days = int(utilization_perc*8760/(24*100))
        return str(utilization_perc) + '% or ' + str(utilization_days) + ' days a year'
    else:
        return 'all year'