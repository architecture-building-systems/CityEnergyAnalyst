"""
Radiation engine and geometry handler for CEA
"""
from __future__ import division
import pandas as pd
import time
import math
from cea.resources.radiation_daysim import daysim_main, geometry_generator
import multiprocessing as mp

import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py2radiance as py2radiance

from geopandas import GeoDataFrame as gpdf
import cea.inputlocator
import cea.config

import fiona
import pytz, datetime

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Kian Wee Chen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_location_properties(geometry_zone_shp):

    from timezonefinder import TimezoneFinder
    with fiona.open(geometry_zone_shp) as shp:
        latitude = round(shp.crs['lat_0'],3)
        longitude = round(shp.crs['lon_0'],3)

    # get the time zone name
    tf = TimezoneFinder()
    time_zone = tf.timezone_at(lng=longitude, lat=latitude)
    time = pytz.timezone(time_zone).localize(datetime.datetime(2011,1,1)).strftime('%z')
    time_zone_num = int(time[:3])

    return latitude, longitude, time_zone_num

def create_radiance_srf(occface, srfname, srfmat, rad):
    bface_pts = fetch.pyptlist_frm_occface(occface)
    py2radiance.RadSurface(srfname, bface_pts, srfmat, rad)

def calc_transmissivity(G_value):
    return (math.sqrt(0.8402528435+0.0072522239*G_value*G_value)-0.9166530661)/0.0036261119/G_value

