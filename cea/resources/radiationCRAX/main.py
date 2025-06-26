import os
import platform
import sys
import time
from itertools import repeat

import pandas as pd
import ast
import numpy as np
import rasterio
import shutil
import json
import geopandas as gpd

from osgeo import gdal
from rasterio.transform import rowcol
from shapely.geometry import Polygon
from shapely import wkt
from typing import Dict, Optional

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings
from cea.resources.radiation import geometry_generator
from cea.resources.radiation.daysim import GridSize, calc_sensors_building
from cea.resources.radiation.geometry_generator import BuildingGeometry
from cea.resources.radiation.main import read_surface_properties
from cea.resources.radiationCRAX import CRAXModel
from cea.utilities.parallel import vectorize

__author__ = "Xiaoyu Wang"
__copyright__ = ["Copyright 2025, Architecture and Building Systems - ETH Zurich"], \
                ["Copyright 2025, College of Architecture and Urban Planning (CAUP) - Tongji University"]
__credits__ = ["Xiaoyu Wang"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = [""]
__email__ = ["cea@arch.ethz.ch", "wanglittlerain@163.com"]
__status__ = "Production"


def generate_general_building_data_for_CRAX(shapefile_path, output_folder, output_file_name):
    """
    Reads a shapefile using GeoPandas to avoid issues with special characters in field names.
    Extracts the 'name', 'height_ag', and 'floors_ag' fields along with geometry data (building footprint).
    Saves the extracted information into a CSV file in the specified output folder.
    If the shapefile is not found, creates an empty CSV with the appropriate headers.
    """
    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, output_file_name)

    # If the shapefile does not exist, write an empty CSV and return
    if not os.path.exists(shapefile_path):
        # Define columns for the empty DataFrame
        columns = ["BuildingID", "BuildingBase", "BuildingFloors", "BuildingHeight"]
        empty_df = pd.DataFrame(columns=columns)
        empty_df.to_csv(output_csv, index=False)
        return output_csv

    try:
        # Read the shapefile using GeoPandas
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        raise Exception(f"Error reading shapefile with GeoPandas: {e}")

    # Convert all column names to lowercase to avoid case sensitivity issues
    gdf.columns = gdf.columns.str.lower()

    # Check if the required fields exist
    required_fields = ['name', 'height_ag', 'floors_ag']
    if not all(field in gdf.columns for field in required_fields):
        raise ValueError(f"Shapefile is missing required fields: {required_fields}")

    building_data = []
    for idx, row in gdf.iterrows():
        building_id = row['name']
        building_height = row['height_ag']
        building_floors = row['floors_ag']

        # Process geometry to extract building footprint coordinates
        geom = row.geometry
        if geom is None:
            building_base = None
        elif geom.geom_type == "Polygon":
            building_base = list(geom.exterior.coords)
        elif geom.geom_type == "MultiPolygon":
            # For multipolygons, extract exterior coordinates from each polygon
            building_base = [list(p.exterior.coords) for p in geom.geoms]
        else:
            building_base = None

        building_data.append({
            "BuildingID": building_id,
            "BuildingBase": building_base,
            "BuildingFloors": building_floors,
            "BuildingHeight": building_height
        })

    # Save the building data to a CSV file
    building_df = pd.DataFrame(building_data)
    building_df.to_csv(output_csv, index=False)

    return output_csv


