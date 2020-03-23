from __future__ import division

import json
import os
import shutil

import numpy as np
import pandas as pd
import py4design.py2radiance as py2radiance
import py4design.py3dmodel.calculate as calculate
from py4design import py3dmodel

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_sensor_input_file(rad, chunk_n):
    sensor_file_path = os.path.join(rad.data_folder_path, "points_" + str(chunk_n) + ".pts")
    sensor_file = open(sensor_file_path, "w")
    sensor_pts_data = py2radiance.write_rad.sensor_file(rad.sensor_positions, rad.sensor_normals)
    sensor_file.write(sensor_pts_data)
    sensor_file.close()
    rad.sensor_file_path = sensor_file_path


def generate_sensor_surfaces(occface, wall_dim, roof_dim, srf_type, orientation, normal, intersection):
    mid_pt = py3dmodel.calculate.face_midpt(occface)
    location_pt = py3dmodel.modify.move_pt(mid_pt, normal, 0.01)
    moved_oface = py3dmodel.fetch.topo2topotype(py3dmodel.modify.move(mid_pt, location_pt, occface))
    if srf_type == 'roofs':
        xdim = ydim = roof_dim
    else:
        xdim = ydim = wall_dim
    # put it into occ and subdivide surfaces
    sensor_surfaces = py3dmodel.construct.grid_face(moved_oface, xdim, ydim)

    # calculate list of properties per surface
    sensor_intersection = [intersection for x in sensor_surfaces]
    sensor_dir = [normal for x in sensor_surfaces]
    sensor_cord = [py3dmodel.calculate.face_midpt(x) for x in sensor_surfaces]
    sensor_type = [srf_type for x in sensor_surfaces]
    sensor_orientation = [orientation for x in sensor_surfaces]
    sensor_area = [calculate.face_area(x) * (1.0 - scalar) for x, scalar in zip(sensor_surfaces, sensor_intersection)]

    return sensor_dir, sensor_cord, sensor_type, sensor_area, sensor_orientation, sensor_intersection


def calc_sensors_building(building_geometry_dict, settings, ):
    sensor_dir_list = []
    sensor_cord_list = []
    sensor_type_list = []
    sensor_area_list = []
    sensor_orientation_list = []
    sensor_intersection_list = []
    surfaces_types = ['walls', 'windows', 'roofs']
    sensor_vertical_grid_dim = settings.walls_grid
    sensor_horizontal_grid_dim = settings.roof_grid
    for srf_type in surfaces_types:
        occface_list = building_geometry_dict[srf_type]
        if srf_type == 'roofs':
            orientation_list = ['top'] * len(occface_list)
            normals_list = [(0.0, 0.0, 1.0)] * len(occface_list)
            interesection_list = [0] * len(occface_list)
        elif srf_type == 'windows':
            orientation_list = building_geometry_dict["orientation_" + srf_type]
            normals_list = building_geometry_dict["normals_" + srf_type]
            interesection_list = [0] * len(occface_list)
        else:
            orientation_list = building_geometry_dict["orientation_" + srf_type]
            normals_list = building_geometry_dict["normals_" + srf_type]
            interesection_list = building_geometry_dict["intersect_" + srf_type]
        for orientation, normal, face, intersection in zip(orientation_list, normals_list, occface_list,
                                                           interesection_list):
            sensor_dir, \
            sensor_cord, \
            sensor_type, \
            sensor_area, \
            sensor_orientation, \
            sensor_intersection = generate_sensor_surfaces(face,
                                                           sensor_vertical_grid_dim,
                                                           sensor_horizontal_grid_dim,
                                                           srf_type,
                                                           orientation,
                                                           normal,
                                                           intersection)
            sensor_intersection_list.extend(sensor_intersection)
            sensor_dir_list.extend(sensor_dir)
            sensor_cord_list.extend(sensor_cord)
            sensor_type_list.extend(sensor_type)
            sensor_area_list.extend(sensor_area)
            sensor_orientation_list.extend(sensor_orientation)

    return sensor_dir_list, sensor_cord_list, sensor_type_list, sensor_area_list, sensor_orientation_list, sensor_intersection_list


