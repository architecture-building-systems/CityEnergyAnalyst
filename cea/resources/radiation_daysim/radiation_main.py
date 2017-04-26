"""
Radiation engine and geometry handler for CEA
"""
from __future__ import division
import os
import pandas as pd
import time 
from cea.resources.radiation_daysim import settings
from cea.resources.radiation_daysim import create_gml

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
        
    #os.rename(file_name_txt, file_name_rad.replace(".txt", ".rad"))
    
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
    #srfmat = settings.TERRAIN_PARAMS['e_terrain']
    tcnt = 0
    for gmlterrain in gmlterrains:
        pytri_list = citygml_reader.get_pytriangle_list(gmlterrain)
        for pytri in pytri_list:
            py2radiance.RadSurface("terrain_srf"+ str(tcnt), pytri, "reflectance0.2", rad)
            tcnt+=1

    bldg_of_interest_name_list = ageometry_table.index.values
    gmlbldgs = citygml_reader.get_buildings()
    eligible_bldgs, n_eligible_bldgs = filter_bldgs_of_interest(gmlbldgs, bldg_of_interest_name_list, citygml_reader)

    for n_gmlbldg in n_eligible_bldgs:
        pypolgon_list = citygml_reader.get_pypolygon_list(n_gmlbldg)
        nbldg_cnt = 0
        for pypolygon in pypolgon_list:
            py2radiance.RadSurface("surroundingbldgs"+ str(nbldg_cnt), pypolygon, "reflectance0.2", rad)
            nbldg_cnt+=1

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
            if 0.0 < wwr < 1.0:
                window = fetch.shape2shapetype(modify.uniform_scale(facade, wwr, wwr, wwr, ref_pypt))
                window_list.append(window)
                create_radiance_srf(window, "win"+str(bcnt)+str(fcnt), "win" + str(ageometry_table['type_win'][bldg_name]), rad)

                #TODO: this next line is creating the error messages
                b_facade_cmpd = fetch.shape2shapetype(construct.boolean_difference(facade, window))

                hole_facade = fetch.geom_explorer(b_facade_cmpd, "face")[0]
                wall_list.append(hole_facade)

                #triangulate the wall with hole
                tri_facade_list = construct.simple_mesh(hole_facade)
                for tri_bface in tri_facade_list:
                    create_radiance_srf(tri_bface, "wall"+str(bcnt)+str(fcnt), 
                                        "wall" + str(ageometry_table['type_wall'][bldg_name]), rad)

            elif wwr == 1.0:
                create_radiance_srf(facade, "win"+str(bcnt)+str(fcnt), "win" + str(ageometry_table['type_win'][bldg_name]), rad)
                window_list.append(facade)
            else:
                create_radiance_srf(facade, "wall"+str(bcnt)+str(fcnt), "wall" + str(ageometry_table['type_wall'][bldg_name]), rad)
                wall_list.append(facade)
            fcnt+=1

            
        rcnt = 0
        for roof in roof_list:
            create_radiance_srf(roof, "roof"+str(bcnt)+str(rcnt), "roof" + str(ageometry_table['type_roof'][bldg_name]), rad)
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
    
