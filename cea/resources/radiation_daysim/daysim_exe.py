"""
Installation:

Install Daysim (Daysim/bin and Daysim/lib as environment varaibales)

Libaries
- create environment with (conda create -n "libary name" python=2.7 numpy=1.9.2)
- conda install lxml
- pip install pyshp
- conda install -c https://conda.anaconda.org/dlr-sc pythonocc-core=1.6.5
- copy paste occutils (https://github.com/tpaviot/pythonocc-utils/tree/master/OCCUtils) into site-packages
- copy paste pyliburo (https://github.com/chenkianwee/pyliburo) into site-packages
- conda install numpy
- conda install scipy
- easy_install pycollada
- pip install networkx
"""

import os
import numpy as np
import pandas as pd
import math
import multiprocessing

from OCC import BRepGProp, GProp, BRep, TopoDS
from OCC.StlAPI import StlAPI_Reader
from OCC.TopAbs import TopAbs_REVERSED
from OCCUtils import face, Topology

from cea.resources.radiation_daysim.pyliburo import py3dmodel
from cea.resources.radiation_daysim.pyliburo import gml3dmodel
from cea.resources.radiation_daysim.interface2py3d import pyptlist_frm_occface
from cea.resources.radiation_daysim.pyliburo import py2radiance

import cea.globalvar
import cea.inputlocator
from geopandas import GeoDataFrame as Gdf

__author__ = "Paul Neitzel"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel"]
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


def make_unique(original_list):
    unique_list = []
    [unique_list.append(obj) for obj in original_list if obj not in unique_list]
    return unique_list


def points_from_face(face):
    point_list = []
    pnt_coord = []
    wire_list = Topology.Topo(face).wires()
    for wire in wire_list:
        edges_list = Topology.Topo(wire).edges()
        for edge in edges_list:
            vertice_list = Topology.Topo(edge).vertices()
            for vertex in vertice_list:
                pnt_coord.append(
                    [BRep.BRep_Tool().Pnt(vertex).X(),
                     BRep.BRep_Tool().Pnt(vertex).Y(), BRep.BRep_Tool().Pnt(vertex).Z()])
    pnt_coord = make_unique(pnt_coord)
    for point in pnt_coord:
        point_list.append(point)
    return point_list


def face_normal(occface):
    fc = face.Face(occface)
    centre_uv, centre_pt = fc.mid_point()
    normal_dir = fc.DiffGeom.normal(centre_uv[0], centre_uv[1])
    if occface.Orientation() == TopAbs_REVERSED:
        normal_dir = normal_dir.Reversed()
    normal = (normal_dir.X(), normal_dir.Y(), normal_dir.Z())
    return normal


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


def geometry2radiance(arad, ageometry_table, ainput_path):

    # add all geometries which are in "ageometry_table" to radiance
    bcnt = 0
    for geo in ageometry_table.index.values:
        filepath = os.path.join(ainput_path, geo + ".stl")
        geo_solid = TopoDS.TopoDS_Solid()
        StlAPI_Reader().Read(geo_solid, str(filepath))
        face_list = py3dmodel.fetch.faces_frm_solid(geo_solid)
        bf_cnt = 0
        for face in face_list:
            bface_pts = pyptlist_frm_occface(face)
            srfname = "building_srf" + str(bcnt) + str(bf_cnt)

            srfmat = ageometry_table['mat_name'][geo]
            py2radiance.RadSurface(srfname, bface_pts, srfmat, arad)
            bf_cnt += 1
        bcnt += 1


def get_bui_props(face_list, aresults_path, abui):

    bui_props = pd.DataFrame(columns=['roof_area', 'facade_area', 'roof_angle', 'bui_height', 'bui_min_z'])

    zs = []
    facade_area = []
    roof_area = []
    roof_angle = []

    for bui_face in face_list:
        fc = face.Face(bui_face)
        centre_uv, centre_pt = fc.mid_point()
        fac_normal = fc.DiffGeom.normal(centre_uv[0], centre_uv[1])
        fac_area = py3dmodel.calculate.face_area(bui_face)

        # builing Z
        zs.append(centre_pt.Z())

        # building roof area
        if fac_normal.Z() > 0.05:
            roof_area.append(fac_area)
            roof_angle.append(math.acos(fac_normal.Z()))

        # building facade area
        elif fac_normal.Z() > -0.85:
            facade_area.append(fac_area)

    bui_roof_area = sum(roof_area)
    bui_roof_angle = sum(roof_angle)/len(roof_angle)
    bui_facade_area= sum(facade_area)
    bui_max_z =max(zs)
    bui_min_z = min(zs)

    bui_props.loc[abui] = [bui_roof_area, bui_facade_area, bui_roof_angle, bui_max_z-bui_min_z, bui_min_z]
    bui_props.to_csv(os.path.join(aresults_path, abui+'_props.csv'), index=None)


