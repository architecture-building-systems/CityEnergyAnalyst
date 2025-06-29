import os
import shutil
import time

import geopandas as gpd
import numpy as np
import pandas as pd
from osgeo import gdal

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings
from cea.resources.radiation import daysim, geometry_generator
from cea.resources.radiation.daysim import calc_sensors_zone, GridSize, write_aggregated_results, write_sensor_results
from cea.resources.radiation.main import read_surface_properties, run_daysim_simulation
from cea.resources.radiation.radiance import CEADaySim
from cea.utilities import epwreader


def generate_sensor_data(sample_values, geometry_data):
    def map_value(row):
        surface = f"{row['TYPE']}_{row['orientation']}"
        value = sample_values[surface]
        return value

    sensor_data = geometry_data.apply(map_value, axis=1)

    return sensor_data


def generate_sample_data(locator, sample_buildings):
    """
    returns sample data for each surface in W/m2
    """
    surfaces = {'windows_east',
                'windows_west',
                'windows_south',
                'windows_north',
                'walls_east',
                'walls_west',
                'walls_south',
                'walls_north',
                'roofs_top'}

    sample_data = {k: [] for k in surfaces}

    for building in sample_buildings:
        data = pd.read_csv(locator.get_radiation_building(building))
        for surface in sample_data.keys():
            # Convert to W/m2
            sample_data[surface].append(data[f"{surface}_kW"]*1000/data[f"{surface}_m2"])

    # Get mean of samples
    for k, v in sample_data.items():
        sample_data[k] = sum(v) / len(v)

    return sample_data


def fetch_simulation_buildings(sample_buildings, zone_df, buffer_m):
    simulation_buildings = set()
    for building in sample_buildings:
        buffer = zone_df[zone_df["name"] == building].buffer(buffer_m).geometry
        buildings_intersect = zone_df.intersects(buffer.values[0])

        for building_name in zone_df[buildings_intersect]["name"].values:
            simulation_buildings.add(building_name)

    return simulation_buildings


def main(config):
    sample_buildings = config.radiation_simplified.sample_buildings
    buffer_m = config.radiation_simplified.buffer
    config.radiation.buildings = sample_buildings

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    daysim_bin_path, daysim_lib_path = daysim.check_daysim_bin_directory(config.radiation.daysim_bin_directory,
                                                                         config.radiation.use_latest_daysim_binaries)

    print(f'Using Daysim binaries from path: {daysim_bin_path}')
    print(f'Using Daysim data from path: {daysim_lib_path}')

    print("verifying geometry files")
    zone_path = locator.get_zone_geometry()
    surroundings_path = locator.get_surroundings_geometry()
    trees_path = locator.get_tree_geometry()

    print(f"zone: {zone_path}")
    print(f"surroundings: {surroundings_path}")

    zone_df = gpd.GeoDataFrame.from_file(zone_path)
    if len(sample_buildings) == len(zone_df):
        raise ValueError("List of sample buildings is the same as all buildings. "
                         "Consider selecting a subset of buildings instead.")

    # Ignore surrounding buildings
    surroundings_df = gpd.GeoDataFrame.from_file(surroundings_path)[0:0]

    verify_input_geometry_zone(zone_df)
    verify_input_geometry_surroundings(surroundings_df)

    if os.path.exists(trees_path):
        print(f"trees: {trees_path}")
        trees_df = gpd.GeoDataFrame.from_file(trees_path)
    else:
        print("trees: None")
        # Create empty area if it does not exist
        trees_df = gpd.GeoDataFrame(geometry=[], crs=zone_df.crs)

    # import material properties of buildings
    print("Getting geometry materials")
    building_surface_properties = read_surface_properties(locator)
    locator.ensure_parent_folder_exists(locator.get_radiation_materials())
    building_surface_properties.to_csv(locator.get_radiation_materials())

    geometry_staging_location = os.path.join(locator.get_solar_radiation_folder(), "radiance_geometry_pickle")

    print("Creating 3D geometry and surfaces")
    print(f"Saving geometry pickle files in: {geometry_staging_location}")
    # create geometrical faces of terrain and buildings
    terrain_raster = gdal.Open(locator.get_terrain())
    architecture_wwr_df = gpd.GeoDataFrame.from_file(locator.get_building_architecture()).set_index('name')

    (geometry_terrain,
     zone_building_names,
     surroundings_building_names,
     tree_surfaces) = geometry_generator.geometry_main(config,
                                                       zone_df,
                                                       surroundings_df,
                                                       trees_df,
                                                       terrain_raster,
                                                       architecture_wwr_df,
                                                       geometry_staging_location)
    # Fetch simulation buildings based on proximity to sample buildings
    simulation_buildings = fetch_simulation_buildings(sample_buildings, zone_df, buffer_m)

    daysim_staging_location = os.path.join(locator.get_temporary_folder(), 'cea_radiation')
    cea_daysim = CEADaySim(daysim_staging_location, daysim_bin_path, daysim_lib_path)

    # create radiance input files
    print("Creating radiance material file")
    cea_daysim.create_radiance_material(building_surface_properties)
    print("Creating radiance geometry file")
    cea_daysim.create_radiance_geometry(geometry_terrain, building_surface_properties, simulation_buildings,
                                        surroundings_building_names, geometry_staging_location)

    if len(tree_surfaces) > 0:
        print("Creating radiance shading file")
        tree_lad = trees_df["density_tc"]
        cea_daysim.create_radiance_shading(tree_surfaces, tree_lad)

    print("Converting files for DAYSIM")
    weather_file = locator.get_weather_file()
    print('Transforming weather files to daysim format')
    cea_daysim.execute_epw2wea(weather_file)
    print('Transforming radiance files to daysim format')
    cea_daysim.execute_radfiles2daysim()

    time1 = time.time()
    run_daysim_simulation(cea_daysim, simulation_buildings, locator, config.radiation, geometry_staging_location,
                          num_processes=config.get_number_of_processes())

    # Remove staging location after everything is successful
    shutil.rmtree(daysim_staging_location)

    # Generate sample values
    sample_values = generate_sample_data(locator, sample_buildings)

    sensors_coords_zone, \
        sensors_dir_zone, \
        sensors_number_zone, \
        names_zone, \
        sensors_code_zone, \
        sensor_intersection_zone = calc_sensors_zone(zone_building_names, locator,
                                                     GridSize(walls=200, roof=200),
                                                     geometry_staging_location)

    weatherfile = epwreader.epw_reader(weather_file)
    date = weatherfile["date"]
    for building_name, sensors_number, sensor_code, sensor_intersection \
            in zip(names_zone, sensors_number_zone, sensors_code_zone, sensor_intersection_zone):

        geometry = pd.read_csv(locator.get_radiation_metadata(building_name)).set_index('SURFACE')
        sensor_data = generate_sensor_data(sample_values, geometry)

        # set sensors that intersect with buildings to 0
        sensor_data[np.array(sensor_intersection) == 1] = 0
        items_sensor_name_and_result = pd.DataFrame(sensor_data, index=sensor_code)

        # create summary and save to disk
        write_aggregated_results(building_name, items_sensor_name_and_result, locator, date)

        if config.radiation.write_sensor_data:
            sensor_data_path = locator.get_radiation_building_sensors(building_name)
            write_sensor_results(sensor_data_path, items_sensor_name_and_result)

    print("Daysim simulation finished in %.2f mins" % ((time.time() - time1) / 60.0))


if __name__ == '__main__':
    main(cea.config.Configuration())
