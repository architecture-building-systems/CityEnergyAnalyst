"""
This script extracts streets from Open street maps
"""

import os

import osmnx
import networkx.exception
import numpy as np
import pandas as pd
from packaging import version

import cea.config
import cea.inputlocator
from cea.datamanagement.surroundings_helper import get_zone_and_surr_in_projected_crs
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_bounding_box(locator):
    """
    Calculate the geographic bounding box for zone and surroundings geometries.
    
    This function combines zone and surroundings geometry data, removes duplicates,
    transforms to geographic coordinates, and calculates the total bounding box
    for use with OSM data extraction.
    
    :param locator: InputLocator instance providing paths to geometry files
    :type locator: cea.inputlocator.InputLocator
    :return: Bounding box coordinates [min_x, min_y, max_x, max_y] in geographic coordinates
    :rtype: pd.Series
    :raises ValueError: If geometry data is empty or invalid
    :raises RuntimeError: If coordinate transformation fails
    """
    try:
        # Load zone and surroundings data in projected CRS
        data_zone, data_dis = get_zone_and_surr_in_projected_crs(locator)
        
        # Validate that we have valid geometry data
        if data_zone.empty and data_dis.empty:
            raise ValueError("Both zone and surroundings geometry files are empty. Cannot calculate bounding box.")
        
        # Remove duplicates: exclude surroundings buildings that are already in zone
        if not data_dis.empty and "name" in data_dis.columns and "name" in data_zone.columns:
            data_dis = data_dis.loc[~data_dis["name"].isin(data_zone["name"])]
        
        # Prepare list of valid dataframes for concatenation
        valid_dataframes = []
        geographic_crs = get_geographic_coordinate_system()
        
        # Transform zone data to geographic coordinates if not empty
        if not data_zone.empty:
            try:
                data_zone_geo = data_zone.to_crs(geographic_crs)
                valid_dataframes.append(data_zone_geo)
            except Exception as e:
                raise RuntimeError(f"Failed to transform zone geometry to geographic coordinates: {e}")
        
        # Transform surroundings data to geographic coordinates if not empty
        if not data_dis.empty:
            try:
                data_dis_geo = data_dis.to_crs(geographic_crs)
                valid_dataframes.append(data_dis_geo)
            except Exception as e:
                raise RuntimeError(f"Failed to transform surroundings geometry to geographic coordinates: {e}")
        
        # Check if we have any valid data after transformations
        if not valid_dataframes:
            raise ValueError("No valid geometry data available after coordinate transformations.")
        
        # Concatenate all valid dataframes
        data = pd.concat(valid_dataframes, ignore_index=True, sort=True)
        
        # Validate that the concatenated data has geometry
        if data.empty or 'geometry' not in data.columns:
            raise ValueError("Combined geometry data is empty or missing geometry column.")
        
        # Calculate and validate bounding box
        result = data.total_bounds
        
        # Validate bounding box values
        if len(result) != 4:
            raise ValueError("Invalid bounding box calculation: expected 4 coordinates.")
        
        if np.any(np.isnan(result)) or np.any(np.isinf(result)):
            raise ValueError("Bounding box contains invalid values (NaN or infinite).")
        
        # Validate that min values are less than max values
        if result[0] >= result[2] or result[1] >= result[3]:
            raise ValueError("Invalid bounding box: minimum coordinates must be less than maximum coordinates.")
        
        return result
        
    except Exception as e:
        print(f"Error calculating bounding box: {e}")
        raise


def geometry_extractor_osm(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    bool_include_private_streets = config.streets_helper.include_private_streets
    shapefile_out_path = locator.get_street_network()

    # Determine to include private streets or not
    if bool_include_private_streets:
        type_streets = 'all'
    else:
        type_streets = 'all_public'

    # Get the bounding box coordinates
    assert os.path.exists(
        locator.get_surroundings_geometry()), 'Get surroundings geometry file first or the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max: %s'
    print("generating streets from Surroundings Geometry")
    bounding_box_surroundings_file = calc_bounding_box(locator)
    bounds = np.array(bounding_box_surroundings_file)
    
    # total_bounds format: [minx, miny, maxx, maxy] 
    # For geographic coordinates: [min_lon, min_lat, max_lon, max_lat]
    min_lon, min_lat, max_lon, max_lat = bounds

    # Get and clean the streets
    try:
        # Ensure backward compatibility with OSMnx versions
        if version.parse(osmnx.__version__) >= version.parse("2.0.0"):
            # OSMnx expects bbox as (left, bottom, right, top)
            # So we need: (min_lon, min_lat, max_lon, max_lat)
            bbox = (min_lon, min_lat, max_lon, max_lat)
        else:
            # OSMnx expects bbox as (north, south, east, west)
            # So we need: (max_lat, min_lat, max_lon, min_lon)
            bbox = (max_lat, min_lat, max_lon, min_lon)

        G = osmnx.graph_from_bbox(bbox=bbox, network_type=type_streets)
    except (ValueError, networkx.exception.NetworkXPointlessConcept):
        print("Unable to find streets in the area (empty graph returned from Open Street Maps). No streets will be extracted.")
        return
    
    # Convert graph to GeoDataFrame (edges only)
    try:
        # When nodes=False and edges=True, osmnx returns only the edges GeoDataFrame
        edges_gdf = osmnx.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)
        
        # Handle the case where osmnx might return a tuple (defensive programming)
        if isinstance(edges_gdf, tuple):
            edges_gdf = edges_gdf[1]  # Take the edges dataframe
        
        # Validate that we have valid edge data
        if edges_gdf.empty:
            print("No street edges found in the specified area. No streets will be extracted.")
            return
            
    except Exception as e:
        print(f"Error converting OSM graph to GeoDataFrame: {e}")
        return

    # Project coordinate system
    try:
        projected_data = edges_gdf.to_crs(get_projected_coordinate_system(float(min_lat), float(min_lon)))
        locator.ensure_parent_folder_exists(shapefile_out_path)
        projected_data[['geometry']].to_file(shapefile_out_path)
        print(f"Successfully extracted and saved streets to: {shapefile_out_path}")
    except Exception as e:
        print(f"Error projecting or saving street data: {e}")
        return


def main(config: cea.config.Configuration):
    """
    Create the streets.shp file.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    geometry_extractor_osm(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