def add_terrain_elevation(tif_path, building_data_csv):
    """
    Reads DEM data from a TIFF file and calculates the average elevation over the bounding
    box of each building's base. The elevation is then added to the CSV.
    """
    df = pd.read_csv(building_data_csv)

    # FIXME: Ensure bounding box of terrain includes all buildings
    with rasterio.open(tif_path) as src:
        dem_array = src.read(1)  # Read the first band of the DEM
        nodata = src.nodata  # Get the nodata value
        transform = src.transform  # Get the affine transform

        terrain_elevations = []
        for idx, row_data in df.iterrows():
            geom_data = row_data["BuildingBase"]
            try:
                # Parse the building base geometry: supports WKT or list format
                if isinstance(geom_data, str):
                    geom_data = geom_data.strip()
                    if geom_data.startswith('['):
                        coords = ast.literal_eval(geom_data)
                        polygon = Polygon(coords)
                    else:
                        polygon = wkt.loads(geom_data)
                else:
                    polygon = Polygon(geom_data)

                # Use the bounding box of the building base
                minx, miny, maxx, maxy = polygon.bounds

                # Convert bounding box coordinates to DEM row and column indices
                row_min, col_min = rowcol(transform, minx, maxy)  # Top-left corner
                row_max, col_max = rowcol(transform, maxx, miny)  # Bottom-right corner

                # Ensure indices are in order
                row_min, row_max = min(row_min, row_max), max(row_min, row_max)
                col_min, col_max = min(col_min, col_max), max(col_min, col_max)

                sample_values = []
                # Loop through the bounding box pixels
                for r in range(row_min, row_max + 1):
                    for c in range(col_min, col_max + 1):
                        val = dem_array[r, c]
                        if val != nodata:
                            sample_values.append(val)
                avg_elevation = np.mean(sample_values) if sample_values else np.nan
            except Exception as e:
                print(f"Error processing building index {idx}: {e}")
                avg_elevation = 0

            terrain_elevations.append(avg_elevation)

        df["TerrainElevation"] = terrain_elevations

    df.to_csv(building_data_csv, index=False)
    # print("Terrain elevation data added to CSV file.")


def add_window_wall_ratio(envelope_csv, building_data_csv):
    """
    Add the building CSV with window wall ratio (WWR) values from the envelope CSV in format of [e,s,w,n,top].
    If a building's WWR data is not found, assigns "0.3, 0.3, 0.3, 0.3, 0" as the value.
    The values added as a new column 'WindowWallRatio[e,s,w,n,top]' to the building CSV.
    """
    envelope_df = pd.read_csv(envelope_csv)
    building_df = pd.read_csv(building_data_csv)

    # Create a mapping from building name to its WWR values
    envelope_dict = envelope_df.set_index('name')[['wwr_north', 'wwr_west', 'wwr_east', 'wwr_south']].to_dict('index')

    wwr_list = []
    for index, row in building_df.iterrows():
        building_id = row['BuildingID']
        if building_id in envelope_dict:
            wwr_values = envelope_dict[building_id]
            wwr_str = f"{wwr_values['wwr_east']}, {wwr_values['wwr_south']}, {wwr_values['wwr_west']}, {wwr_values['wwr_north']}, 0"
        else:
            # If envelope data is not found, assign WWR as "0, 0, 0, 0, 0"
            wwr_str = "0.3, 0.3, 0.3, 0.3, 0"
        wwr_list.append(wwr_str)

    building_df["WindowWallRatio[e,s,w,n,top]"] = wwr_list
    building_df.to_csv(building_data_csv, index=False)
    # print(f"WindowWallRatio data added to file: {building_data_csv}")


def import_weather_file(source_file, target_dir):
    """
    import the weather.epw file from the source path to the target directory.
    """
    if not os.path.exists(source_file):
        print(f"weather.epw file not found: {source_file}")
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target_file = os.path.join(target_dir, "weather.epw")
    shutil.copy2(source_file, target_file)
    # print(f"Copied: {source_file} -> {target_file}")


def export_radiation_crax_config(config: cea.config.Configuration, output_folder: str, crax_result_folder: str,
                                 output_filename: str = "radiation_crax_config.json") -> Optional[Dict]:
    """
    Export radiation-crax configuration to JSON file

    :param config: CEA configuration object
    :param output_folder: Absolute path to output directory (will be stored as CRAX_input_folder)
    :param crax_result_folder: Result directory path (will be stored as CRAX_result_folder)
    :param output_filename: Output filename, default is radiation_crax_config.json
    :return: Dictionary containing configuration data on success, None on failure
    """

    try:
        # Build full file path
        output_path = os.path.join(output_folder, output_filename)

        # Get configuration sections
        radiation_section = config.sections['radiation-crax']

        # Build configuration dictionary from radiation-crax parameters
        config_data = {
            param_name: radiation_section.parameters[param_name].get()
            for param_name in radiation_section.parameters
        }

        # Add multiprocessing flag and I/O paths to output
        config_data.update({
            'multiprocessing': config.multiprocessing,
            'CRAX_input_folder': output_folder,
            'CRAX_result_folder': crax_result_folder
        })

        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)

        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        print(f"Configuration file saved to: {output_path}")
        return config_data

    except KeyError:
        print("Error: required configuration section not found in configuration")
        return None
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return None


