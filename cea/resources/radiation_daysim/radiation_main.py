"""
Radiation engine and geometry handler for CEA
"""

import os
import numpy as np
import pandas as pd
import math
import multiprocessing
from cea.resources.radiation_daysim import settings
from geopandas import GeoDataFrame as gpdf

from OCC import BRepGProp, GProp, BRep, TopoDS
from OCC.StlAPI import StlAPI_Reader
from OCC.TopAbs import TopAbs_REVERSED
from OCCUtils import face, Topology

import pyliburo.py3dmodel.construct as construct
import pyliburo.py3dmodel.fetch as fetch
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py3dmodel.modify as modify
import pyliburo.gml3dmodel as gml3dmodel
import pyliburo.pycitygml as pycitygml
import pyliburo.py2radiance as py2radiance

import cea.globalvar
import cea.inputlocator
from geopandas import GeoDataFrame as Gdf

__author__ = "Paul Neitzel"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_sensor_input_file(arad, abui):
    sensor_file_path = os.path.join(arad.data_folder_path, abui+"_sensor_points.pts")
    sensor_file = open(sensor_file_path, "w")
    sensor_pts_data = py2radiance.write_rad.sensor_file(arad.sensor_positions, arad.sensor_normals)
    sensor_file.write(sensor_pts_data)
    sensor_file.close()
    arad.sensor_file_path = sensor_file_path

def add_rad_mat(aresults_path, abui, ageometry_table):
    file_path = os.path.join(aresults_path, abui + '\\rad\\' + abui +
                             "_material")
    file_name_rad = file_path + ".rad"
    file_name_txt = file_path + ".txt"
    os.rename(file_name_rad, file_name_rad.replace(".rad", ".txt"))
    with open(file_name_txt, 'a') as write_file:
        name_int = 0
        for geo in ageometry_table.index.values:
            mat_name = ageometry_table['mat_name'][geo]
            mat_value = ageometry_table['mat_value'][geo]
            string = "void plastic " + mat_name + " 0 0 5 " + str(mat_value) + " " + str(mat_value) + " " + str(mat_value) \
                     + " 0.0000 0.0000"
            write_file.writelines('\n' + string + '\n')
            name_int += 1
        write_file.close()
    os.rename(file_name_txt, file_name_rad.replace(".txt", ".rad"))

def create_radiance_srf(occface, srfname, srfmat, arad):
    bface_pts = fetch.pyptlist_frm_occface(occface)
    py2radiance.RadSurface(srfname, bface_pts, srfmat, arad)
    
def triangulate_occface(occface):
    pyptlist = fetch.pyptlist_frm_occface(occface)
    d_face = construct.delaunay3d(pyptlist)
    compound = construct.boolean_common(d_face, occface)
    face_list = fetch.geomexplorer(compound, "face")
    return face_list
            
def geometry2radiance(arad, ageometry_table, ainput_path, citygml_reader):
    # add all geometries which are in "ageometry_table" to radiance
    bldg_dict_list = []
    gmlbldgs = citygml_reader.get_buildings()
    bcnt = 0
    for gmlbldg in gmlbldgs:
        bldg_dict = {}
        window_list = []
        
        bldg_name = citygml_reader.get_gml_id(gmlbldg) 
        pypolgon_list = citygml_reader.get_pypolygon_list(gmlbldg)
        geo_solid = construct.make_occsolid_frm_pypolygons(pypolgon_list)
        facade_list, roof_list, footprint_list = gml3dmodel.identify_building_surfaces(geo_solid)

        wwr = ageometry_table["fwindow"][bldg_name]
        print wwr
        fcnt = 0
        for facade in facade_list:
            ref_pypt = calculate.face_midpt(facade)
            #offset the facade to create a window according to the wwr
            if wwr != 0.0 and wwr != 1.0:
                window = fetch.shape2shapetype(modify.uniform_scale(facade, wwr, wwr, wwr, ref_pypt))
                window_list.append(window)
                create_radiance_srf(window, "win"+str(bcnt)+str(fcnt), ageometry_table['win_name'][bldg_name], arad)
                b_facade_cmpd = fetch.shape2shapetype(construct.boolean_difference(facade, window))
                hole_facade = fetch.geom_explorer(b_facade_cmpd, "face")[0]
                #triangulate the wall with hole
                tri_facade_list = construct.simple_mesh(hole_facade)
                for tri_bface in tri_facade_list:
                    create_radiance_srf(tri_bface, "wall"+str(bcnt)+str(fcnt), ageometry_table['wall_name'][bldg_name], arad)
                    
            elif wwr == 1.0:
                create_radiance_srf(facade, "win"+str(bcnt)+str(fcnt), ageometry_table['win_name'][bldg_name], arad)
            else:
                create_radiance_srf(facade, "wall"+str(bcnt)+str(fcnt), ageometry_table['wall_name'][bldg_name], arad)
            fcnt+=1
            
        rcnt = 0
        for roof in roof_list:
            create_radiance_srf(roof, "roof"+str(bcnt)+str(rcnt), ageometry_table['roof_name'][bldg_name], arad)
            rcnt+=1
            
        bldg_dict["name"] = bldg_name
        bldg_dict["windows"] = window_list
        bldg_dict["facades"] = facade_list
        bldg_dict["roofs"] = roof_list
        bldg_dict["footprints"] = footprint_list
        bldg_dict_list.append(bldg_dict)
        bcnt += 1
        
    return bldg_dict_list