def add_rad_mat(daysim_mat_file, ageometry_table):
    file_path = daysim_mat_file
    roughness = 0.02
    specularity = 0.03
    with open(file_path, 'w') as write_file:
        # first write the material use for the terrain and surrounding buildings
        string = "void plastic reflectance0.2\n0\n0\n5 0.5360 0.1212 0.0565 0 0"
        write_file.writelines(string + '\n')

        written_mat_name_list = []
        for geo in ageometry_table.index.values:
            mat_name = "wall" + str(ageometry_table['type_wall'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_wall'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness
                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(
                    mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)

                write_file.writelines('\n' + string + '\n')

                written_mat_name_list.append(mat_name)

            mat_name = "win" + str(ageometry_table['type_win'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = calc_transmissivity(ageometry_table['G_win'][geo])
                mat_value2 = mat_value1
                mat_value3 = mat_value1

                string = "void glass " + mat_name + "\n0\n0\n3 " + str(mat_value1) + " " + str(mat_value2) + " " + str(
                    mat_value3)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)

            mat_name = "roof" + str(ageometry_table['type_roof'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_roof'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness

                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(
                    mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)

        write_file.close()


def terrain2radiance(rad, tin_occface_terrain):
    for id, face in enumerate(tin_occface_terrain):
        create_radiance_srf(face, "terrain_srf" + str(id), "reflectance0.2", rad)


def buildings2radiance(rad, building_surface_properties, geometry_3D_zone, geometry_3D_surroundings):
    # translate buildings into radiance surface
    fcnt = 0
    for bcnt, building_surfaces in enumerate(geometry_3D_zone):
        building_name = building_surfaces['name']
        for pypolygon in building_surfaces['windows']:
            create_radiance_srf(pypolygon, "win" + str(bcnt) + str(fcnt),
                                "win" + str(building_surface_properties['type_win'][building_name]), rad)
            fcnt += 1
        for pypolygon in building_surfaces['walls']:
            create_radiance_srf(pypolygon, "wall" + str(bcnt) + str(fcnt),
                                "wall" + str(building_surface_properties['type_wall'][building_name]), rad)
            fcnt += 1
        for pypolygon in building_surfaces['roofs']:
            create_radiance_srf(pypolygon, "roof" + str(bcnt) + str(fcnt),
                                "roof" + str(building_surface_properties['type_roof'][building_name]), rad)
            fcnt += 1

    for building_surfaces in geometry_3D_surroundings:
        ## for the surrounding buildings only, walls and roofs
        id = 0
        for pypolygon in building_surfaces['walls']:
            create_radiance_srf(pypolygon, "surroundingbuildings" + str(id), "reflectance0.2" , rad)
            id += 1
        for pypolygon in building_surfaces['roofs']:
            create_radiance_srf(pypolygon, "surroundingbuildings" + str(id), "reflectance0.2", rad)
            id += 1

    return


def reader_surface_properties(locator, input_shp):
    """
    This function returns a dataframe with the emissivity values of walls, roof, and windows
    of every building in the scene
    :param input_shp:
    :return:
    """

    # local variables
    architectural_properties = gpdf.from_file(input_shp).drop('geometry', axis=1)
    surface_database_windows = pd.read_excel(locator.get_envelope_systems(), "WINDOW")
    surface_database_roof = pd.read_excel(locator.get_envelope_systems(), "ROOF")
    surface_database_walls = pd.read_excel(locator.get_envelope_systems(), "WALL")

    # querry data
    df = architectural_properties.merge(surface_database_windows, left_on='type_win', right_on='code')
    df2 = architectural_properties.merge(surface_database_roof, left_on='type_roof', right_on='code')
    df3 = architectural_properties.merge(surface_database_walls, left_on='type_wall', right_on='code')
    fields = ['Name', 'G_win', "type_win"]
    fields2 = ['Name', 'r_roof', "type_roof"]
    fields3 = ['Name', 'r_wall', "type_wall"]
    surface_properties = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')

    return surface_properties.set_index('Name').round(decimals=2)

def radiation_singleprocessing(rad, geometry_3D_zone, locator, weather_path, settings):
    if settings.buildings == []:
        # get chunks of buildings to iterate
        chunks = [geometry_3D_zone[i:i + settings.n_buildings_in_chunk] for i in
                  range(0, len(geometry_3D_zone),
                        settings.n_buildings_in_chunk)]
    else:
        list_of_building_names = settings.buildings
        chunks = []
        for bldg_dict in geometry_3D_zone:
            if bldg_dict['name'] in list_of_building_names:
                chunks.append([bldg_dict])

    for chunk_n, building_dict in enumerate(chunks):
        daysim_main.isolation_daysim(chunk_n, rad, building_dict, locator, weather_path, settings)

def main(config):
    """
    This function makes the calculation of solar insolation in X sensor points for every building in the zone
    of interest. the number of sensor points depends on the size of the grid selected in the SETTINGS.py file and
    are generated automatically.

    :param config: Configuration object with the settings (genera and radiation-daysim)
    :type config: cea.config.Configuartion
    :return:
    """

    #  reference case need to be provided here
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    #  the selected buildings are the ones for which the individual radiation script is run for
    #  this is only activated when in default.config, run_all_buildings is set as 'False'

    settings = config.radiation_daysim

    # import material properties of buildings
    building_surface_properties = reader_surface_properties(locator=locator,
                                                            input_shp=locator.get_building_architecture())

    print "creating 3D geometry and surfaces"
    # create geometrical faces of terrain and buildingsL
    elevation, geometry_terrain, geometry_3D_zone, geometry_3D_surroundings = geometry_generator.geometry_main(locator,
                                                                                                    settings)

    print "Sending the scene: geometry and materials to daysim"
    # send materials
    daysim_mat = locator.get_temporary_file('default_materials.rad')
    rad = py2radiance.Rad(daysim_mat, locator.get_temporary_folder())
    add_rad_mat(daysim_mat, building_surface_properties)
    # send terrain
    terrain2radiance(rad, geometry_terrain)
    # send buildings
    buildings2radiance(rad, building_surface_properties, geometry_3D_zone, geometry_3D_surroundings)
    # create scene out of all this
    rad.create_rad_input_file()

    time1 = time.time()
    radiation_singleprocessing(rad, geometry_3D_zone, locator, config.weather, settings)

    print("Daysim simulation finished in %.2f mins" % ((time.time() - time1) / 60.0))

if __name__ == '__main__':
    main(cea.config.Configuration())