def calc_sensors_zone_crax(building_names, locator, grid_size: GridSize, geometry_pickle_dir):
    sensors_coords_zone = []
    sensors_dir_zone = []
    sensors_total_number_list = []
    names_zone = []
    sensors_code_zone = []
    sensor_intersection_zone = []
    for building_name in building_names:
        building_geometry = BuildingGeometry.load(os.path.join(geometry_pickle_dir, 'zone', building_name))
        # get sensors in the building
        sensors_dir_building, \
        sensors_coords_building, \
        sensors_type_building, \
        sensors_area_building, \
        sensor_orientation_building, \
        sensor_intersection_building = calc_sensors_building(building_geometry, grid_size)

        # get the total number of sensors and store in lst
        sensors_number = len(sensors_coords_building)
        sensors_total_number_list.append(sensors_number)

        sensors_code = ['srf' + str(x) for x in range(sensors_number)]
        sensors_code_zone.append(sensors_code)

        # get the total list of coordinates and directions to send to daysim
        sensors_coords_zone.extend(sensors_coords_building)
        sensors_dir_zone.extend(sensors_dir_building)

        # get total list of intersections
        sensor_intersection_zone.append(sensor_intersection_building)

        # get the name of all buildings
        names_zone.append(building_name)

        # save sensors geometry result to disk
        locator.ensure_parent_folder_exists(locator.get_radiation_metadata(building_name))
        pd.DataFrame({'BUILDING': building_name,
                      'SURFACE': sensors_code,
                      'orientation': sensor_orientation_building,
                      'intersection': sensor_intersection_building,
                      'terrain_elevation': building_geometry.terrain_elevation,
                      'Xcoor': [x[0] for x in sensors_coords_building],
                      'Ycoor': [x[1] for x in sensors_coords_building],
                      'Zcoor': [x[2] for x in sensors_coords_building],
                      'Xdir': [x[0] for x in sensors_dir_building],
                      'Ydir': [x[1] for x in sensors_dir_building],
                      'Zdir': [x[2] for x in sensors_dir_building],
                      'AREA_m2': sensors_area_building,
                      'TYPE': sensors_type_building}).to_csv(locator.get_radiation_metadata(building_name), index=False)

    return sensors_coords_zone, sensors_dir_zone, sensors_total_number_list, names_zone, sensors_code_zone, sensor_intersection_zone


def sensor_generate_cea_daysim(building_names, locator, grid_size: GridSize, geometry_pickle_dir):
    # calculate sensors
    print("Calculating and sending sensor points")
    sensors_coords_zone, \
    sensors_dir_zone, \
    sensors_number_zone, \
    names_zone, \
    sensors_code_zone, \
    sensor_intersection_zone = calc_sensors_zone_crax(building_names, locator, grid_size, geometry_pickle_dir)

    # print(f"Starting Daysim simulation for buildings: {names_zone}")
    print(f"Total number of sensors: {len(sensors_coords_zone)}")


def run_daysim_sensor_generate(zone_building_names, locator, settings, geometry_pickle_dir, num_processes):
    list_of_building_names = [building_name for building_name in settings.buildings
                              if building_name in zone_building_names]
    # get chunks of buildings to iterate
    n_buildings_in_chunk = 1
    chunks = [list_of_building_names[i:i + n_buildings_in_chunk] for i in
              range(0, len(list_of_building_names), n_buildings_in_chunk)]

    grid_size = GridSize(walls=settings.walls_grid, roof=settings.roof_grid)

    num_chunks = len(chunks)

    if num_chunks == 1:
        sensor_generate_cea_daysim(chunks[0],
                                   locator,
                                   grid_size,
                                   geometry_pickle_dir)
    else:
        vectorize(sensor_generate_cea_daysim, num_processes)(
            chunks,
            repeat(locator, num_chunks),
            repeat(grid_size, num_chunks),
            repeat(geometry_pickle_dir, num_chunks)
        )


