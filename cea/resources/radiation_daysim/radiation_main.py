"""
Radiation engine and geometry handler for CEA
"""
from __future__ import division
import os
import pandas as pd
import time
from cea.resources.radiation_daysim import settings
from cea.resources.radiation_daysim import create_gml, daysim_main, geometry_generator
import multiprocessing as mp

import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py3dmodel.modify as modify
import pyliburo.gml3dmodel as gml3dmodel
import pyliburo.pycitygml as pycitygml
import pyliburo.py2radiance as py2radiance

from geopandas import GeoDataFrame as gpdf

import cea.globalvar
import cea.inputlocator

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Kian Wee Chen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def create_radiance_srf(occface, srfname, srfmat, rad):
    bface_pts = fetch.pyptlist_frm_occface(occface)
    py2radiance.RadSurface(srfname, bface_pts, srfmat, rad)
    
def add_rad_mat(daysim_mat_file, ageometry_table):
    file_path = daysim_mat_file
    
    with open(file_path, 'w') as write_file:
        
        #first write the material use for the terrain and surrounding buildings 
        string = "void plastic reflectance0.2\n0\n0\n5 0.5360 0.1212 0.0565 0 0"
        write_file.writelines(string + '\n')
                
        written_mat_name_list = []
        for geo in ageometry_table.index.values:
            mat_name = "wall" + str(ageometry_table['type_wall'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_wall'][geo]
                mat_value2 = ageometry_table['g_wall'][geo]
                mat_value3 = ageometry_table['b_wall'][geo]
                mat_value4 = ageometry_table['spec_wall'][geo]
                mat_value5 = ageometry_table['rough_wall'][geo]
                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)
                         
                write_file.writelines('\n' + string + '\n')
                
                written_mat_name_list.append(mat_name)

            mat_name = "win" + str(ageometry_table['type_win'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['rtn_win'][geo]
                mat_value2 = ageometry_table['gtn_win'][geo]
                mat_value3 = ageometry_table['btn_win'][geo]

                string = "void glass " + mat_name + "\n0\n0\n3 " + str(mat_value1) + " " + str(mat_value2) + " " + str(mat_value3)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)
            
            mat_name = "roof" + str(ageometry_table['type_roof'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_roof'][geo]
                mat_value2 = ageometry_table['g_roof'][geo]
                mat_value3 = ageometry_table['b_roof'][geo]
                mat_value4 = ageometry_table['spec_roof'][geo]
                mat_value5 = ageometry_table['rough_roof'][geo]

                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)
                
        write_file.close()
    
def filter_bldgs_of_interest(gmlbldgs, bldg_of_interest_name_list, citygml_reader):
    eligible_bldgs = []
    n_eligible_bldgs = []
    for gmlbldg in gmlbldgs:
        bldg_name = citygml_reader.get_gml_id(gmlbldg) 
        if bldg_name not in bldg_of_interest_name_list:
            n_eligible_bldgs.append(gmlbldg)
        else:
            eligible_bldgs.append(gmlbldg)
            
    return eligible_bldgs, n_eligible_bldgs

def terrain2radiance(rad, tin_occface_terrain):
    for id, pytri in enumerate(tin_occface_terrain):
        py2radiance.RadSurface("terrain_srf"+ str(id), pytri, "reflectance0.2", rad)

def buildings2radiance(rad, ageometry_table, geometry_buildings):
    bldg_dict_list = []

    #translate buildings into radiance surface
    building_names = ageometry_table.index.values

    for bcnt, building_surfaces in enumerate(geometry_buildings):
        building_name = building_surfaces['Name']
        if building_name in building_names:
            for pypolygon in building_surfaces['windows']:
                create_radiance_srf(pypolygon, "win" + str(bcnt) + str(fcnt),
                                    "win" + str(ageometry_table['type_win'][building_name]), rad)
            for pypolygon in building_surfaces['walls']:
                create_radiance_srf(pypolygon, "wall" + str(bcnt) + str(fcnt),
                                   "wall" + str(ageometry_table['type_wall'][building_name]), rad)
            for pypolygon in building_surfaces['roofs']:
                create_radiance_srf(pypolygon, "roof" + str(bcnt) + str(rcnt),
                                    "roof" + str(ageometry_table['type_roof'][building_name]), rad)
                id += 1
        else:
            ## for the surrounding buildings
            id = 0
            for pypolygon in building_surfaces['windows']:
                py2radiance.RadSurface("surroundingbldgs"+ str(id), pypolygon, "reflectance0.2", rad)
                id+=1
            for pypolygon in building_surfaces['walls']:
                py2radiance.RadSurface("surroundingbldgs" + str(id), pypolygon, "reflectance0.2", rad)
                id += 1
            for pypolygon in building_surfaces['roofs']:
                py2radiance.RadSurface("surroundingbldgs" + str(id), pypolygon, "reflectance0.2", rad)
                id += 1


        bldg_dict["name"] = bldg_name
        bldg_dict["windows"] = window_list
        bldg_dict["walls"] = wall_list
        bldg_dict["roofs"] = roof_list
        bldg_dict["footprints"] = footprint_list
        bldg_dict_list.append(bldg_dict)
        
    return bldg_dict_list

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
    fields = ['Name', 'G_win', 'win_wall', 'rtn_win', 'gtn_win', 'btn_win', "type_win"]
    fields2 = ['Name', 'r_roof', 'g_roof', 'b_roof', 'spec_roof', 'rough_roof', "type_roof"]
    fields3 = ['Name', 'r_wall', 'g_wall', 'b_wall', 'spec_wall', 'rough_wall', "type_wall"]
    surface_properties = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')

    return surface_properties.set_index('Name').round(decimals=2)

def radiation_multiprocessing(rad, simul_params, bldg_dict_list, aresults_path, rad_params, aweatherfile_path):

    # get chunks to iterate and start multiprocessing
    chunks = [bldg_dict_list[i:i +simul_params['n_build_in_chunk']] for i in range(0, len(bldg_dict_list),
                                                                                   simul_params['n_build_in_chunk'])]

    # pool = mp.Pool()
    # joblist = []
    # for chunk_n, bldg_dict in enumerate(chunks):
    #     job = pool.apply_async(daysim_main.isolation_daysim,
    #                                 [chunk_n, rad, bldg_dict, aresults_path, rad_params, aweatherfile_path])
    #     joblist.append(job)
    # for i, job in enumerate(joblist):
    #     job.get(240)
    # pool.close()

    processes = []
    for chunk_n, bldg_dict in enumerate(chunks):
        process = mp.Process(target=daysim_main.isolation_daysim, args=(
            chunk_n, rad, bldg_dict, aresults_path, rad_params, aweatherfile_path,))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()

def radiation_singleprocessing(rad, bldg_dict_list, aresults_path, rad_params, aweatherfile_path):

    num_buildings = len(bldg_dict_list)
    chunk_n = None
    for i, bldg_dict in enumerate(bldg_dict_list):
        daysim_main.isolation_daysim(chunk_n, rad, bldg_dict, aresults_path, rad_params, aweatherfile_path)

def radiation_daysim_main(weatherfile_path, locator, zone_shp, district_shp,
                          input_terrain_raster, architecture_dbf):
    """
        This function makes the calculation of solar insolation in X sensor points for every building in the zone
    of interest. the number of sensor points depends on the size of the grid selected in the SETTINGS.py file and
    are generated automatically.
    :param weatherfile_path:
    :param locator:
    :param zone_shp:
    :param district_shp:
    :param input_terrain_raster:
    :param architecture_dbf:
    :return:
    """

    # import material properties of buildings
    building_surface_properties = reader_surface_properties(locator=locator,
                                                            input_shp=locator.get_building_architecture())

    print "creating 3D geometry and surfaces"
    # create geometrical faces of terrain and buildings
    geometry_terrain, geometry_buildings = geometry_generator.geometry_main(zone_shp, district_shp,
                                                                            input_terrain_raster, architecture_dbf)

    print "Sending the scene: geometry and materials to daysim"
    # send materials
    daysim_mat = locator.get_daysim_mat()
    results_path = locator.get_solar_radiation_folder()
    rad = py2radiance.Rad(daysim_mat, results_path)
    add_rad_mat(daysim_mat, building_surface_properties)
    # send terrain
    terrain2radiance(rad, geometry_terrain)
    # send buildings
    bldg_dict_list = buildings2radiance(rad, building_surface_properties, geometry_terrain, geometry_buildings)
    # create scene out of all this
    rad.create_rad_input_file()

    print "Daysim simulation starts"
    time1 = time.time()
    if (settings.SIMUL_PARAMS['multiprocessing'] and mp.cpu_count() > 1):
        radiation_multiprocessing(rad, settings.SIMUL_PARAMS, bldg_dict_list, results_path, settings.RAD_PARMS, weatherfile_path)
    else:
        radiation_singleprocessing(rad, bldg_dict_list, results_path, settings.RAD_PARMS, weatherfile_path)

    print "Daysim simulation finished in ", (time.time() - time1) / 60.0, " mins"

def main(locator, weather_path):

    district_shp = locator.get_district()
    zone_shp = locator.get_building_geometry()
    architecture_dbf = locator.get_building_architecture()
    input_terrain_raster = locator.get_terrain()

    # calculate solar radiation
    radiation_daysim_main(weather_path, locator, zone_shp=zone_shp, district_shp=district_shp,
         input_terrain_raster=input_terrain_raster, architecture_dbf=architecture_dbf)

if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    main(locator=locator, weather_path=weather_path)