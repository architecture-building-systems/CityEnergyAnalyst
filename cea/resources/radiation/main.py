"""
Radiation engine and geometry handler for CEA
"""

import os
import shutil
import time
from itertools import repeat

import pandas as pd
import geopandas as gpd
from osgeo import gdal

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings
from cea.datamanagement.void_deck_migrator import migrate_void_deck_data
from cea.resources.radiation import daysim, geometry_generator
from cea.resources.radiation.daysim import GridSize
from cea.resources.radiation.radiance import CEADaySim
from cea.utilities import epwreader
from cea.utilities.parallel import vectorize

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Kian Wee Chen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def read_surface_properties(locator: cea.inputlocator.InputLocator) -> pd.DataFrame:
    """
    This function returns a dataframe with the emissivity values of walls, roof, and windows
    of every building in the scene

    :param cea.inputlocator.InputLocator locator: CEA InputLocator
    :returns pd.DataFrame: Dataframe with the emissivity values
    """

    # local variables
    architectural_properties = pd.read_csv(locator.get_building_architecture())
    surface_database_windows = pd.read_csv(locator.get_database_assemblies_envelope_window()).set_index("code")
    surface_database_roof = pd.read_csv(locator.get_database_assemblies_envelope_roof()).set_index("code")
    surface_database_walls = pd.read_csv(locator.get_database_assemblies_envelope_wall()).set_index("code")

    errors = {}
    def match_code(property_code_column: str, code_value_df: pd.DataFrame) -> pd.DataFrame:
        """
        Matches envelope code in building properties with code in the database and retrieves its values
        """
        building_prop_code = set(architectural_properties[property_code_column].unique())
        diff = building_prop_code.difference(code_value_df.index)

        if len(diff) > 0:
            errors[property_code_column] = diff

        df = pd.merge(architectural_properties[property_code_column], code_value_df,
                      left_on=property_code_column, right_on="code", how="left")
        return df

    # query data
    building_names = architectural_properties['name']
    df1 = match_code('type_win', surface_database_windows[['G_win']])
    df2 = match_code('type_roof', surface_database_roof[['r_roof']])
    df3 = match_code('type_wall', surface_database_walls[['r_wall']])

    if len(errors) > 0:
        raise ValueError(f"The following building properties were not found in the database: {errors}. "
                         f"Please check the ENVELOPE database: {locator.get_db4_assemblies_envelope_folder()}")

    surface_properties = pd.concat([building_names, df1, df2, df3], axis=1)

    return surface_properties.set_index('name').round(decimals=2)


def run_daysim_simulation(cea_daysim: CEADaySim, zone_building_names, locator, settings, geometry_pickle_dir, num_processes):
    weather_path = locator.get_weather_file()
    # check inconsistencies and replace by max value of weather file
    weatherfile = epwreader.epw_reader(weather_path)
    max_global = weatherfile['glohorrad_Whm2'].max()

    list_of_building_names = [building_name for building_name in settings.buildings
                              if building_name in zone_building_names]
    # get chunks of buildings to iterate
    chunks = [list_of_building_names[i:i + settings.n_buildings_in_chunk] for i in
              range(0, len(list_of_building_names),
                    settings.n_buildings_in_chunk)]

    write_sensor_data = settings.write_sensor_data
    radiance_parameters = {"rad_ab": settings.rad_ab, "rad_ad": settings.rad_ad, "rad_as": settings.rad_as,
                           "rad_ar": settings.rad_ar, "rad_aa": settings.rad_aa,
                           "rad_lr": settings.rad_lr, "rad_st": settings.rad_st, "rad_sj": settings.rad_sj,
                           "rad_lw": settings.rad_lw, "rad_dj": settings.rad_dj,
                           "rad_ds": settings.rad_ds, "rad_dr": settings.rad_dr, "rad_dp": settings.rad_dp}

    grid_size = GridSize(walls=settings.walls_grid, roof=settings.roof_grid)

    num_chunks = len(chunks)

    if num_chunks == 1:
        daysim.isolation_daysim(
            0, cea_daysim, chunks[0], locator, radiance_parameters, write_sensor_data, grid_size,
            max_global, weatherfile, geometry_pickle_dir)
    else:
        vectorize(daysim.isolation_daysim, num_processes)(
            range(0, num_chunks),
            repeat(cea_daysim, num_chunks),
            chunks,
            repeat(locator, num_chunks),
            repeat(radiance_parameters, num_chunks),
            repeat(write_sensor_data, num_chunks),
            repeat(grid_size, num_chunks),
            repeat(max_global, num_chunks),
            repeat(weatherfile, num_chunks),
            repeat(geometry_pickle_dir, num_chunks)
        )


def main(config):
    """
    This function makes the calculation of solar insolation in X sensor points for every building in the zone
    of interest. The number of sensor points depends on the size of the grid selected in the config file and
    are generated automatically.

    :param config: Configuration object with the settings (general and radiation)
    :type config: cea.config.Configuration
    :return:
    """

    #  reference case need to be provided here
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    migrate_void_deck_data(locator)
    #  the selected buildings are the ones for which the individual radiation script is run for
    #  this is only activated when in default.config, run_all_buildings is set as 'False'

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
    surroundings_df = gpd.GeoDataFrame.from_file(surroundings_path)

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

    daysim_staging_location = os.path.join(locator.get_temporary_folder(), 'cea_radiation')
    cea_daysim = CEADaySim(daysim_staging_location, daysim_bin_path, daysim_lib_path)

    # create radiance input files
    print("Creating radiance material file")
    cea_daysim.create_radiance_material(building_surface_properties)
    print("Creating radiance geometry file")
    cea_daysim.create_radiance_geometry(geometry_terrain, building_surface_properties, zone_building_names,
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
    run_daysim_simulation(cea_daysim, zone_building_names, locator, config.radiation, geometry_staging_location,
                          num_processes=config.get_number_of_processes())

    # Remove staging location after everything is successful
    shutil.rmtree(daysim_staging_location)

    print("Daysim simulation finished in %.2f mins" % ((time.time() - time1) / 60.0))


if __name__ == '__main__':
    main(cea.config.Configuration())
