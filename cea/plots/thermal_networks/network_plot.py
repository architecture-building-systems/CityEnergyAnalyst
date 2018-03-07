from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
import networkx as nx
from cea.plots.color_code import ColorCodeCEA
COLOR = ColorCodeCEA()

def network_plot(data_frame, path, title, output_path):
    ''
    graph = nx.read_shp(path)
    #pos = nx.get_node_attributes(graph, 'pos')

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
            size=20,
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

    #TODO: this is where to add data to nodes and edges
    #todo: begin with one timestep temperature, later add slider
    for data in data_frame['Temperature']:
        node_trace['marker']['color'].append(data)
        node_info = 'Temperature: ' + str(data)
        node_trace['text'].append(node_info)

    edge_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='lines',
        hoverinfo='none',
        line=go.Line(
            showscale=True,
            # colorscale options
            # 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
            # Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
            colorscale='Hot',
            reversescale=True,
            color=[],
            size=20,
            width=2,
            colorbar=dict(
                thickness=30,
                title='Node Temperature',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))


    for edge in graph.edges():
        x0, y0 = edge[0][0], edge[0][1]
        x1, y1 = edge[1][0], edge[1][1]
        edge_trace['x'] += [x0, x1, None]
        edge_trace['y'] += [y0, y1, None]

    #TODO: this is where to add data to edges
    #todo: begin with one timestep edge loss, later add slider
    for data in data_frame['q_loss']:
        node_trace['marker']['color'].append(data)
        node_info = 'Edge Heat Loss: ' + str(data)
        node_trace['text'].append(node_info)

    fig = go.Figure(data=go.Data([edge_trace, node_trace]),
                 layout=go.Layout(
                     title=title,
                     titlefont=dict(size=16),
                     showlegend=False,
                     hovermode='closest',
                     margin=dict(b=20, l=5, r=5, t=40),
                     xaxis=go.XAxis(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=go.YAxis(showgrid=False, zeroline=False, showticklabels=False)))

    plot(fig, auto_open=False, filename=output_path)