def get_bui_props(bldg_dict, aresults_path, abui):

    bui_props = pd.DataFrame(columns=['roof_area', 'facade_area', 'roof_angle', 'bui_height', 'bui_min_z'])

    zs = []
    facade_area = []
    roof_area = []
    roof_angle = []
    
    facade_list = bldg_dict["facades"]
    roof_list = bldg_dict["roofs"]
    footprint_list = bldg_dict["footprints"]
    
    for facade in facade_list:
        fac_area = calculate.face_area(facade)
        facade_area.append(fac_area)
        
    for roof in roof_list:
        rf_area = calculate.face_area(roof)
        roof_area.append(rf_area)
        rf_normal = calculate.face_normal(roof)
        roof_angle.append(math.acos(rf_normal[2]))
        centre_pt = calculate.face_midpt(roof)
        zs.append(centre_pt[2])
        
    for ftprnt in footprint_list:
        centre_pt = calculate.face_midpt(ftprnt)
        zs.append(centre_pt[2])
        
    bui_roof_area = sum(roof_area)
    bui_roof_angle = sum(roof_angle)/len(roof_angle)
    bui_facade_area= sum(facade_area)
    bui_max_z =max(zs)
    bui_min_z = min(zs)

    bui_props.loc[abui] = [bui_roof_area, bui_facade_area, bui_roof_angle, bui_max_z-bui_min_z, bui_min_z]
    bui_props.to_csv(os.path.join(aresults_path, abui+'_props.csv'), index=None)


def calc_sensors(aresults_path, abui, ainput_path):

    sen_df = []
    fps_df = []
    
    facade_list = abui["facades"]
    roof_list = abui["roofs"]
    window_list = abui["windows"]
    all_faces = []
    all_faces.extend(facade_list)
    all_faces.extend(roof_list)
    
    abui_name = abui["name"]
    get_bui_props(abui, aresults_path, abui_name)

    fac_int = 0
    for face in all_faces:
        normal = calculate.face_normal(face)
        # calculate pts of each face
        fps = fetch.pyptlist_frm_occface(face)
        fps_df.append([val for sublist in fps for val in sublist])

        sensor_srfs, sensor_pts, sensor_dirs = \
            gml3dmodel.generate_sensor_surfaces(face, settings.SEN_PARMS['X_DIM'], settings.SEN_PARMS['Y_DIM'])
        fac_area = calculate.face_area(face)
        # generate dataframe with building, face and sensor ID
        
        sen_int = 0
        for sen_dir in sensor_dirs:
            orientation = math.copysign(math.acos(normal[1]), normal[0]) * 180 / math.pi
            tilt = math.acos(normal[2]) * 180 / math.pi

            sen_df.append((fac_int, sen_int, fac_area, fac_area / len(sensor_dirs), sensor_pts[sen_int][0], sensor_pts[sen_int][1],
                 sensor_pts[sen_int][2], normal[0], normal[1], normal[2], orientation, tilt))
            
            sen_int += 1
        fac_int += 1

    sen_df = pd.DataFrame(sen_df, columns=['fac_int', 'sen_int', 'fac_area','sen_area', 'sen_x', 'sen_y',
                                       'sen_z', 'sen_dir_x', 'sen_dir_y', 'sen_dir_z', 'orientation', 'tilt'])
    sen_df.to_csv(os.path.join(aresults_path, abui + '_' + 'sen_df' + '.csv'), index=None)
    fps_df = pd.DataFrame(fps_df, columns=['fp_0_x', 'fp_0_y', 'fp_0_z', 'fp_1_x', 'fp_1_y', 'fp_1_z', 'fp_2_x', 'fp_2_y', 'fp_2_z', ])
    fps_df.to_csv(os.path.join(aresults_path, abui + '_' + 'fps_df' + '.csv'), index=None, float_format="%.2f")


    print 'calculate sensors', abui, 'done'


