from __future__ import annotations
import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Tuple, NamedTuple, TYPE_CHECKING

import numpy as np
import pandas as pd
from py4design import py3dmodel, py2radiance

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Kian Wee Chen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from pyarrow import feather

from cea.constants import HOURS_IN_YEAR
from cea.resources.radiation.geometry_generator import BuildingGeometry, SURFACE_TYPES, SURFACE_DIRECTION_LABELS

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.resources.radiation.radiance import CEADaySim

BUILT_IN_BINARIES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bin")
REQUIRED_BINARIES = {"ds_illum", "epw2wea", "gen_dc", "oconv", "radfiles2daysim", "rtrace_dc"}
REQUIRED_LIBS = {"rayinit.cal", "isotrop_sky.cal"}


class GridSize(NamedTuple):
    roof: int
    walls: int


def create_temp_daysim_directory(directory):
    daysim_dir = os.path.join(BUILT_IN_BINARIES_PATH, sys.platform)

    os.makedirs(directory, exist_ok=True)
    temp_dir = tempfile.TemporaryDirectory(prefix="cea-daysim-temp", dir=directory)

    if sys.platform == "win32":
        daysim_dir = os.path.join(daysim_dir, "bin64")

    for file in os.listdir(daysim_dir):
        binary_file = os.path.join(daysim_dir, file)
        output_file = os.path.join(temp_dir.name, file)
        if not os.path.exists(output_file):
            shutil.copyfile(binary_file, output_file)

    atexit.register(temp_dir.cleanup)

    return temp_dir.name


def check_daysim_bin_directory(path_hint: Optional[str] = None, latest_binaries: bool = True) -> Tuple[str, Optional[str]]:
    """
    Check for the Daysim bin directory based on ``path_hint`` and return it on success.

    If the binaries could not be found there, check in a folder `Depencencies/Daysim` of the installation - this will
    catch installations on Windows that used the official CEA installer.

    Check the RAYPATH environment variable. Return that.

    Check for ``C:\\Daysim\\bin`` - it might be there?

    If the binaries can't be found anywhere, raise an exception.

    :param str path_hint: The path to check first, according to the `cea.config` file.
    :param bool latest_binaries: Use latest Daysim binaries
    :return: bin_path, lib_path: contains the Daysim binaries - otherwise an exception occurs.
    """

    def contains_binaries(path):
        """True if all the required binaries are found in path - note that binaries might have an extension"""
        try:
            found_binaries = set(binary for binary, _ in map(os.path.splitext, os.listdir(path)))
        except OSError:
            # could not find the binaries, bogus path
            return False
        return all(binary in found_binaries for binary in REQUIRED_BINARIES)

    def contains_libs(path):
        try:
            found_libs = set(os.listdir(path))
        except OSError:
            # could not find the libs, bogus path
            return False
        return all(lib in found_libs for lib in REQUIRED_LIBS)

    def contains_whitespace(path):
        """True if path contains whitespace"""
        return len(path.split()) > 1

    folders_to_check = []
    if path_hint is not None:
        folders_to_check.append(path_hint)

    # Path of shipped binaries
    shipped_daysim = os.path.join(os.path.dirname(__file__), "bin", sys.platform)
    folders_to_check.append(shipped_daysim)

    # Additional paths
    if sys.platform == "win32":
        # Check latest binaries only applies to Windows
        folders_to_check.append(os.path.join(shipped_daysim, "bin64" if latest_binaries else "bin"))
        folders_to_check.append(os.path.join(path_hint, "bin64" if latest_binaries else "bin"))

        # User might have a default DAYSIM installation
        folders_to_check.append(r"C:\Daysim\bin")

    elif sys.platform == "linux":
        # For docker
        folders_to_check.append(os.path.normcase(r"/Daysim/bin"))

    elif sys.platform == "darwin":
        pass

    # Expand paths
    folders_to_check = [os.path.abspath(os.path.normpath(os.path.normcase(p))) for p in folders_to_check]
    lib_path = None

    for possible_path in folders_to_check:
        if not contains_binaries(possible_path):
            continue

        # If path to binaries contains whitespace, provide a warning
        # if contains_whitespace(possible_path):
        #     warnings.warn(f"ATTENTION: Daysim binaries found in '{possible_path}', but its path contains whitespaces. "
        #                   "Consider moving the binaries to another path to use them.")
        #     continue

        if sys.platform == "win32":
            # Use path lib folder if it exists
            _lib_path = os.path.abspath(os.path.normpath(os.path.join(possible_path, "..", "lib")))
            if contains_libs(_lib_path):
                lib_path = _lib_path
            # Check if lib files in binaries path, for backward capability
            elif contains_libs(possible_path):
                lib_path = possible_path

        elif sys.platform == "darwin":
            # Remove unidentified developer warning when running binaries on mac
            for binary in REQUIRED_BINARIES:
                binary_path = os.path.join(possible_path, binary)
                result = subprocess.run(["xattr", "−l", binary_path], capture_output=True)
                if "com.apple.quarantine" in result.stdout.decode('utf-8'):
                    subprocess.run(["xattr", "-d", "com.apple.quarantine", binary_path])

        return str(possible_path), str(lib_path)

    raise ValueError("Could not find Daysim binaries - checked these paths: {}".format(", ".join(folders_to_check)))


