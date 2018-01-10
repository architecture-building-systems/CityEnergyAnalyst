from plotly.offline import plot
import plotly.graph_objs as go
import numpy as np

def load_year_stacked(data_frame, analysis_fields, title, output_path):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    data_frame = data_frame[analysis_fields].sum()
    x = ["Absolute"]
    for field in analysis_fields:
        y = data_frame[field]
        trace = go.Bar(x = x, y= y, name = field)
        traces.append(trace)

    layout = go.Layout(barmode='stack', title='Stacked Bar with Pandas'
)
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)