def execute_daysim(abui, aresults_path, arad, aweatherfile_path, rad_params, ageometry_table):

    sen_df= pd.read_csv(os.path.join(aresults_path, abui + '_' + 'sen_df' + '.csv'))
    #sen_df = pd.read_csv(os.path.join(aresults_path, abui +'.csv'))

    sen = sen_df[['sen_x', 'sen_y', 'sen_z']].values.tolist()
    sen_dir = sen_df[['sen_dir_x', 'sen_dir_y', 'sen_dir_z']].values.tolist()
    arad.set_sensor_points(sensor_normals=sen_dir, sensor_positions=sen)
    create_sensor_input_file(arad, abui)

    # generate daysim result folders for all an_cores
    daysim_dir = os.path.join(aresults_path, abui)
    arad.initialise_daysim(daysim_dir)
    # transform weather file
    arad.execute_epw2wea(aweatherfile_path)
    arad.execute_radfiles2daysim()

    add_rad_mat(aresults_path, abui, ageometry_table)

    arad.write_radiance_parameters(rad_params['RAD_AB'], rad_params['RAD_AD'], rad_params['RAD_AS'],rad_params['RAD_AR'],
                                   rad_params['RAD_AA'], rad_params['RAD_LR'],rad_params['RAD_ST'],rad_params['RAD_SJ'],
                                   rad_params['RAD_LW'],rad_params['RAD_DJ'],rad_params['RAD_DS'],rad_params['RAD_DR'],
                                   rad_params['RAD_DP'])

    #os.rename(os.path.join(arad.data_folder_path, abui + ".pts"), os.path.join(daysim_dir, 'pts', "sensor_points.pts"))
    arad.sensor_file_path = os.path.join(arad.data_folder_path, abui+"_sensor_points.pts")
    arad.execute_gen_dc("w/m2")
    arad.execute_ds_illum()
    print 'execute daysim', abui, 'done'


def execute_sum(results_path, bui, max_z_dir,):
    # calculate sum of all sensor values output in W
    res = pd.read_csv(os.path.join(results_path, bui, 'res', bui+'.ill'), sep=' ', header=None).ix[:, 4:]
    res.columns = [col for col in range(res.shape[1])]
    sen_df = pd.read_csv(os.path.join(results_path, bui+'_sen_df.csv'))
    sen_area = sen_df['sen_area']
    sen_z_dir_bool = sen_df['sen_dir_z']
    sen_z_dir_bool = np.where(sen_z_dir_bool > max_z_dir, 0, 1)
    # calculate W from W/m2
    sum = res.multiply(sen_area, axis=1)
    # calculate only for facade total sum
    sum = sum.multiply(sen_z_dir_bool, axis=1).sum(axis=1)
    sum.columns = [bui]
    sum.to_csv(os.path.join(results_path, bui, 'res', bui+'.csv'), index=None)


def execute_frac_exposed(results_path, bui):

    res = pd.read_csv(os.path.join(results_path, bui, 'res', bui+'.ill'), sep=' ', header=None)
    sen_df = pd.read_csv(os.path.join(results_path, bui + '_' + 'sen_df' + '.csv'))
    bui_props = pd.read_csv(os.path.join(results_path, bui+'_props.csv'))
    exposed = res.ix[:, 4:].sum(axis=0)
    exposed.ix[exposed > 0.0] = 1.0
    sen_df['exposed'] = exposed.values.tolist()
    sen_df.to_csv(os.path.join(results_path, bui + '_' + 'sen_df' + '.csv'), index=None)
    bui_props['exposed'] = sum(exposed)/len(exposed)
    bui_props.to_csv(os.path.join(results_path, bui + '_props.csv'), index=None)


