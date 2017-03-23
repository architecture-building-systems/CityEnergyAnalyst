"""
Radiation engine and geometry handler for CEA
"""

import os
import pandas as pd
import math
import time 
from cea.resources.radiation_daysim import settings

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
    
def geometry2radiance(rad, ageometry_table, citygml_reader):
    bldg_dict_list = []
    #translate the terrain into radiance surface 
    gmlterrains = citygml_reader.get_relief_feature()
    srfmat = settings.TERRAIN_PARAMS['e_terrain']
    tcnt = 0
    for gmlterrain in gmlterrains:
        pytri_list = citygml_reader.get_pytriangle_list(gmlterrain)
        for pytri in pytri_list:
            py2radiance.RadSurface("terrain_srf"+ str(tcnt), pytri, str(srfmat), rad)
            tcnt+=1
    
    bldg_of_interest_name_list = ageometry_table.index.values
    gmlbldgs = citygml_reader.get_buildings()
    eligible_bldgs, n_eligible_bldgs = filter_bldgs_of_interest(gmlbldgs, bldg_of_interest_name_list, citygml_reader)
    
    bcnt = 0
    for gmlbldg in eligible_bldgs:
        bldg_dict = {}
        window_list = []
        
        bldg_name = citygml_reader.get_gml_id(gmlbldg) 
        pypolgon_list = citygml_reader.get_pypolygon_list(gmlbldg)
        geo_solid = construct.make_occsolid_frm_pypolygons(pypolgon_list)
        facade_list, roof_list, footprint_list = gml3dmodel.identify_building_surfaces(geo_solid)
        wall_list = []

        wwr = ageometry_table["win_wall"][bldg_name]
        fcnt = 0
        for facade in facade_list:
            ref_pypt = calculate.face_midpt(facade)
            #offset the facade to create a window according to the wwr
            if wwr != 0.0 and wwr != 1.0:
                window = fetch.shape2shapetype(modify.uniform_scale(facade, wwr, wwr, wwr, ref_pypt))
                window_list.append(window)
                create_radiance_srf(window, "win"+str(bcnt)+str(fcnt), str(ageometry_table['G_win'][bldg_name]), rad)
                b_facade_cmpd = fetch.shape2shapetype(construct.boolean_difference(facade, window))
                hole_facade = fetch.geom_explorer(b_facade_cmpd, "face")[0]
                wall_list.append(hole_facade)
                #triangulate the wall with hole
                tri_facade_list = construct.simple_mesh(hole_facade)
                for tri_bface in tri_facade_list:
                    create_radiance_srf(tri_bface, "wall"+str(bcnt)+str(fcnt), str(ageometry_table['a_wall'][bldg_name]), rad)
                    
            elif wwr == 1.0:
                create_radiance_srf(facade, "win"+str(bcnt)+str(fcnt), str(ageometry_table['G_win'][bldg_name]), rad)
                window_list.append(facade)
            else:
                create_radiance_srf(facade, "wall"+str(bcnt)+str(fcnt), str(ageometry_table['a_wall'][bldg_name]), rad)
                wall_list.append(facade)
            fcnt+=1
            
        rcnt = 0
        for roof in roof_list:
            create_radiance_srf(roof, "roof"+str(bcnt)+str(rcnt), str(ageometry_table['a_roof'][bldg_name]), rad)
            rcnt+=1
            
        bldg_dict["name"] = bldg_name
        bldg_dict["windows"] = window_list
        bldg_dict["walls"] = wall_list
        bldg_dict["roofs"] = roof_list
        bldg_dict["footprints"] = footprint_list
        bldg_dict_list.append(bldg_dict)
        bcnt += 1
        
    return bldg_dict_list
    
def create_srf_dict(occface_list, srf_type, bldg_name):
    srf_dict_list = []
    for face in occface_list:
        sensor_srfs, sensor_pts, sensor_dirs = \
            gml3dmodel.generate_sensor_surfaces(face, settings.SEN_PARMS['X_DIM'], settings.SEN_PARMS['Y_DIM'])
        scnt = 0
        for sensor_srf in sensor_srfs:
            srf_dict = {}
            srf_dict["bldg_name"] = bldg_name
            srf_dict["occface"] = sensor_srf
            srf_dict["srf_type"] = srf_type
            srf_dict["sensor_pt"] = sensor_pts[scnt]
            srf_dict["sensor_dir"] = sensor_dirs[scnt]
            srf_dict_list.append(srf_dict)
            scnt+=1
    return srf_dict_list
    
