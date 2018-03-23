from __future__ import division
from __future__ import print_function

import numpy as np
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def distance_loss_curve(data_frame, data_frame_2, analysis_fields, title, output_path, axis_title, plant_nodes):
    traces = []
    for field in analysis_fields:
        for plant_number in data_frame_2.index.values:
            y = data_frame[field].values
            #sort by distance
            y_old = np.vstack((np.array(data_frame_2.ix[plant_number]), y))
            y_new = np.vstack((np.array(data_frame_2.ix[plant_number]), y))
            y_new[0,:] = y_old[0,:][y_old[0,:].argsort()]
            y_new[1, :] = y_old[1, :][y_old[0, :].argsort()]
            if field.split('_')[2] == 'min':
                trace = go.Scatter(x=y_new[0], y=y_new[1], name=field.split('_', 1)[0]+'-'+field.split('_', 3)[2]+
                                                                ' Plant Node '+ str(plant_nodes[plant_number]),
                                   marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                                   line=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0]),
                                   dash='dash'))
            elif field.split('_')[2] == 'max':
                trace = go.Scatter(x=y_new[0], y=y_new[1], name=field.split('_', 1)[0]+'-'+field.split('_', 3)[2]+
                                                                ' Plant Node '+ str(plant_nodes[plant_number]),
                                   marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])),
                                   line=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0]),
                                   dash='dot'))
            else:
                trace = go.Scatter(x=y_new[0], y=y_new[1], name=field.split('_', 1)[0]+'-'+field.split('_', 3)[2]+
                                                                ' Plant Node '+ str(plant_nodes[plant_number]),
                                   marker=dict(color=COLOR.get_color_rgb(field.split('_', 1)[0])))

            traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title=axis_title), xaxis=dict(title='Distance from plant [m]'))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}