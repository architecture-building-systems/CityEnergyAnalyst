"""
A demo for creating the maps (based on the data provided in issue #1536)

Steps to run:

- ensure the zip files from issue #1536 are unpacked to the appropriate folders of the current scenario
- run the script
- open the output file (<scenario>/outputs/plots/demo/demo_maps.html)

NOTE: this demo needs to be added to the following functions:

- cea.plots.supply_system.main.Plots#map_location_size_customers_energy_system
- cea.plots.supply_system.map_chart.map_chart

Also note, that these maps are NOT plots in a strict sense and the overall plotting structure might need to be
abandoned.
"""
from __future__ import print_function, division

import os

import geopandas as gpd
import jinja2

import cea.config
import cea.inputlocator


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # map the buildings
    district_shp = locator.get_district_geometry()
    district_df = gpd.GeoDataFrame.from_file(district_shp)
    district_crs = district_df.crs
    district_df = district_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    buildings_json = district_df.to_json(show_bbox=True)

    # map the edges of the network
    edges_shp = locator.get_network_layout_edges_shapefile('DC', '')
    edges_df = gpd.GeoDataFrame.from_file(edges_shp)
    edges_df.crs = district_crs  # FIXME: i think the edges.shp file should include CRS information, no?
    edges_df = edges_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    edges_json = edges_df.to_json()

    # map the nodes of the network
    nodes_shp = locator.get_network_layout_nodes_shapefile('DC', '')
    nodes_df = gpd.GeoDataFrame.from_file(nodes_shp)
    nodes_df.crs = district_crs  # FIXME: i think the nodes.shp file should include CRS information, no?
    nodes_df = nodes_df.to_crs(epsg=4326)  # make sure that the geojson is coded in latitude / longitude
    nodes_json = nodes_df.to_json()

    template_path = os.path.join(os.path.dirname(__file__), 'demo_maps.html')
    template = jinja2.Template(open(template_path, 'r').read())

    # create html by applying the template
    table_div = '<table><tr><th>one</th><th>two</th></tr><tr><th>1.0</th><th>2.0</th></tr></table>'
    title = "jimeno's awesome plot"
    maps_html = template.render(buildings_json=buildings_json, edges_json=edges_json, nodes_json=nodes_json,
                                table_div=table_div, title=title)

    maps_html_path = os.path.join(locator.get_plots_folder('demo'), 'demo_maps.html')
    print('Writing output to: %s' % maps_html_path)
    with open(maps_html_path, 'w') as f:
        f.write(maps_html)


if __name__ == '__main__':
    main(cea.config.Configuration())
