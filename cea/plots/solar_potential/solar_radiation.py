from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO


def solar_radiation_district(data_frame, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,title=title, barmode='stack', yaxis=dict(title='Solar radiation [kWh/yr]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    x = data_frame["Name"].tolist()
    for field in analysis_fields:
        y = data_frame[field]
        trace = go.Bar(x=x, y=y, name=field)
        graph.append(trace)

    return graph

def calc_table(analysis_fields, data_frame):
    table = []
    # calculate variables for the analysis
    data_frame.set_index("DATE", inplace=True)
    resample_data_frame = data_frame.resample('M').sum()
    resample_data_frame.drop("T_out_dry_C", axis=1, inplace=True)
    resample_data_frame['TOTAL'] = resample_data_frame.sum(axis=1)

    for field in analysis_fields:
        trace = go.Scatter(x=data_frame.index, y=resample_data_frame[field], name=field)
        table.append(trace)
    layout = go.Layout(xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                       yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]))
    fig = go.Figure(data=table, layout=layout)
    # values = [resample_data_frame[x] for x in analysis_fields]
    #
    # table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
    #                         header=dict(
    #                             values=['Load Name', 'Peak Load [kW]', 'Yearly Demand [MWh]', 'Utilization [-]']),
    #                         cells=dict(values=[load_names, load_peak, load_total, load_utilization]))
    return fig