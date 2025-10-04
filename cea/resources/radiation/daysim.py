from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING, NamedTuple, Optional, Tuple

import numpy as np
import pandas as pd

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
from cea.resources.radiation.building_geometry_radiation import (
    BuildingGeometryForRadiation,
    SURFACE_DIRECTION_LABELS,
    SURFACE_TYPES,
)
from cea.resources.radiation.sensor_area_calculator import (
    build_sensor_patches,
    patch_centers_from_patches,
)
from cea.resources.utils import get_radiation_bin_path

if TYPE_CHECKING:
    from compas.geometry import Point, Polygon, Vector

    from cea.inputlocator import InputLocator
    from cea.resources.radiation.radiance import CEADaySim

BUILT_IN_BINARIES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bin")
REQUIRED_BINARIES = {"ds_illum", "epw2wea", "gen_dc", "oconv", "radfiles2daysim", "rtrace_dc"}
REQUIRED_LIBS = {"rayinit.cal", "isotrop_sky.cal"}



class GridSize(NamedTuple):
    roof: int
    walls: int


def check_daysim_bin_directory(path_hint: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Check for the Daysim bin directory based on ``path_hint`` and return it on success.

    If the binaries could not be found there, check in a folder `Depencencies/Daysim` of the installation - this will
    catch installations on Windows that used the official CEA installer.

    Check the RAYPATH environment variable. Return that.

    Check for ``C:\\Daysim\\bin`` - it might be there?

    If the binaries can't be found anywhere, raise an exception.

    :param str path_hint: The path to check first, according to the `cea.config` file.
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

    # Check site-packages location first (where binaries are actually installed)
    site_package_daysim = get_radiation_bin_path()
    if site_package_daysim:
        folders_to_check.append(site_package_daysim)

    # Fallback: Path relative to this script (for development or custom setups)
    shipped_daysim = os.path.join(os.path.dirname(__file__), "bin", sys.platform)
    folders_to_check.append(shipped_daysim)

    # Additional paths
    if sys.platform == "win32":
        folders_to_check.append(os.path.join(shipped_daysim, "bin64"))
        # User might have a default DAYSIM installation
        folders_to_check.append(r"C:\Daysim\bin")

    elif sys.platform == "linux":
        # For docker
        folders_to_check.append(os.path.normcase(r"/Daysim/bin"))

    elif sys.platform == "darwin":
        pass

    # Expand paths
    folders_to_check = [os.path.abspath(os.path.normpath(os.path.normcase(p))) for p in folders_to_check]
    lib_path = os.path.join(os.path.dirname(__file__), "lib")

    for possible_path in folders_to_check:
        if not contains_binaries(possible_path):
            continue

        # If path to binaries contains whitespace, provide a warning
        # if contains_whitespace(possible_path):
        #     warnings.warn(f"ATTENTION: Daysim binaries found in '{possible_path}', but its path contains whitespaces. "
        #                   "Consider moving the binaries to another path to use them.")
        #     continue

        elif sys.platform == "darwin":
            # Remove unidentified developer warning when running binaries on mac
            for binary in REQUIRED_BINARIES:
                binary_path = os.path.join(possible_path, binary)
                result = subprocess.run(["xattr", "−l", binary_path], capture_output=True)
                if "com.apple.quarantine" in result.stdout.decode('utf-8'):
                    subprocess.run(["xattr", "-d", "com.apple.quarantine", binary_path])

        return str(possible_path), str(lib_path)

    raise ValueError("Could not find Daysim binaries - checked these paths: {}".format(", ".join(folders_to_check)))


def generate_sensor_surfaces(
    face: Polygon,
    grid_size: float,
    srf_type: str,
    orientation: str,
    normal: Vector,
    face_intersection: int,
) -> Tuple[
    list[Vector],
    list[Point],
    list[str],
    list[float],
    list[str],
    list[int],
]:
    moved_face: Polygon = face.translated(normal.scaled(0.01))
    _, patches_nested, _ = build_sensor_patches(moved_face, grid_dx=grid_size, grid_dy=grid_size)
    sensors, _, areas, _ = patch_centers_from_patches(patches_nested)
    
    n_sensors = len(sensors)
    # calculate list of properties per surface
    sensor_intersection = [face_intersection] * n_sensors
    sensor_dir = [normal] * n_sensors
    sensor_coord = sensors
    sensor_type = [srf_type] * n_sensors
    sensor_orientation = [orientation] * n_sensors
    sensor_area = areas

    return sensor_dir, sensor_coord, sensor_type, sensor_area, sensor_orientation, sensor_intersection


def calc_sensors_building(
    building_geometry: BuildingGeometryForRadiation, grid_size: GridSize
) -> tuple[
    list[Vector],
    list[Point],
    list[str],
    list[float],
    list[str],
    list[int],
]:
    sensor_intersection_list: list[int] = []
    sensor_dir_list: list[Vector] = []
    sensor_coord_list: list[Point] = []
    sensor_type_list: list[str] = []
    sensor_area_list: list[float] = []
    sensor_orientation_list: list[str] = []

    for srf_type in SURFACE_TYPES:
        face_list, orientation_list, normals_list, interesection_list = (
            building_geometry.group(srf_type)
        )
        for orientation, normal, face, intersection in zip(
            orientation_list, normals_list, face_list, interesection_list
        ):
            (
                sensor_dir,
                sensor_coord,
                sensor_type,
                sensor_area,
                sensor_orientation,
                sensor_intersection,
            ) = generate_sensor_surfaces(
                face,
                grid_size.roof if srf_type == "roofs" else grid_size.walls,
                srf_type,
                orientation,
                normal,
                intersection,
            )
            sensor_intersection_list.extend(sensor_intersection)
            sensor_dir_list.extend(sensor_dir)
            sensor_coord_list.extend(sensor_coord)
            sensor_type_list.extend(sensor_type)
            sensor_area_list.extend(sensor_area)
            sensor_orientation_list.extend(sensor_orientation)

    return (
        sensor_dir_list,
        sensor_coord_list,
        sensor_type_list,
        sensor_area_list,
        sensor_orientation_list,
        sensor_intersection_list,
    )


def calc_sensors_zone(
    building_names: list[str],
    locator: InputLocator,
    grid_size: GridSize,
    geometry_pickle_dir: str,
) -> tuple[
    list[Point], list[Vector], list[int], list[str], list[list[str]], list[list[int]]
]:
    sensors_coords_zone: list[Point] = []
    sensors_dir_zone: list[Vector] = []
    sensors_total_number_list: list[int] = []
    names_zone: list[str] = []
    sensors_code_zone: list[list[str]] = []
    sensor_intersection_zone: list[list[int]] = []
    for building_name in building_names:
        building_geometry = BuildingGeometryForRadiation.load(os.path.join(geometry_pickle_dir, 'zone', building_name))
        # get sensors in the building
        (
            sensors_dir_building,
            sensors_coords_building,
            sensors_type_building,
            sensors_area_building,
            sensor_orientation_building,
            sensor_intersection_building,
        ) = calc_sensors_building(building_geometry, grid_size)

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
                      'Xcoor': [p.x for p in sensors_coords_building],
                      'Ycoor': [p.y for p in sensors_coords_building],
                      'Zcoor': [p.z for p in sensors_coords_building],
                      'Xdir': [vec.x for vec in sensors_dir_building],
                      'Ydir': [vec.y for vec in sensors_dir_building],
                      'Zdir': [vec.z for vec in sensors_dir_building],
                      'AREA_m2': sensors_area_building,
                      'TYPE': sensors_type_building}).to_csv(locator.get_radiation_metadata(building_name), index=False)

    return sensors_coords_zone, sensors_dir_zone, sensors_total_number_list, names_zone, sensors_code_zone, sensor_intersection_zone


def isolation_daysim(chunk_n, cea_daysim: CEADaySim, building_names: list[str], locator, radiance_parameters, write_sensor_data,
                     grid_size: GridSize,
                     max_global, weatherfile, geometry_pickle_dir):
    # initialize daysim project
    daysim_project = cea_daysim.initialize_daysim_project('chunk_{n}'.format(n=chunk_n))
    print('Creating daysim project in: {daysim_dir}'.format(daysim_dir=daysim_project.project_path))

    # calculate sensors
    print("Calculating and sending sensor points")
    (
        sensors_coords_zone,
        sensors_dir_zone,
        sensors_number_zone,
        names_zone,
        sensors_code_zone,
        sensor_intersection_zone,
    ) = calc_sensors_zone(building_names, locator, grid_size, geometry_pickle_dir)

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
    for building_name, sensors_number, sensor_code, sensor_intersection in zip(
        names_zone, sensors_number_zone, sensors_code_zone, sensor_intersection_zone
    ):

        # select sensors data
        sensor_data = solar_res[index:index + sensors_number]
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
