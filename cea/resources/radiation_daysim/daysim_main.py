import json
import os

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

from cea.constants import HOURS_IN_YEAR
from cea.resources.radiation_daysim.geometry_generator import BuildingGeometry
from cea import suppress_3rd_party_debug_loggers

suppress_3rd_party_debug_loggers()


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


def calc_sensors_building(building_geometry, grid_size):
    sensor_dir_list = []
    sensor_cord_list = []
    sensor_type_list = []
    sensor_area_list = []
    sensor_orientation_list = []
    sensor_intersection_list = []
    surfaces_types = ['walls', 'windows', 'roofs']
    sensor_vertical_grid_dim = grid_size["walls_grid"]
    sensor_horizontal_grid_dim = grid_size["roof_grid"]
    for srf_type in surfaces_types:
        occface_list = getattr(building_geometry, srf_type)
        if srf_type == 'roofs':
            orientation_list = ['top'] * len(occface_list)
            normals_list = [(0.0, 0.0, 1.0)] * len(occface_list)
            interesection_list = [0] * len(occface_list)
        elif srf_type == 'windows':
            orientation_list = getattr(building_geometry, "orientation_{srf_type}".format(srf_type=srf_type))
            normals_list = getattr(building_geometry, "normals_{srf_type}".format(srf_type=srf_type))
            interesection_list = [0] * len(occface_list)
        else:
            orientation_list = getattr(building_geometry, "orientation_{srf_type}".format(srf_type=srf_type))
            normals_list = getattr(building_geometry, "normals_{srf_type}".format(srf_type=srf_type))
            interesection_list = getattr(building_geometry, "intersect_{srf_type}".format(srf_type=srf_type))
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


def calc_sensors_zone(building_names, locator, grid_size, geometry_pickle_dir):
    sensors_coords_zone = []
    sensors_dir_zone = []
    sensors_total_number_list = []
    names_zone = []
    sensors_code_zone = []
    sensor_intersection_zone = []
    for building_name in building_names:
        building_geometry = BuildingGeometry.load(os.path.join(geometry_pickle_dir, 'zone', building_name))
        # get sensors in the building
        sensors_dir_building, \
        sensors_coords_building, \
        sensors_type_building, \
        sensors_area_building, \
        sensor_orientation_building, \
        sensor_intersection_building = calc_sensors_building(building_geometry, grid_size)

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


def isolation_daysim(chunk_n, cea_daysim, building_names, locator, radiance_parameters, write_sensor_data, grid_size,
                     max_global, weatherfile, geometry_pickle_dir):
    # initialize daysim project
    daysim_project = cea_daysim.initialize_daysim_project('chunk_{n}'.format(n=chunk_n))
    print('Creating daysim project in: {daysim_dir}'.format(daysim_dir=daysim_project.project_path))

    # calculate sensors
    print("Calculating and sending sensor points")
    sensors_coords_zone, \
    sensors_dir_zone, \
    sensors_number_zone, \
    names_zone, \
    sensors_code_zone, \
    sensor_intersection_zone = calc_sensors_zone(building_names, locator, grid_size, geometry_pickle_dir)

    num_sensors = sum(sensors_number_zone)
    daysim_project.create_sensor_input_file(sensors_coords_zone, sensors_dir_zone, num_sensors, "w/m2")

    print("Starting Daysim simulation for buildings: {buildings}".format(buildings=names_zone))
    print("Total number of sensors:  {num_sensors}".format(num_sensors=num_sensors))

    print('Writing radiance parameters')
    daysim_project.write_radiance_parameters(radiance_parameters["rad_ab"], radiance_parameters["rad_ad"],
                                             radiance_parameters["rad_as"], radiance_parameters["rad_ar"],
                                             radiance_parameters["rad_aa"], radiance_parameters["rad_lr"],
                                             radiance_parameters["rad_st"], radiance_parameters["rad_sj"],
                                             radiance_parameters["rad_lw"], radiance_parameters["rad_dj"],
                                             radiance_parameters["rad_ds"], radiance_parameters["rad_dr"],
                                             radiance_parameters["rad_dp"])

    print('Executing hourly solar isolation calculation')
    daysim_project.execute_gen_dc()
    daysim_project.execute_ds_illum()

    print('Reading results...')
    solar_res = daysim_project.eval_ill()

    # check inconsistencies and replace by max value of weather file
    print('Fixing inconsistencies, if any')
    solar_res = np.clip(solar_res, a_min=0.0, a_max=max_global)

    # Check if leap year and remove extra day
    if solar_res.shape[1] == HOURS_IN_YEAR + 24:
        print('Removing leap day')
        leap_day_hours = range(1416, 1440)
        solar_res = np.delete(solar_res, leap_day_hours, axis=1)

    print("Writing results to disk")
    index = 0
    for building_name, \
        sensors_number_building, \
        sensor_code_building, \
        sensor_intersection_building in zip(names_zone,
                                            sensors_number_zone,
                                            sensors_code_zone,
                                            sensor_intersection_zone):
        # select sensors data
        selection_of_results = solar_res[index:index + sensors_number_building]
        selection_of_results[np.array(sensor_intersection_building) == 1] = 0
        items_sensor_name_and_result = dict(zip(sensor_code_building, selection_of_results.tolist()))
        index = index + sensors_number_building

        # create summary and save to disk
        write_aggregated_results(building_name, items_sensor_name_and_result, locator, weatherfile)

        if write_sensor_data:
            write_sensor_results(building_name, items_sensor_name_and_result, locator)

    # erase daysim folder to avoid conflicts after every iteration
    print('Removing results folder')
    daysim_project.cleanup_project()


def write_sensor_results(building_name, items_sensor_name_and_result, locator):
    with open(locator.get_radiation_building_sensors(building_name), 'w') as outfile:
        json.dump(items_sensor_name_and_result, outfile)


def write_aggregated_results(building_name, items_sensor_name_and_result, locator, weatherfile):
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
        array_field = np.array([select_sensors.loc[surface, 'AREA_m2'] *
                                np.array(items_sensor_name_and_result[surface])
                                for surface in select_sensors.index]).sum(axis=0)
        dict_not_aggregated[field] = array_field / 1000  # in kWh
        dict_not_aggregated[field_area] = area_m2

    data_aggregated_kW = (pd.DataFrame(dict_not_aggregated)).round(2)
    data_aggregated_kW["Date"] = weatherfile["date"]
    data_aggregated_kW.set_index('Date', inplace=True)
    data_aggregated_kW.to_csv(locator.get_radiation_building(building_name))