def calc_sensors_zone(geometry_3D_zone, locator, settings):
    sensors_coords_zone = []
    sensors_dir_zone = []
    sensors_total_number_list = []
    names_zone = []
    sensors_code_zone = []
    sensor_intersection_zone = []
    for building_geometry in geometry_3D_zone:
        # building name
        building_name = building_geometry["name"]
        # get sensors in the building
        sensors_dir_building, \
        sensors_coords_building, \
        sensors_type_building, \
        sensors_area_building, \
        sensor_orientation_building, \
        sensor_intersection_building = calc_sensors_building(building_geometry,
                                                             settings,
                                                             )

        # get the total number of sensors and store in lst
        sensors_number = len(sensors_coords_building)
        sensors_total_number_list.append(sensors_number)

        sensors_code = ['srf' + str(x) for x in range(sensors_number)]
        sensors_code_zone.append(sensors_code)

        # get the total list of coordinates and directions to send to daysim
        sensors_coords_zone.extend(sensors_coords_building)
        sensors_dir_zone.extend(sensors_dir_building)

        # get total list of intersections
        sensor_intersection_zone.append(sensor_intersection_building)

        # get the name of all buildings
        names_zone.append(building_name)

        # save sensors geometry result to disk
        pd.DataFrame({'BUILDING': building_name,
                      'SURFACE': sensors_code,
                      'orientation': sensor_orientation_building,
                      'intersection': sensor_intersection_building,
                      'Xcoor': [x[0] for x in sensors_coords_building],
                      'Ycoor': [x[1] for x in sensors_coords_building],
                      'Zcoor': [x[2] for x in sensors_coords_building],
                      'Xdir': [x[0] for x in sensors_dir_building],
                      'Ydir': [x[1] for x in sensors_dir_building],
                      'Zdir': [x[2] for x in sensors_dir_building],
                      'AREA_m2': sensors_area_building,
                      'TYPE': sensors_type_building}).to_csv(locator.get_radiation_metadata(building_name), index=None)

    return sensors_coords_zone, sensors_dir_zone, sensors_total_number_list, names_zone, sensors_code_zone, sensor_intersection_zone


