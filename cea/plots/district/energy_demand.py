from plotly.offline import plot
import plotly.graph_objs as go

def energy_demand_district(data_frame, analysis_fields, title, output_path):
    traces = []
    x = data_frame["Name"].tolist()
    for field in analysis_fields:
        y = data_frame[field]
        trace = go.Bar(x = x, y= y, name = field.split('_', 1)[0])
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack', yaxis=dict(title='Energy Demand [MWh/yr]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)