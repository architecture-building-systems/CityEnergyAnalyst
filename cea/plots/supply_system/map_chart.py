from __future__ import division
from __future__ import print_function

import os

import geopandas as gpd
import jinja2
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def map_chart(data_frame, locator, analysis_fields, title, output_path,
              output_name_network, output_type_network,
              building_connected_not_connected):
    # CALCULATE TABLE
    table_div, header_values, cells_values = calc_table(data_frame, analysis_fields)

    # CALCULATE MAP FILES
    streets_json, buildings_json, edges_json, nodes_json = calc_graph(locator, output_name_network, output_type_network,
                                                                      building_connected_not_connected)

    # PLOT
    template_path = os.path.join(os.path.dirname(__file__), 'map_location_size_customers_energy_system.html')
    template = jinja2.Template(open(template_path, 'r').read())
    maps_html = template.render(buildings_json=buildings_json, edges_json=edges_json, nodes_json=nodes_json,
                                streets_json=streets_json, table_div=table_div, title=title,
                                header_values=header_values, cells_values=cells_values)
    print('Writing output to: %s' % output_path)
    with open(output_path, 'w') as f:
        f.write(maps_html)

    return {'data': maps_html}


def calc_graph(locator, output_name_network, output_type_network,
               building_connected_not_connected):
    # map the buildings
    district_shp = locator.get_district_geometry()
    district_df = gpd.GeoDataFrame.from_file(district_shp)
    district_df = district_df.merge(building_connected_not_connected, on="Name", how="outer")
    district_df["Type"] = district_df["Type"].fillna(
        "SURROUNDINGS")  # add type centralized, decentralized and clear with surroundings
    district_crs = district_df.crs
    district_df = district_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    buildings_json = district_df.to_json(show_bbox=True)

    # map the streets
    streets_shp = locator.get_street_network()
    streets_df = gpd.GeoDataFrame.from_file(streets_shp)
    streets_df.crs = district_crs  # FIXME: i think the edges.shp file should include CRS information, no?
    streets_df = streets_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    streets_json = streets_df.to_json()

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

    return streets_json, buildings_json, edges_json, nodes_json


def calc_table(data_frame, analysis_fields):
    # calculate graph
    header_values = ["Name"] + analysis_fields
    cells_values = [list(data_frame.index.values)] + [list(data_frame[x].values) for x in analysis_fields]

    table = go.Table(domain=dict(x=[0, 0.7], y=[0, 1]),
                     header=dict(values=header_values),
                     cells=dict(values=cells_values))

    layout = go.Layout(images=LOGO)
    fig = go.Figure(data=[table], layout=layout)
    result = plot(fig, auto_open=False, output_type='div')

    return result, header_values, cells_values
