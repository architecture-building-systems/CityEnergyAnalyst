from __future__ import division
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def solar_radiation_curve(data_frame, analysis_fields, title, output_path):

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    layout = dict(images=LOGO, title=title, yaxis=dict(domain=dict(x=[0, 1], y=[0.0, 0.7]),title='Solar Radiation [kW]'), yaxis2=dict(title='Temperature [C]', overlaying='y',
                   side='right'),xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(step='all')])),rangeslider=dict(),type='date'))

    fig = dict(data=traces_graph, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

def calc_graph(analysis_fields, data_frame):
    graph = []
    x = data_frame.DATE
    for field in analysis_fields:
        y = data_frame[field].values
        if field == "T_out_dry_C":
            trace = go.Scatter(x= x, y= y, name = field.split('t', 1)[0], yaxis='y2', opacity = 0.2)
        else:
            trace = go.Scatter(x= x, y= y, name = field,
                               marker=dict(color=COLOR.get_color_rgb(field)))
        graph.append(trace)
    return graph