def calculate_windows(results_path, bui):

    # initialize lists
    window_area = []
    window_height = []
    window_angle = []
    window_orientation = []
    bui_name = []

    sen_df = pd.read_csv(os.path.join(results_path, bui + '_' + 'sen_df' + '.csv'))
    bui_props = pd.read_csv(os.path.join(results_path, bui + '_props.csv'))

    # building porperties
    architecture_path = locator.get_building_architecture()
    prop_architecture = Gdf.from_file(architecture_path).drop('geometry', axis=1).set_index('Name')


    for window_int in range(sen_df['fac_int'].iloc[-1]):

        window_df = sen_df[sen_df['fac_int']==window_int]

        # window building name
        bui_name.append(bui)

        # window height
        centroid_z = window_df['sen_z'].mean()
        window_height.append(centroid_z-bui_props['bui_min_z'].get_value(0))

        # window area
        win_wall = prop_architecture.ix[bui]['win_wall']
        win_op = prop_architecture.ix[bui]['win_op']
        exposed = window_df['exposed'].mean()
        face_area = window_df['fac_area'].mean()
        window_area.append(face_area * win_wall * win_op * exposed)

        # window angle
        dir_z = window_df['sen_dir_z'].mean()
        window_angle.append(math.acos(dir_z) * 180 / math.pi)

        # window orientation
        dir_x = window_df['sen_dir_x'].mean()
        dir_y = window_df['sen_dir_y'].mean()
        angle = math.copysign(math.acos(dir_y), dir_x) * 180 / math.pi
        if abs(angle) > 135:
            orientation = 0
        elif abs(angle) < 45:
            orientation = 180
        elif angle < 0:
            orientation = 270
        else:
            orientation = 90

        window_orientation.append(orientation)

    df_windows = pd.DataFrame({'name_building': bui_name,
                               'area_window': window_area,
                               'height_window_above_ground': window_height,
                               'orientation_window': window_orientation,
                               'angle_window': window_angle,
                               'height_window_in_zone': window_height})

    df_windows = df_windows[df_windows['area_window'] != 0.0]
    df_windows.to_csv(os.path.join(results_path, bui + '_window_props.csv'), index=None)


def calc_radiation(geometry_table_name, weatherfile_path, locator):
    # file paths
    input_path = locator.get_3D_geometry_folder()
    results_path = locator.get_solar_radiation_folder()

    # =============================== Preface =============================== #
    rad = py2radiance.Rad(os.path.join(results_path, 'base.rad'), results_path)

    # =============================== Import =============================== #
    bldg_prop_list = pd.read_csv(os.path.join(input_path, geometry_table_name +".csv"), index_col='name')
    # =============================== Simulation =============================== #
    citygml_reader = pycitygml.Reader()
    citygml_filepath = os.path.join(input_path, "new.gml")
    citygml_reader.load_filepath(citygml_filepath)
    bldg_dict_list = geometry2radiance(rad, bldg_prop_list, input_path, citygml_reader)
    
    rad.create_rad_input_file()

    building_names_df = gpdf.from_file(locator.get_building_occupancy())
    building_names = building_names_df.Name.values

    # calculate sensor points
    pool = multiprocessing.Pool()  # use all available cores, otherwise specify the number you want as an argument
    for bldg_dict in bldg_dict_list:
        pool.apply_async(calc_sensors, args=(results_path, bldg_dict, input_path))
    pool.close()
    pool.join()

    # execute daysim
    processes = []
    for bui in building_names:
        process = multiprocessing.Process(target=execute_daysim, args=(bui, results_path, rad, weatherfile_path, settings.RAD_PARMS, bldg_prop_list,))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()

    # calculate total irradiance of each stl file
    pool = multiprocessing.Pool()
    for bui in building_names:
        pool.apply_async(execute_sum, args=(results_path, bui, settings.SEN_PARMS['MAX_Z_DIR'],))
    pool.close()
    pool.join()

    # create radiaiton file
    radiation = pd.DataFrame(columns=building_names)
    print radiation
    for bui in building_names:
        res = pd.read_csv(os.path.join(results_path, bui, 'res', bui + '.csv'), header=None).ix[:, 0].values.tolist()
        radiation[bui] = res
    col_list = radiation.columns.tolist()
    radiation['index']=['T'+str(i) for i in range(8760)]
    radiation.set_index('index', inplace=True)
    radiation = radiation.T
    radiation['Name'] = col_list
    radiation.to_csv(os.path.join(results_path, 'radiation.csv'), index=None)

    # update sensor and building props with exposed value
    for bui in building_names:
        execute_frac_exposed(results_path, bui)

    # calculate windows
    for bui in building_names:
        calculate_windows(results_path, bui)

    # create properties file
    props = pd.DataFrame(columns=['roof_area', 'facade_area', 'roof_angle', 'bui_height', 'bui_min_z', 'exposed'])
    for bui in building_names:
        bui_props = pd.read_csv(os.path.join(results_path, bui + '_props.csv'))
        props.loc[bui] = bui_props.ix[0, :]
    props['Name'] = props.index.values
    props.to_csv(os.path.join(results_path, 'properties_surfaces.csv'), index=None)


if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weatherfile_path = locator.get_default_weather()
    geometry_table_name = 'background_geometries'
    sensor_geometries_name = 'sensor_geometries'

    calc_radiation(geometry_table_name, weatherfile_path, locator)