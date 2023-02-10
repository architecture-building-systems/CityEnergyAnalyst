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
        print(sample_values[surface], row['AREA_m2'])
        value = sample_values[surface] * row['AREA_m2']
        return value

    sensor_data = geometry_data.apply(map_value, axis=1)

    print(sensor_data)


def generate_sample_data(locator, sample_buildings):
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
            # Convert to W
            sample_data[surface].append(data[f"{surface}_kW"]/data[f"{surface}_m2"]/1000)

    return sample_data


def main(config):
    sample_buildings = ["B1000"]

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    daysim_bin_path, daysim_lib_path = daysim.check_daysim_bin_directory(config.radiation.daysim_bin_directory,
                                                                         config.radiation.use_latest_daysim_binaries)

    print(f'Using Daysim binaries from path: {daysim_bin_path}')
    print(f'Using Daysim data from path: {daysim_lib_path}')

    print("verifying geometry files")
    zone_path = locator.get_zone_geometry()
    surroundings_path = locator.get_surroundings_geometry()
    print(f"zone: {zone_path}")
    print(f"surroundings: {surroundings_path}")

    zone_df = gpd.GeoDataFrame.from_file(zone_path)
    surroundings_df = gpd.GeoDataFrame.from_file(surroundings_path)[0:0]

    verify_input_geometry_zone(zone_df)
    verify_input_geometry_surroundings(surroundings_df)

    # import material properties of buildings
    print("Getting geometry materials")
    building_surface_properties = read_surface_properties(locator)
    building_surface_properties.to_csv(locator.get_radiation_materials())

    geometry_staging_location = os.path.join(locator.get_solar_radiation_folder(), "radiance_geometry_pickle")

    print("Creating 3D geometry and surfaces")
    print(f"Saving geometry pickle files in: {geometry_staging_location}")
    # create geometrical faces of terrain and buildings
    terrain_raster = gdal.Open(locator.get_terrain())
    architecture_wwr_df = gpd.GeoDataFrame.from_file(locator.get_building_architecture()).set_index('Name')

    geometry_terrain, zone_building_names, surroundings_building_names = geometry_generator.geometry_main(config,
                                                                                                          zone_df,
                                                                                                          surroundings_df,
                                                                                                          terrain_raster,
                                                                                                          architecture_wwr_df,
                                                                                                          geometry_staging_location)

    daysim_staging_location = os.path.join(locator.get_temporary_folder(), 'cea_radiation')
    cea_daysim = CEADaySim(daysim_staging_location, daysim_bin_path, daysim_lib_path)

    # create radiance input files
    print("Creating radiance material file")
    cea_daysim.create_radiance_material(building_surface_properties)
    print("Creating radiance geometry file")
    cea_daysim.create_radiance_geometry(geometry_terrain, building_surface_properties, zone_building_names,
                                        surroundings_building_names, geometry_staging_location)

    print("Converting files for DAYSIM")
    weather_file = locator.get_weather_file()
    print('Transforming weather files to daysim format')
    cea_daysim.execute_epw2wea(weather_file)
    print('Transforming radiance files to daysim format')
    cea_daysim.execute_radfiles2daysim()

    time1 = time.time()
    run_daysim_simulation(cea_daysim, sample_buildings, locator, config.radiation, geometry_staging_location,
                          num_processes=config.get_number_of_processes())

    # Remove staging location after everything is successful
    shutil.rmtree(daysim_staging_location)

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