def execute_daysim(bldg_dict_list,aresults_path, rad, aweatherfile_path, rad_params):
    """
    This is the main routine of the Daysim calculation
    :param bldg_dict_list: array of dicts storing ID's of surfaces of all buildings.
    :type narray
    :param aresults_path: path to folder where to store the daysim project.
    :type path to folder
    :param rad: Pyliburo object needed to initialize radiance and daysim
    :type pyliburo object
    :param aweatherfile_path: location of weather file
    :type path to folder
    :param rad_params: dict storing dafault parameters of daysim
    :return: <building>_geometry.csv
            'BUILDING': name of building
             'SURFACE': ID of surface
             'Xcoor': geolocation of centroid in X
             'Ycoor': geolocation of centroid in Y
             'Zcoor': geolocation of centroid in Z
              'Xdir': orientation of surface in  X
              'Ydir': orientation of surface in  Y
              'Zdir': orientation of surface in  Z
              'AREA_m2': area of surface
              'TYPE': type of surface, e.g., wall, roof, window.

             <building>_insolation_whm2.csv
             'srf': 8760 data points for every surface ID in the building

    :rtype: comma delimeted files

    """
    sensor_pt_list = []
    sensor_dir_list = []
    daysim_dir = os.path.join(aresults_path, "daysim_project")
    rad.initialise_daysim(daysim_dir)

    # transform weather file
    rad.execute_epw2wea(aweatherfile_path)
    rad.execute_radfiles2daysim()
    print rad
    all_sensor_srf_dict_2dlist = []
    for bldg_dict in bldg_dict_list:
        bldg_name = bldg_dict["name"]
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
    print 'starting Daysim radiation simulation'
    rad.execute_gen_dc("w/m2")
    rad.execute_ds_illum()
    solar_res = rad.eval_ill_per_sensor()
    print 'Daysim radiation finished - proceed to save results'
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
            
        srf_properties = pd.DataFrame(srf_properties, columns=['BUILDING', 'SURFACE', 'Xcoor','Ycoor', 'Zcoor',
                                      'Xdir', 'Ydir', 'Zdir', 'AREA_m2',
                                      'TYPE'])
        
        srf_properties.to_csv(os.path.join(aresults_path, bldg_name + '_geometry.csv'), index=None)
        zipped_solar_res = zip(*srf_solar_results)
        srf_solar_results = pd.DataFrame(zipped_solar_res[1:], columns = zipped_solar_res[0])
        srf_solar_results.to_csv(os.path.join(aresults_path, bldg_name + '_insolation_Whm2.csv'), index=None)
        
    #construct.visualise_falsecolour_topo(sum_res_list, occface_list, backend = "wx")
    print 'execute daysim', 'done'

def calc_radiation(weatherfile_path, locator):

    # local variables
    building_surface_properties = reader_surface_properties(locator=locator,
                                                            input_shp=locator.get_building_architecture())

    results_path = locator.get_solar_radiation_folder()

    # city gml reader
    citygml_reader = pycitygml.Reader()
    citygml_filepath = locator.get_building_geometry_citygml()
    citygml_reader.load_filepath(citygml_filepath)

    # Simulation
    daysim_mat = locator.get_daysim_mat()
    rad = py2radiance.Rad(daysim_mat, results_path)
    add_rad_mat(daysim_mat, building_surface_properties)

    bldg_dict_list = geometry2radiance(rad, building_surface_properties, citygml_reader)

    rad.create_rad_input_file()
    time1 = time.time()
    execute_daysim(bldg_dict_list, results_path, rad, weatherfile_path, settings.RAD_PARMS)
    
    # execute daysim
    time2 = time.time()
    time3 = time2-time1
    print "TIME TAKEN: ", time3/60.0

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
    fields = ['Name', 'G_win', 'win_wall', 'rtn_win', 'gtn_win', 'btn_win', "type_win" ]
    fields2 = ['Name', 'r_roof', 'g_roof', 'b_roof', 'spec_roof', 'rough_roof', "type_roof" ]
    fields3 = ['Name', 'r_wall', 'g_wall', 'b_wall', 'spec_wall', 'rough_wall', "type_wall" ]
    surface_properties = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')
    
    return surface_properties.set_index('Name').round(decimals=2)


def main(locator, weather_path):
    # Create City GML file (this is necesssary only once).
    output_folder = locator.get_building_geometry_citygml()
    input_buildings_shapefile = locator.get_district()
    input_terrain_raster = locator.get_terrain()
    create_gml.create_citygml(input_buildings_shapefile, input_terrain_raster, output_folder)
    # calculate solar radiation
    calc_radiation(weather_path, locator)


if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()

    main(locator=locator, weather_path=weather_path)