def calc_sensors(bldg_dict):    
    sensor_srf_dict_list = []
    wall_list = bldg_dict["walls"]
    window_list = bldg_dict["windows"]
    roof_list = bldg_dict["roofs"]
    bldg_name = bldg_dict["name"]
    
    #grid up all the surfaces and return a srf dict that has all the information on the surface
    wall_sensor_srf_dict_list = create_srf_dict(wall_list, "wall", bldg_name)
    win_sensor_srf_dict_list = create_srf_dict(window_list, "window", bldg_name)
    rf_sensor_srf_dict_list = create_srf_dict(roof_list, "roof", bldg_name)
    sensor_srf_dict_list.extend(wall_sensor_srf_dict_list)
    sensor_srf_dict_list.extend(win_sensor_srf_dict_list)
    sensor_srf_dict_list.extend(rf_sensor_srf_dict_list)
    return sensor_srf_dict_list 
    
def create_sensor_input_file(rad):
    sensor_file_path = os.path.join(rad.data_folder_path, "sensor_points.pts")
    sensor_file = open(sensor_file_path, "w")
    sensor_pts_data = py2radiance.write_rad.sensor_file(rad.sensor_positions, rad.sensor_normals)
    sensor_file.write(sensor_pts_data)
    sensor_file.close()
    rad.sensor_file_path = sensor_file_path

def add_rad_mat(aresults_path, daysim_dir, bldg_name, ageometry_table):
    file_path = os.path.join(daysim_dir, 'rad',  "daysim_project_material")
    print file_path
    file_name_rad = file_path + ".rad"
    file_name_txt = file_path + ".txt"
    os.rename(file_name_rad, file_name_rad.replace(".rad", ".txt"))
    with open(file_name_txt, 'a') as write_file:
        for geo in ageometry_table.index.values:
            mat_name = str(ageometry_table['a_wall'][geo])
            mat_value = ageometry_table['a_wall'][geo]
            string = "void plastic " + mat_name + " 0 0 5 " + str(mat_value) + " " + str(mat_value) + " " + str(mat_value) \
                     + " 0.0000 0.0000"
            write_file.writelines('\n' + string + '\n')

            mat_name = str(ageometry_table['G_win'][geo])
            mat_value = ageometry_table['G_win'][geo]
            if not math.isnan(mat_value):
                string = "void plastic " + mat_name + " 0 0 5 " + str(mat_value) + " " + str(mat_value) + " " + str(mat_value) \
                + " 0.0000 0.0000"
                write_file.writelines('\n' + string + '\n')
            
            mat_name = str(ageometry_table['a_roof'][geo])
            mat_value = ageometry_table['a_roof'][geo]
            if not math.isnan(mat_value):
                string = "void plastic " + mat_name + " 0 0 5 " + str(mat_value) + " " + str(mat_value) + " " + str(mat_value) \
                         + " 0.0000 0.0000"
                write_file.writelines('\n' + string + '\n')

        write_file.close()
        
    os.rename(file_name_txt, file_name_rad.replace(".txt", ".rad"))
    
