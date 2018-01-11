from __future__ import division
from plotly.offline import plot
import plotly.graph_objs as go

def load_duration_curve(data_frame, analysis_fields, title, output_path):

    traces = []
    duration = range(8760)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        trace = go.Scatter(x= x, y= y, name = field.split('_', 1)[0], fill='tozeroy', opacity = 0.8)
        traces.append(trace)

    layout = go.Layout(title=title,
                       xaxis=dict(title='Duration Normalized [%]'),
                       yaxis=dict(title='Load [kW]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)