def calulate_cea_sensor_data(locator, config):
    print("verifying geometry files")
    zone_path = locator.get_zone_geometry()
    surroundings_path = locator.get_surroundings_geometry()

    print(f"zone: {zone_path}")
    print(f"surroundings: {surroundings_path}")

    zone_df = gpd.GeoDataFrame.from_file(zone_path)
    surroundings_df = gpd.GeoDataFrame.from_file(surroundings_path)

    verify_input_geometry_zone(zone_df)
    verify_input_geometry_surroundings(surroundings_df)

    # Ignore trees as model does not support them
    trees_df = gpd.GeoDataFrame(geometry=[], crs=zone_df.crs)

    geometry_staging_location = os.path.join(locator.get_solar_radiation_folder(), "radiance_geometry_pickle")

    print("Creating 3D geometry and surfaces")
    print(f"Saving geometry pickle files in: {geometry_staging_location}")
    # create geometrical faces of terrain and buildings
    terrain_raster = gdal.Open(locator.get_terrain())
    architecture_wwr_df = gpd.GeoDataFrame.from_file(locator.get_building_architecture()).set_index('name')

    # create custom config to override radiation settings
    _config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    _config.project = config.project
    _config.scenario = config.scenario
    _config.radiation.zone_geometry = config.radiation_crax.zone_geometry
    _config.radiation.surrounding_geometry = config.radiation_crax.surrounding_geometry
    _config.radiation.neglect_adjacent_buildings = config.radiation_crax.neglect_adjacent_buildings

    (geometry_terrain,
     zone_building_names,
     surroundings_building_names,
     tree_surfaces) = geometry_generator.geometry_main(_config,
                                                       zone_df,
                                                       surroundings_df,
                                                       trees_df,
                                                       terrain_raster,
                                                       architecture_wwr_df,
                                                       geometry_staging_location)

    run_daysim_sensor_generate(zone_building_names, locator, config.radiation_crax, geometry_staging_location,
                               num_processes=config.get_number_of_processes())  # Call the provided CEA mesh generation method


# def post_process_radiation_files(building_names, locator):
#     weather = epw_reader(locator.get_weather_file())
#     date = weather.date
#
#     for building_name in building_names:
#         radiation_file_path = locator.get_radiation_building(building_name)
#         radiation_file = pd.read_csv(radiation_file_path)
#
#         # Add date column
#         radiation_file['date'] = date
#
#         # Fix column names
#         radiation_file.rename(columns={"roofs_top":"roofs_top_kW",
#                                        "walls_e": "walls_east_kW",
#                                        "walls_n": "walls_north_kW",
#                                        "walls_s": "walls_south_kW",
#                                        "walls_w": "walls_west_kW",
#                                        "windows_e": "windows_east_kW",
#                                        "windows_n": "windows_north_kW",
#                                        "windows_s": "windows_south_kW",
#                                        "windows_w": "windows_west_kW",
#                                        }, inplace=True)
#
#         #  Add surface area
#         building_metadata = pd.read_csv(locator.get_radiation_metadata(building_name))
#         surface_area = building_metadata.groupby(['TYPE', 'orientation'])['AREA_m2'].sum()
#         existing_surface_directions = set()
#         for index, value in surface_area.items():
#             surface_direction = f"{index[0]}_{index[1]}"
#             existing_surface_directions.add(surface_direction)
#             radiation_file[f"{surface_direction}_m2"] = round(value, 2)
#         # Add missing surfaces to output
#         missing_surface_directions = SURFACE_DIRECTION_LABELS - existing_surface_directions
#         for surface_direction in missing_surface_directions:
#             radiation_file[f"{surface_direction}_kW"] = 0.0
#             radiation_file[f"{surface_direction}_m2"] = 0.0
#
#         radiation_file.set_index("date").to_csv(radiation_file_path)


def check_os():
    """
    Raise error if the operating system is not supported.

    Currently Intel Macs are not supported.
    """
    if sys.platform == "darwin" and platform.machine() == "x86_64":
        raise ValueError("Intel Macs are not supported.")

