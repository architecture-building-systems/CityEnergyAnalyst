import os
import pandas as pd
import pyliburo.py3dmodel.calculate as calculate
import pyliburo.py2radiance as py2radiance
from cea.resources.radiation_daysim import settings

import pyliburo.gml3dmodel as gml3dmodel
__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_sensor_input_file(rad, chunk_n):
    sensor_file_path = os.path.join(rad.data_folder_path, "points_"+str(chunk_n)+".pts")
    sensor_file = open(sensor_file_path, "w")
    sensor_pts_data = py2radiance.write_rad.sensor_file(rad.sensor_positions, rad.sensor_normals)
    sensor_file.write(sensor_pts_data)
    sensor_file.close()
    rad.sensor_file_path = sensor_file_path


def create_srf_dict(occface_list, srf_type, bldg_name):
    srf_dict_list = []
    for face in occface_list:
        sensor_srfs, sensor_pts, sensor_dirs = \
            gml3dmodel.generate_sensor_surfaces(face, settings.SEN_PARMS['X_DIM'], settings.SEN_PARMS['Y_DIM'])

        for scnt, sensor_srf in enumerate(sensor_srfs):
            srf_dict = {}
            srf_dict["bldg_name"] = bldg_name
            srf_dict["occface"] = sensor_srf
            srf_dict["srf_type"] = srf_type
            srf_dict["sensor_pt"] = sensor_pts[scnt]
            srf_dict["sensor_dir"] = sensor_dirs[scnt]
            srf_dict_list.append(srf_dict)
    return srf_dict_list


def calc_sensors(bldg_dict):
    sensor_srf_dict_list = []
    wall_list = bldg_dict["walls"]
    window_list = bldg_dict["windows"]
    roof_list = bldg_dict["roofs"]
    bldg_name = bldg_dict["name"]

    # grid up all the surfaces and return a srf dict that has all the information on the surface
    wall_sensor_srf_dict_list = create_srf_dict(wall_list, "wall", bldg_name)
    win_sensor_srf_dict_list = create_srf_dict(window_list, "window", bldg_name)
    rf_sensor_srf_dict_list = create_srf_dict(roof_list, "roof", bldg_name)
    sensor_srf_dict_list.extend(wall_sensor_srf_dict_list)
    sensor_srf_dict_list.extend(win_sensor_srf_dict_list)
    sensor_srf_dict_list.extend(rf_sensor_srf_dict_list)
    return sensor_srf_dict_list


def isolation_daysim(chunk_n, rad, geometry_3D_building, aresults_path, rad_params, aweatherfile_path):

    # calculate sensors
    sensor_pt_list = []
    sensor_dir_list = []

    # folder for data work
    daysim_dir = os.path.join(aresults_path, "temp" + str(chunk_n))
    rad.initialise_daysim(daysim_dir)

    # calculate sensors
    if chunk_n == None: # do simple list when considering single buildings (single processing)
        all_sensor_srf_dict_2dlist = calc_sensors(geometry_3D_building)
        for srf_dict in all_sensor_srf_dict_2dlist:
            sensor_pt = srf_dict["sensor_pt"]
            sensor_pt_list.append(sensor_pt)
            sensor_dir = srf_dict["sensor_dir"]
            sensor_dir_list.append(sensor_dir)
    else: # create bigger list when considering chunks of buildings (multi-processing)
        all_sensor_srf_dict_2dlist = []
        for bldg_dict in geometry_3D_building:
            sensor_srf_dict_list = calc_sensors(bldg_dict)
            all_sensor_srf_dict_2dlist.append(sensor_srf_dict_list)
            for srf_dict in sensor_srf_dict_list:
                sensor_pt = srf_dict["sensor_pt"]
                sensor_pt_list.append(sensor_pt)
                sensor_dir = srf_dict["sensor_dir"]
                sensor_dir_list.append(sensor_dir)

    rad.set_sensor_points(sensor_pt_list, sensor_dir_list)
    create_sensor_input_file(rad, chunk_n)

    rad.execute_epw2wea(aweatherfile_path)
    rad.execute_radfiles2daysim()
    rad.write_radiance_parameters(rad_params['RAD_AB'], rad_params['RAD_AD'], rad_params['RAD_AS'],
                                  rad_params['RAD_AR'], rad_params['RAD_AA'], rad_params['RAD_LR'],
                                  rad_params['RAD_ST'], rad_params['RAD_SJ'], rad_params['RAD_LW'],
                                  rad_params['RAD_DJ'], rad_params['RAD_DS'], rad_params['RAD_DR'],
                                  rad_params['RAD_DP'])
    rad.execute_gen_dc("w/m2")
    rad.execute_ds_illum()
    solar_res = rad.eval_ill_per_sensor()

    #write the results
    if chunk_n == None:
        results_writer_single_processing(solar_res, all_sensor_srf_dict_2dlist, aresults_path)
    else:
        results_writer_multi_processing(solar_res, all_sensor_srf_dict_2dlist, aresults_path)

