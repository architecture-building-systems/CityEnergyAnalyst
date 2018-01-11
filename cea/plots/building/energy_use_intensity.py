from plotly.offline import plot
import plotly.graph_objs as go


def energy_use_intensity(data_frame, analysis_fields, title, output_path):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    area = data_frame["Af_m2"]
    data_frame = data_frame[analysis_fields]
    x = ["Absolute [MWh/yr]", "Relative [kWh/m2.yr]"]
    for field in analysis_fields:
        y = [data_frame[field], data_frame[field]/area*1000]
        trace = go.Bar(x = x, y= y, name = field.split('_', 1)[0])
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack')
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)