def main(config):
    check_os()

    print("Creating building geometry data CSV file for CRAX")
    #  reference case need to be provided here
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    #  the selected buildings are the ones for which the individual radiation script is run for
    #  this is only activated when in default.config, run_all_buildings is set as 'False'

    # Automatically create the subfolder "input_files_CRAX"
    input_folder = os.path.join(locator.get_solar_radiation_folder(), "input_files_CRAX")
    os.makedirs(input_folder, exist_ok=True)

    # Define input file paths of CEA
    zone_shapefile_path = locator.get_zone_geometry()
    surroundings_shapefile_path = locator.get_surroundings_geometry()
    envelope_csv = locator.get_building_architecture()
    tif_path = locator.get_terrain()

    # Step 1: Automatically generate building geometry data CSV
    zone_building_geometry_csv = generate_general_building_data_for_CRAX(zone_shapefile_path, input_folder,
                                                                         'zone_building_geometry.csv')
    
    # Step 2: Add terrain elevation data to the generated CSV
    add_terrain_elevation(tif_path, zone_building_geometry_csv)

    # Step 3: Add window wall ratio (WWR) data to the same CSV
    add_window_wall_ratio(envelope_csv, zone_building_geometry_csv)

    # Step 4: repeat step 1-3 for surrounding buildings if there's any.
    try:
        gdf_surroundings = gpd.read_file(surroundings_shapefile_path)
        if not gdf_surroundings.empty:
            surroundings_building_geometry_csv = generate_general_building_data_for_CRAX(surroundings_shapefile_path,
                                                                                         input_folder,
                                                                                         'surroundings_building_geometry.csv')
            add_terrain_elevation(tif_path, surroundings_building_geometry_csv)
            add_window_wall_ratio(envelope_csv, surroundings_building_geometry_csv)
    except Exception as e:
        print(f"Could not read surroundings shapefile: {e}")

    # import material properties of buildings
    print("Getting geometry materials")
    building_surface_properties = read_surface_properties(locator)
    building_surface_properties.to_csv(os.path.join(input_folder, 'building_materials.csv'))

    # import weather.epw for CRAX
    print("Getting weather.epw file")
    import_weather_file(locator.get_weather_file(), input_folder)

    # export cea.config to json
    print("Getting radiation_crax_config file")
    json_filename = "radiation_crax_config.json"
    json_path = os.path.join(input_folder, json_filename)
    json_abs_path = os.path.abspath(json_path)
    export_radiation_crax_config(config, input_folder, locator.get_solar_radiation_folder(), json_filename)

    # Grid generation by CEA workflow or CRAX method
    # Load the JSON file
    with open(os.path.join(input_folder, "radiation_crax_config.json"), "r", encoding="utf-8") as f:
        content = json.load(f)

    crax_bin_directory = content["crax-bin-directory"]
    calculate_sensor_data = content["calculate-sensor-data"]
    using_cea_sensor = content["using-cea-sensor"]

    CRAX_bin_path, CRAX_lib_path = CRAXModel.check_crax_exe_directory(crax_bin_directory)
    # Create an instance of CRAXModel
    CRAX_model = CRAXModel.CRAX(CRAX_bin_path, CRAX_lib_path)

    # FIXME: temp solution to get building surface area using cea method
    # if calculate_sensor_data or using_cea_sensor:
    if calculate_sensor_data:
        if using_cea_sensor:
            time1 = time.time()
            print("Using CEA method to generate the mesh.")
            calulate_cea_sensor_data(locator, config)
            print("Grid generation of CEA finished in %.2f mins" % ((time.time() - time1) / 60.0))
        else:
            time2 = time.time()
            print("Generating mesh using CRAXModel.")
            CRAX_model.run_mesh_generation(json_abs_path)  # Run mesh generation via CRAXModel
            print("Grid generation of CRAX finished in %.2f mins" % ((time.time() - time2) / 60.0))

    # Run radiation calculation after mesh generation (or directly if calculate_sensor_data is False)

    time3 = time.time()
    print("Running CRAX radiation calculation")
    CRAX_model.run_radiation(json_abs_path)  # Run radiation calculation via CRAXModel
    print("CRAX simulation finished in %.2f mins" % ((time.time() - time3) / 60.0))


if __name__ == '__main__':
    main(cea.config.Configuration())
