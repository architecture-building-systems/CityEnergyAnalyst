from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import numpy as np
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
import networkx as nx
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def network_plot(data_frame, path, title, output_path, analysis_fields):
    ''
    graph = nx.read_shp(path)
    #pos = nx.get_node_attributes(graph, 'pos')

    #data = list()
    #for hour in range(8760):
    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=go.Marker(
            showscale=True,
            # colorscale options
            # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
            # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
            colorscale='Hot',
            reversescale=True,
            color=[],
            size=40,
            colorbar=dict(
                thickness=30,
                title='Node Temperature',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))

    for i in range(len(graph.nodes())):
        x, y = graph.node.items()[i][0][0], graph.node.items()[i][0][1]
        node_trace['x'].append(x)
        node_trace['y'].append(y)

    #todo: begin with one timestep temperature, later add slider
    for data in data_frame[analysis_fields[0]]:
        number = np.round(data_frame[analysis_fields[0]][data][3300],0)
        node_trace['marker']['color'].append(number)
        node_info = analysis_fields[0].split('_', 1)[0] + ' ' + str(number)
        node_trace['text'].append(node_info)

    edge_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='lines',
        hoverinfo='text',
        line=go.Line(
            # colorscale options
            # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
            # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
            #colorscale='Hot',
            #reversescale=True,
            #color=[],
            color = '#888',
            width=[]
        )
    )
    '''    
    colorbar=dict(
        thickness=30,
        title='Edge Heat Loss',
        xanchor='left',
        titleside='right'
    )'''

    for edge in graph.edges():
        x0, y0 = edge[0][0], edge[0][1]
        x1, y1 = edge[1][0], edge[1][1]
        edge_trace['x'] += [x0, x1, None]
        edge_trace['y'] += [y0, y1, None]

    #todo: begin with one timestep edge loss, later add slider
    for data in data_frame[analysis_fields[1]]:
        number = data_frame[analysis_fields[1]][data][3300]
        number_normed = number/np.max(data_frame[analysis_fields[1]].ix[3300])
        diameter = data_frame['Diameters'].ix[data][0]
        edge_trace['line']['width'].append(np.round(diameter*100,0))
        #edge_trace['line']['color'].append(number_normed)
        edge_info = analysis_fields[1] + str(number)
        edge_trace['text'].append(edge_info)

    fig = go.Figure(data=go.Data([edge_trace, node_trace]),
                 layout=go.Layout(
                     title=title,
                     titlefont=dict(size=20),
                     showlegend=False,
                     hovermode='closest',
                     margin=dict(b=20, l=5, r=5, t=40),
                     xaxis=go.XAxis(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=go.YAxis(showgrid=False, zeroline=False, showticklabels=False)))

    plot(fig, auto_open=False, filename=output_path)