def create_sensor_input_file(rad, chunk_n):
    sensor_file_path = os.path.join(rad.data_folder_path, "points_" + str(chunk_n) + ".pts")
    sensor_file = open(sensor_file_path, "w")
    sensor_pts_data = py2radiance.write_rad.sensor_file(rad.sensor_positions, rad.sensor_normals)
    sensor_file.write(sensor_pts_data)
    sensor_file.close()
    rad.sensor_file_path = sensor_file_path


def generate_sensor_surfaces(occface, grid_size, srf_type, orientation, normal, intersection):
    mid_pt = py3dmodel.calculate.face_midpt(occface)
    location_pt = py3dmodel.modify.move_pt(mid_pt, normal, 0.01)
    moved_oface = py3dmodel.fetch.topo2topotype(py3dmodel.modify.move(mid_pt, location_pt, occface))

    # put it into occ and subdivide surfaces
    sensor_surfaces = py3dmodel.construct.grid_face(moved_oface, grid_size, grid_size)

    # calculate list of properties per surface
    sensor_intersection = [intersection for x in sensor_surfaces]
    sensor_dir = [normal for x in sensor_surfaces]
    sensor_cord = [py3dmodel.calculate.face_midpt(x) for x in sensor_surfaces]
    sensor_type = [srf_type for x in sensor_surfaces]
    sensor_orientation = [orientation for x in sensor_surfaces]
    sensor_area = [py3dmodel.calculate.face_area(x) * (1.0 - scalar)
                   for x, scalar in zip(sensor_surfaces, sensor_intersection)]

    return sensor_dir, sensor_cord, sensor_type, sensor_area, sensor_orientation, sensor_intersection


def calc_sensors_building(building_geometry: BuildingGeometry, grid_size: GridSize):
    sensor_dir_list = []
    sensor_cord_list = []
    sensor_type_list = []
    sensor_area_list = []
    sensor_orientation_list = []
    sensor_intersection_list = []

    for srf_type in SURFACE_TYPES:
        occface_list = getattr(building_geometry, srf_type)
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
                                                           grid_size.roof if srf_type == "roofs" else grid_size.walls,
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


def calc_sensors_zone(building_names, locator, grid_size: GridSize, geometry_pickle_dir):
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
        locator.ensure_parent_folder_exists(locator.get_radiation_metadata(building_name))
        pd.DataFrame({'BUILDING': building_name,
                      'SURFACE': sensors_code,
                      'orientation': sensor_orientation_building,
                      'intersection': sensor_intersection_building,
                      'terrain_elevation': building_geometry.terrain_elevation,
                      'Xcoor': [x[0] for x in sensors_coords_building],
                      'Ycoor': [x[1] for x in sensors_coords_building],
                      'Zcoor': [x[2] for x in sensors_coords_building],
                      'Xdir': [x[0] for x in sensors_dir_building],
                      'Ydir': [x[1] for x in sensors_dir_building],
                      'Zdir': [x[2] for x in sensors_dir_building],
                      'AREA_m2': sensors_area_building,
                      'TYPE': sensors_type_building}).to_csv(locator.get_radiation_metadata(building_name), index=False)

    return sensors_coords_zone, sensors_dir_zone, sensors_total_number_list, names_zone, sensors_code_zone, sensor_intersection_zone