def isolation_daysim(chunk_n, rad, geometry_3D_zone, locator, settings, max_global, weatherfile):
    # folder for data work
    daysim_dir = locator.get_temporary_file("temp" + str(chunk_n))
    print('isolation_daysim: daysim_dir={daysim_dir}'.format(daysim_dir=daysim_dir))

    # daysim_bin_directory might contain two paths (e.g. "C:\Daysim\bin;C:\Daysim\lib") - in which case, only
    # use the "bin" folder
    bin_directory = [d for d in settings.daysim_bin_directory.split(";") if not d.endswith("lib")][0]

    rad.initialise_daysim(daysim_dir, os.path.join(bin_directory, ''))
    print("\tisolation_daysim: rad.hea_file: {}".format(rad.hea_file))
    print("\tisolation_daysim: rad.hea_filename: {}".format(rad.hea_filename))
    print("\tisolation_daysim: rad.daysimdir_ies: {}".format(rad.daysimdir_ies))
    print("\tisolation_daysim: rad.daysimdir_pts: {}".format(rad.daysimdir_pts))
    print("\tisolation_daysim: rad.daysimdir_rad: {}".format(rad.daysimdir_rad))
    print("\tisolation_daysim: rad.daysimdir_res: {}".format(rad.daysimdir_res))
    print("\tisolation_daysim: rad.daysimdir_tmp: {}".format(rad.daysimdir_tmp))
    print("\tisolation_daysim: rad.daysimdir_wea: {}".format(rad.daysimdir_wea))

    # calculate sensors
    print("Calculating and sending sensor points")

    sensors_coords_zone, \
    sensors_dir_zone, \
    sensors_number_zone, \
    names_zone, \
    sensors_code_zone, \
    sensor_intersection_zone = calc_sensors_zone(geometry_3D_zone, locator, settings)
    rad.set_sensor_points(sensors_coords_zone, sensors_dir_zone)
    create_sensor_input_file(rad, chunk_n)
    print("\tisolation_daysim: rad.sensor_file_path: {}".format(rad.sensor_file_path))

    num_sensors = sum(sensors_number_zone)
    print("Starting Daysim simulation starts for buildings {buildings}".format(buildings=names_zone))
    print("Total number of sensors:  {num_sensors}".format(num_sensors=num_sensors))
    if num_sensors > 50000:
        raise ValueError('You are sending more than 50000 sensors at the same time, this '
                         'will eventually crash a daysim instance. To solve it, please reconfigure the radiation tool. '
                         'Just reduce the number of buildings per chunk and try again')

    # add_elevation_weather_file(weather_path)
    print('Transforming weather files to daysim format')
    rad.execute_epw2wea(locator.get_weather_file(), ground_reflectance=settings.albedo)
    print('Transforming radiance files to daysim format')
    rad.execute_radfiles2daysim()
    print('Writing radiance parameters')
    rad.write_radiance_parameters(settings.rad_ab, settings.rad_ad, settings.rad_as, settings.rad_ar, settings.rad_aa,
                                  settings.rad_lr, settings.rad_st, settings.rad_sj, settings.rad_lw, settings.rad_dj,
                                  settings.rad_ds, settings.rad_dr, settings.rad_dp)
    print('Executing hourly solar isolation calculation')
    rad.execute_gen_dc("w/m2")
    rad.execute_ds_illum()
    solar_res = rad.eval_ill_per_sensor()

    # check inconsistencies and replace by max value of weather file
    print('Fixing inconsistencies, if any')
    solar_res = np.clip(solar_res, a_min=0.0, a_max=max_global)

    print("Writing results to disk")
    index = 0
    for building_name, \
        sensors_number_building, \
        sensor_code_building, \
        sensor_intersection_building in zip(names_zone,
                                            sensors_number_zone,
                                            sensors_code_zone,
                                            sensor_intersection_zone):
        # select sensors and plot to disk
        selection_of_results = solar_res[index:index + sensors_number_building]
        result = [(array * (1.0 - scalar)).tolist() for array, scalar in
                  zip(selection_of_results, sensor_intersection_building)]
        items_sensor_name_and_result = dict(zip(sensor_code_building, result))
        with open(locator.get_radiation_building_sensors(building_name), 'w') as outfile:
            json.dump(items_sensor_name_and_result, outfile)
        index = index + sensors_number_building

        # create summary and save to disk
        geometry = pd.read_csv(locator.get_radiation_metadata(building_name))
        geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation'] + '_kW'
        solar_analysis_fields = ['windows_east_kW',
                                 'windows_west_kW',
                                 'windows_south_kW',
                                 'windows_north_kW',
                                 'walls_east_kW',
                                 'walls_west_kW',
                                 'walls_south_kW',
                                 'walls_north_kW',
                                 'roofs_top_kW']
        solar_analysis_fields_area = ['windows_east_m2',
                                      'windows_west_m2',
                                      'windows_south_m2',
                                      'windows_north_m2',
                                      'walls_east_m2',
                                      'walls_west_m2',
                                      'walls_south_m2',
                                      'walls_north_m2',
                                      'roofs_top_m2']
        dict_not_aggregated = {}
        for field, field_area in zip(solar_analysis_fields, solar_analysis_fields_area):
            select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
            area_m2 = select_sensors['AREA_m2'].sum()
            array_field = np.array([select_sensors.ix[surface, 'AREA_m2'] *
                                    np.array(items_sensor_name_and_result[surface])
                                    for surface in select_sensors.index]).sum(axis=0)
            dict_not_aggregated[field] = array_field / 1000  # in kWh
            dict_not_aggregated[field_area] = area_m2

        data_aggregated_kW = (pd.DataFrame(dict_not_aggregated)).round(2)
        data_aggregated_kW["Date"] = weatherfile["date"]
        data_aggregated_kW.set_index('Date', inplace=True)
        data_aggregated_kW.to_csv(locator.get_radiation_building(building_name))

    # erase daysim folder to avoid conflicts after every iteration
    print('Removing results folder')
    shutil.rmtree(daysim_dir)