def results_writer_single_processing(solar_res, all_sensor_srf_dict_2dlist, aresults_path):

    srf_properties = []
    srf_solar_results = []
    nsrfs = len(all_sensor_srf_dict_2dlist)
    res_columns = []
    for _ in range(nsrfs):
        res_columns.append("building_surface_name")
    for scnt, srf_dict in enumerate(all_sensor_srf_dict_2dlist):
        occface = srf_dict["occface"]
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
        srf_properties.append(
            (bldg_name, srf_name, mid_ptx, mid_pty, mid_ptz, nrmlx, nrmly, nrmlz, face_area, srf_type))

        # create csv for 8760 hours of results
        srf_res = solar_res[scnt]
        asrf_solar_result = [srf_name]
        for res in srf_res:
            asrf_solar_result.append(res)

        srf_solar_results.append(asrf_solar_result)
        scnt +=1

    srf_properties = pd.DataFrame(srf_properties, columns=['BUILDING', 'SURFACE', 'Xcoor', 'Ycoor', 'Zcoor',
                                                           'Xdir', 'Ydir', 'Zdir', 'AREA_m2',
                                                           'TYPE'])

    srf_properties.to_csv(os.path.join(aresults_path, bldg_name + '_geometry.csv'), index=None)
    zipped_solar_res = zip(*srf_solar_results)
    srf_solar_results = pd.DataFrame(zipped_solar_res[1:], columns=zipped_solar_res[0])
    srf_solar_results.to_csv(os.path.join(aresults_path, bldg_name + '_insolation_Whm2.csv'), index=None)

def results_writer_multi_processing(solar_res, all_sensor_srf_dict_2dlist, aresults_path):

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
            srf_properties.append(
                (bldg_name, srf_name, mid_ptx, mid_pty, mid_ptz, nrmlx, nrmly, nrmlz, face_area, srf_type))

            # create csv for 8760 hours of results
            srf_res = solar_res[scnt]
            asrf_solar_result = [srf_name]
            for res in srf_res:
                asrf_solar_result.append(res)

            srf_solar_results.append(asrf_solar_result)
            scnt +=1

        srf_properties = pd.DataFrame(srf_properties, columns=['BUILDING', 'SURFACE', 'Xcoor', 'Ycoor', 'Zcoor',
                                                               'Xdir', 'Ydir', 'Zdir', 'AREA_m2',
                                                               'TYPE'])

        srf_properties.to_csv(os.path.join(aresults_path, bldg_name + '_geometry.csv'), index=None)
        zipped_solar_res = zip(*srf_solar_results)
        srf_solar_results = pd.DataFrame(zipped_solar_res[1:], columns=zipped_solar_res[0])
        srf_solar_results.to_csv(os.path.join(aresults_path, bldg_name + '_insolation_Whm2.csv'), index=None)