def execute_daysim(bldg_dict_list,aresults_path, rad, aweatherfile_path, rad_params, ageometry_table):
    sensor_pt_list = []
    sensor_dir_list = []
    daysim_dir = os.path.join(aresults_path, "daysim_project")
    rad.initialise_daysim(daysim_dir)
    # transform weather file
    rad.execute_epw2wea(aweatherfile_path)
    rad.execute_radfiles2daysim()
    
    all_sensor_srf_dict_2dlist = []
    for bldg_dict in bldg_dict_list:
        bldg_name = bldg_dict["name"]
        add_rad_mat(aresults_path, daysim_dir, bldg_name, ageometry_table)
        
        sensor_srf_dict_list = calc_sensors(bldg_dict)
        all_sensor_srf_dict_2dlist.append(sensor_srf_dict_list)
        for srf_dict in sensor_srf_dict_list:
            sensor_pt = srf_dict["sensor_pt"]
            sensor_pt_list.append(sensor_pt)
            sensor_dir = srf_dict["sensor_dir"]
            sensor_dir_list.append(sensor_dir)
            
    
    rad.set_sensor_points(sensor_pt_list, sensor_dir_list)
    create_sensor_input_file(rad)

    rad.write_radiance_parameters(rad_params['RAD_AB'], rad_params['RAD_AD'], rad_params['RAD_AS'],rad_params['RAD_AR'],
                                   rad_params['RAD_AA'], rad_params['RAD_LR'],rad_params['RAD_ST'],rad_params['RAD_SJ'],
                                   rad_params['RAD_LW'],rad_params['RAD_DJ'],rad_params['RAD_DS'],rad_params['RAD_DR'],
                                   rad_params['RAD_DP'])

    rad.execute_gen_dc("w/m2")
    rad.execute_ds_illum()
    solar_res = rad.eval_ill_per_sensor()
    sum_res_list = []
    occface_list = []
    scnt = 0
    for srf_dict_list in all_sensor_srf_dict_2dlist:
        srf_properties = []
        srf_solar_results = []
        nsrfs = len(srf_dict_list)
        res_columns = []
        for _ in range(nsrfs):
            res_columns.append("building_surface_name")
        for srf_dict in srf_dict_list:
            occface = srf_dict["occface"]
            #occface_list.append(occface)
            bldg_name = srf_dict["bldg_name"]
            srf_name = "srf" + str(scnt)
            mid_pt = srf_dict["sensor_pt"]
            mid_ptx = mid_pt[0]
            mid_pty = mid_pt[1]
            mid_ptz = mid_pt[2]
            nrml = srf_dict["sensor_dir"]
            nrmlx = nrml[0]
            nrmly = nrml[1]
            nrmlz = nrml[2]
            face_area = calculate.face_area(occface)
            srf_type = srf_dict["srf_type"]
            srf_properties.append((bldg_name, srf_name, mid_ptx, mid_pty, mid_ptz, nrmlx, nrmly, nrmlz, face_area, srf_type))
            
            #create csv for 8760 hours of results
            srf_res = solar_res[scnt]
            #sum_res = sum(srf_res)
            #sum_res_list.append(sum_res)
            asrf_solar_result = [srf_name]
            for res in srf_res:
                asrf_solar_result.append(res)
                
            srf_solar_results.append(asrf_solar_result)
            scnt+=1
            
        srf_properties = pd.DataFrame(srf_properties, columns=['building_name', 'surface_name', 'centre_point_x','centre_point_y', 'centre_point_z', 
                                      'surface_direction_x', 'surface_direction_y', 'surface_direction_z', 'surface_area_m2', 
                                      'surface_type'])
        
        srf_properties.to_csv(os.path.join(aresults_path, bldg_name + '_srf_properties.csv'), index=None)
        zipped_solar_res = zip(*srf_solar_results)
        srf_solar_results = pd.DataFrame(zipped_solar_res[1:], columns = zipped_solar_res[0])
        srf_solar_results.to_csv(os.path.join(aresults_path, bldg_name + '_srf_solar_results.csv'), index=None)
        
    #construct.visualise_falsecolour_topo(sum_res_list, occface_list, backend = "wx")
    print 'execute daysim', 'done'

def calc_radiation(geometry_table_name, weatherfile_path, locator):    

    # local variables
    building_surface_properties = reader_surface_properties(locator.get_building_architecture())
    results_path = locator.get_solar_radiation_folder()

    # city gml reader
    citygml_reader = pycitygml.Reader()
    citygml_filepath = locator.get_building_geometry_citygml()
    citygml_reader.load_filepath(citygml_filepath)

    # Simulation
    rad = py2radiance.Rad(locator.get_daysim_mat(), results_path)
    bldg_dict_list = geometry2radiance(rad, building_surface_properties, citygml_reader)
    rad.create_rad_input_file()
    time1 = time.time()
    execute_daysim(bldg_dict_list, results_path, rad, weatherfile_path, settings.RAD_PARMS, building_surface_properties)
    
    # execute daysim
    time2 = time.time()
    time3 = time2-time1
    print time3

def reader_surface_properties(input_shp):
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
    fields = ['Name', 'G_win', 'win_wall']
    fields2 = ['Name', 'a_roof']
    fields3 = ['Name', 'a_wall']
    surface_properties = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')
    
    return surface_properties.set_index('Name').round(decimals=2)

if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weatherfile_path = locator.get_default_weather()
    geometry_table_name = 'background_geometries'
    sensor_geometries_name = 'sensor_geometries'

    calc_radiation(geometry_table_name, weatherfile_path, locator)