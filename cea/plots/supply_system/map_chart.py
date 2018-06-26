from __future__ import division
from __future__ import print_function


import os
import pandas as pd
import geopandas as gpd

import cea.config
import cea.inputlocator
import jinja2
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR



def map_chart(data_frame, locator, analysis_fields, title, output_path,
                         output_name_network, output_type_network,
                         building_connected_not_connected):
    # CALCULATE TABLE
    table_div = calc_table(data_frame, analysis_fields)

    # CACLUALTE MAP FILES
    buildings_json, edges_json, nodes_json = calc_graph(locator, output_name_network, output_type_network, building_connected_not_connected)

    # PLOT
    template_path = os.path.join(os.path.dirname(__file__), 'demo_maps.html')
    template = jinja2.Template(open(template_path, 'r').read())
    maps_html = template.render(buildings_json=buildings_json, edges_json=edges_json, nodes_json=nodes_json, table_div=table_div, title=title)
    print('Writing output to: %s' % output_path)
    with open(output_path, 'w') as f:
        f.write(maps_html)

    return {'data': maps_html}

def calc_graph(locator, output_name_network, output_type_network,
                         building_connected_not_connected):

    # map the buildings
    district_shp = locator.get_district_geometry()
    district_df = gpd.GeoDataFrame.from_file(district_shp)
    district_df = district_df.merge(building_connected_not_connected, on="Name", how="outer") # add type centralized, decentralized.
    district_crs = district_df.crs
    district_df = district_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    buildings_json = district_df.to_json(show_bbox=True)

    # map the edges of the network
    edges_shp = locator.get_network_layout_edges_shapefile(output_type_network, output_name_network)
    edges_df = gpd.GeoDataFrame.from_file(edges_shp)
    edges_df.crs = district_crs  # FIXME: i think the edges.shp file should include CRS information, no?
    edges_df = edges_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    edges_json = edges_df.to_json()

    # map the nodes of the network
    nodes_shp = locator.get_network_layout_nodes_shapefile(output_type_network, output_name_network)
    nodes_df = gpd.GeoDataFrame.from_file(nodes_shp)
    nodes_df.crs = district_crs  # FIXME: i think the nodes.shp file should include CRS information, no?
    nodes_df = nodes_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    nodes_json = nodes_df.to_json()

    return  buildings_json, edges_json, nodes_json

def calc_table(data_frame, analysis_fields):

    # calculate graph
    header_values = ["Name"] + analysis_fields
    cells_values = [data_frame[x].values for x in header_values]
    table = go.Table(domain=dict(x=[0, 1.0], y=[0, 0.2]),
                     header=dict(values=header_values),
                     cells=dict(values=cells_values))

    layout = go.Layout(images=LOGO)
    fig = go.Figure(data=[table], layout=layout)
    result = plot(fig, auto_open=False, output_type='div')

    return result




