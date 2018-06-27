from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR


def likelihood_chart(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph['layout'].update(images=LOGO, title=title, showlegend=True,
                                  yaxis=dict(title='Frequency [hours/yr]'),
                                  xaxis=dict(title='Ramp-up[MW] (-), Ramp-down[MW] (+)')
                                  )
    plot(traces_graph, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': traces_graph['layout']}

def calc_graph(analysis_fields, data_frame):

    # calculate graph
    labels = []
    hist_data = []
    colors = []
    for field in analysis_fields:
        hist_data.append(data_frame[field].values/1000000) # in kWh
        labels.append(NAMING[field])
        colors.append(COLOR[field])
    print(hist_data)
    graph = ff.create_distplot(hist_data, labels, bin_size=10, colors=colors)
    return graph
