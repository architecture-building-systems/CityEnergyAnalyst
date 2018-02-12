from __future__ import division
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

import matplotlib
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
import pickle
import deap
import cea.globalvar
import pandas as pd
import numpy as np
import json
import os
import csv
import cea.inputlocator
from cea.optimization import supportFn as sFn

def individual_activation_curve(data_frame, analysis_fields_loads, analysis_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph= calc_graph(analysis_fields, data_frame)

    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Power Capacity [kW]', domain=[.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def calc_graph(analysis_fields, data_frame):
    data = data_frame['activation_units_data']/1000 # to kW
    graph = []
    for field in analysis_fields:
        y = data[field].values
        trace = go.Bar(x=data.index, y= y, name = field, marker=dict(color=COLOR.get_color_rgb(field)),
                        ) #fill='tonexty')
        graph.append(trace)
    return graph