def calc_sensors(aresults_path, abui, ainput_path, axdim, aydim, min_z_dir):

    bui_vol = []
    sen_df = []
    fps_df = []
    # import stl file
    filepath = os.path.join(ainput_path, abui + ".stl")
    geo_solid = TopoDS.TopoDS_Solid()
    StlAPI_Reader().Read(geo_solid, str(filepath))

    # calculate geometries properties
    props = GProp.GProp_GProps()
    BRepGProp.brepgprop_VolumeProperties(geo_solid, props)

    # reverse geometry if volume is negative
    if props.Mass() < 0:
        bui_vol.append(-props.Mass())
        geo_solid.Reverse()
    else:
        bui_vol.append(props.Mass())

    # get all faces from geometry
    face_list = py3dmodel.fetch.faces_frm_solid(geo_solid)

    # get minimum z of building
    get_bui_props(face_list, aresults_path, abui)

    fac_int = 0
    for face in face_list:
        normal = face_normal(face)

        if min_z_dir < normal[2]:

            # calculate pts of each face
            fps = points_from_face(face)
            fps_df.append([val for sublist in fps for val in sublist])

            sensor_srfs, sensor_pts, sensor_dirs = \
                gml3dmodel.generate_sensor_surfaces(face, axdim, aydim)
            fac_area = py3dmodel.calculate.face_area(face)
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

    arad.write_radiance_parameters(rad_params['rad_ab'], rad_params['rad_ad'], rad_params['rad_as'],rad_params['rad_ar'],
                                   rad_params['rad_aa'], rad_params['rad_lr'],rad_params['rad_st'],rad_params['rad_sj'],
                                   rad_params['rad_lw'],rad_params['rad_dj'],rad_params['rad_ds'],rad_params['rad_dr'],
                                   rad_params['rad_dp'])


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


def calc_radiation(geometry_table_name, sensor_geometries_name, locator):

    # file paths
    input_path = locator.get_3D_geometry_folder()
    results_path = locator.get_solar_radiation_folder()
    weatherfile_path = locator.get_default_weather()

    # Sensor parameters
    xdim = 5
    ydim = 5
    min_z_dir = -0.85
    max_z_dir = 0.05

    # Daysim simulation parameters
    rad_params = {
        'rad_n': 2,
        'rad_af': 'file',
        'rad_ab': 4,
        'rad_ad': 512,
        'rad_as': 256,
        'rad_ar': 128,
        'rad_aa': 0.15,
        'rad_lr': 8,
        'rad_st': 0.15,
        'rad_sj': 0.7,
        'rad_lw': 0.002,
        'rad_dj': 0.7,
        'rad_ds': 0.15,
        'rad_dr': 3,
        'rad_dp': 512,
        }

    # =============================== Preface =============================== #
    rad = py2radiance.Rad(os.path.join(results_path, 'base.rad'), results_path)

    # =============================== Import =============================== #

    geometry_table = pd.read_csv(os.path.join(input_path, geometry_table_name+".csv"), index_col='name')

    # =============================== Simulation =============================== #
    geometry2radiance(rad, geometry_table, input_path)
    rad.create_rad_input_file()

    sensor_geometries = pd.read_csv(os.path.join(input_path,sensor_geometries_name + '.csv'), index_col='name')
    sensor_geo_list = sensor_geometries.index.values

    # calculate sensor points
    pool = multiprocessing.Pool()  # use all available cores, otherwise specify the number you want as an argument
    for bui in sensor_geometries.index.values:
        pool.apply_async(calc_sensors, args=(results_path, bui, input_path, xdim, ydim, min_z_dir,))
    pool.close()
    pool.join()

    # execute daysim
    processes = []
    for bui in sensor_geo_list:
        process = multiprocessing.Process(target=execute_daysim, args=(bui, results_path, rad, weatherfile_path, rad_params, geometry_table,))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()

    # calculate total irradiance of each stl file
    pool = multiprocessing.Pool()
    for bui in sensor_geo_list:
        pool.apply_async(execute_sum, args=(results_path, bui, max_z_dir,))
    pool.close()
    pool.join()

    # create radiaiton file
    radiation = pd.DataFrame(columns=sensor_geometries.index.values)
    for bui in sensor_geo_list:
        res = pd.read_csv(os.path.join(results_path, bui, 'res', bui + '.csv'), header=None).ix[:, 0].values.tolist()
        radiation[bui] = res
    col_list = radiation.columns.tolist()
    radiation['index']=['T'+str(i) for i in range(8760)]
    radiation.set_index('index', inplace=True)
    radiation = radiation.T
    radiation['Name'] = col_list
    radiation.to_csv(os.path.join(results_path, 'radiation.csv'), index=None)

    # update sensor and building props with exposed value
    for bui in sensor_geo_list:
        execute_frac_exposed(results_path, bui)

    # calculate windows
    for bui in sensor_geo_list:
        calculate_windows(results_path, bui)

    # create properties file
    props = pd.DataFrame(columns=['roof_area', 'facade_area', 'roof_angle', 'bui_height', 'bui_min_z', 'exposed'])
    for bui in sensor_geo_list:
        bui_props = pd.read_csv(os.path.join(results_path, bui + '_props.csv'))
        props.loc[bui] = bui_props.ix[0, :]
    props['Name'] = props.index.values
    props.to_csv(os.path.join(results_path, 'properties_surfaces.csv'), index=None)


if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    geometry_table_name = 'background_geometries'
    sensor_geometries_name = 'sensor_geometries'

    calc_radiation(geometry_table_name, sensor_geometries_name, locator)