def isolation_daysim(chunk_n, cea_daysim: CEADaySim, building_names, locator, radiance_parameters, write_sensor_data,
                     grid_size: GridSize,
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

    daysim_project.create_sensor_input_file(sensors_coords_zone, sensors_dir_zone)

    print(f"Starting Daysim simulation for buildings: {names_zone}")
    print(f"Total number of sensors: {len(sensors_coords_zone)}")

    print('Writing radiance parameters')
    daysim_project.write_radiance_parameters(**radiance_parameters)

    print('Executing hourly solar isolation calculation')
    import time
    start = time.time()
    daysim_project.execute_gen_dc()
    daysim_project.execute_ds_illum()
    print(f"Daysim calculation took {time.time() - start} seconds")

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
    for building_name, sensors_number, sensor_code, sensor_intersection \
            in zip(names_zone, sensors_number_zone, sensors_code_zone, sensor_intersection_zone):

        # select sensors data
        sensor_data = solar_res[index:index+sensors_number]
        # set sensors that intersect with buildings to 0
        sensor_data[np.array(sensor_intersection) == 1] = 0
        items_sensor_name_and_result = pd.DataFrame(sensor_data, index=sensor_code)

        # create summary and save to disk
        date = weatherfile["date"]
        write_aggregated_results(building_name, items_sensor_name_and_result, locator, date)

        if write_sensor_data:
            sensor_data_path = locator.get_radiation_building_sensors(building_name)
            write_sensor_results(sensor_data_path, items_sensor_name_and_result)

        # Increase sensor index
        index = index + sensors_number

    # erase daysim folder to avoid conflicts after every iteration
    print('Removing results folder')
    daysim_project.cleanup_project()


def write_sensor_results(sensor_data_path, sensor_values):
    feather.write_feather(sensor_values.T, sensor_data_path, compression="zstd")


def write_aggregated_results(building_name, sensor_values: pd.DataFrame, locator: InputLocator, date):
    # Get sensor properties
    geometry = pd.read_csv(locator.get_radiation_metadata(building_name)).set_index('SURFACE')

    # Create map between sensors and building surfaces
    labels = geometry['TYPE'] + '_' + geometry['orientation']
    group_dict = labels.to_dict()

    # Ensure surface columns (sometimes windows do not exist)
    current_labels = set(labels.unique())
    missing_labels = SURFACE_DIRECTION_LABELS - current_labels

    extra_labels = current_labels - SURFACE_DIRECTION_LABELS
    if len(extra_labels) > 0:
        raise ValueError(f"Unrecognized surface names {extra_labels}")

    # Transform data
    sensor_values_kw = sensor_values.multiply(geometry['AREA_m2'], axis="index") / 1000
    data = sensor_values_kw.groupby(group_dict).sum().T.add_suffix('_kW')

    # TODO: Remove total sensor area information from output. Area information is repeated over rows.
    # Add area to data
    area = geometry['AREA_m2'].groupby(group_dict).sum().add_suffix('_m2')
    area_cols = pd.concat([area] * len(data), axis=1).T.set_index(data.index)
    data = pd.concat([data, area_cols], axis=1)

    # Add missing surfaces to output
    for surface in missing_labels:
        data[f"{surface}_kW"] = 0.0
        data[f"{surface}_m2"] = 0.0

    # Round values and add date index
    data = data.round(2)
    data["Date"] = date
    data.set_index("Date", inplace=True)

    locator.ensure_parent_folder_exists(locator.get_radiation_building(building_name))
    data.to_csv(locator.get_radiation_building(building_name))
