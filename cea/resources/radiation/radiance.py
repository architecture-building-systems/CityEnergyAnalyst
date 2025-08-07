import csv
import math
import os
import shutil
import subprocess
import shlex
import sys
from enum import Enum

import numpy as np

from cea.resources.radiation.geometry_generator import BuildingGeometry
from py4design.py3dmodel.fetch import points_frm_occface


class SensorOutputUnit(Enum):
    w_m2 = 1
    lux = 2


class CEADaySim:
    """
    This class helps to initialize the Daysim folder structure in the `staging_path`
    and encapsulates all the methods required to create the initial input files for Daysim
    (i.e radiance material file, radiance geometry file and weather file) which are needed for Daysim projects.
    It also initializes Daysim projects with the help of the `DaySimProject` class

    The staging folder is split into 2 folders, 'common_inputs' and 'projects'.
    'common_inputs' store the created input files which are shared among any running Daysim projects,
    'projects' store the folders of any running Daysim projects

    This splitting allows Daysim projects to be run parallel with multiprocessing

    :param str staging_path: Path where to create Daysim Project
    :param str daysim_dir: Directory where Daysim binaries are found
    """

    def __init__(self, staging_path, daysim_dir, daysim_lib):
        self.common_inputs = os.path.join(staging_path, 'common_inputs')
        self.projects_dir = os.path.join(staging_path, 'projects')
        self.daysim_dir = daysim_dir
        self.daysim_lib = daysim_lib
        self._create_folders()

        # Raw input files (radiance material and geometry)
        self.rad_material_path = os.path.join(self.common_inputs, 'radiance_material.rad')
        self.rad_geometry_path = os.path.join(self.common_inputs, 'radiance_geometry.rad')

        # Common generated input files
        self.daysim_material_path = os.path.join(self.common_inputs, 'daysim_material.rad')
        self.daysim_geometry_path = os.path.join(self.common_inputs, 'daysim_geometry.rad')
        self.wea_weather_path = os.path.join(self.common_inputs, 'weather_60min.wea')
        self.daysim_shading_path = os.path.join(self.common_inputs, 'daysim_shading.rad')

        # Header Properties
        self.site_info = None

    def _create_folders(self):
        os.makedirs(self.common_inputs, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)

    def initialize_daysim_project(self, project_name):
        """
        Returns a DaySimProject object that initializes a Daysim project with the name `project_name`

        :param str project_name: Name of Daysim project
        :return DaySimProject:
        """
        return DaySimProject(project_name, self.projects_dir, self.daysim_dir, self.daysim_lib,
                             self.daysim_material_path, self.daysim_geometry_path, self.wea_weather_path,
                             self.site_info, self.daysim_shading_path)

    def create_radiance_material(self, building_surface_properties):
        add_rad_mat(self.rad_material_path, building_surface_properties)

    def create_radiance_geometry(self, geometry_terrain, building_surface_properties, zone_building_names,
                                 surroundings_building_names, geometry_pickle_dir):
        create_rad_geometry(self.rad_geometry_path, geometry_terrain, building_surface_properties, zone_building_names,
                            surroundings_building_names, geometry_pickle_dir)

    def create_radiance_shading(self, tree_surfaces, leaf_area_densities):
        def tree_to_radiance(tree_id, tree_surface_list):
            for num, occ_face in enumerate(tree_surface_list):
                surface_name = f"tree_surface_{tree_id}_{num}"
                yield RadSurface(surface_name, occ_face, f"tree_material_{tree_id}")

        with open(self.daysim_shading_path, "w") as rad_file:
            # # write material for trees
            for i, tree in enumerate(tree_surfaces):
                # light would pass through at least 2 surfaces so we divide the effect by half
                transmissivity = math.sqrt(1 - leaf_area_densities[i])
                string = f"void glass tree_material_{i}\n" \
                         "0\n" \
                         "0\n" \
                         f"3 {transmissivity} {transmissivity} {transmissivity}"
                rad_file.writelines(string + '\n')

            for i, tree in enumerate(tree_surfaces):
                for tree_surface_rad in tree_to_radiance(i, tree):
                    rad_file.write(tree_surface_rad.rad())

    @staticmethod
    def run_cmd(cmd, daysim_dir, daysim_lib):
        print(f'Running command `{cmd}`')

        # Add daysim directory to path
        env = {
            "PATH": f'{daysim_dir}{os.pathsep}{os.environ["PATH"]}',
            "RAYPATH": daysim_lib
        }

        _cmd = shlex.split(cmd)
        if sys.platform == "win32":
            # Prepend daysim directory to binary for windows since PATH cannot be changed using env
            # Refer to https://docs.python.org/3/library/subprocess.html#popen-constructor
            _cmd[0] = f"{daysim_dir}\\{_cmd[0]}"

        process = subprocess.run(_cmd, capture_output=True, env=env)
        output = process.stdout.decode('utf-8')
        print(output)

        # Stops script if commands fail (i.e non-zero exit code)
        if process.returncode != 0:
            print(process.stderr)
            raise subprocess.CalledProcessError(process.returncode, cmd)

        return output

    @staticmethod
    def generate_project_header(project_name, project_directory, tmp_directory, daysim_bin_directory):
        return f"project_name {project_name}\n" \
               f"project_directory {project_directory}\n" \
               f"bin_directory {daysim_bin_directory}\n" \
               f"tmp_directory {tmp_directory}\n"

    @staticmethod
    def generate_geometry_header(daysim_material_path, daysim_geometry_path):
        return f"material_file {daysim_material_path}\n" \
               f"geometry_file {daysim_geometry_path}\n"

    @staticmethod
    def generate_site_info_header(site_info, wea_weather_path):
        return f"{site_info}\n" \
               "time_step 60\n" \
               f"wea_data_short_file {wea_weather_path}\n" \
               "wea_data_short_file_units 1\n" \
               "lower_direct_threshold 2\n" \
               "lower_diffuse_threshold 2\n"

    def execute_epw2wea(self, epw_weather_path, ground_reflectance=0.2):
        command = f'epw2wea "{epw_weather_path}" "{self.wea_weather_path}"'

        # get site information from stdout of epw2wea
        epw2wea_result = self.run_cmd(command, self.daysim_dir, self.daysim_lib)
        site_headers = epw2wea_result

        epw2wea_output = site_headers.replace('\r', '')
        self.site_info = f"{epw2wea_output}\n" \
                         f"ground_reflectance {ground_reflectance}\n"

        # Save info of original epw file
        weather_info_path = os.path.join(self.common_inputs, "weather_info.txt")
        with open(weather_info_path, "w") as weather_info:
            weather_info.write(f'# Original epw file: {epw_weather_path}')
            weather_info.write(self.site_info)

    def execute_radfiles2daysim(self):
        hea_path = os.path.join(self.common_inputs, "rad2daysim.hea")
        tmp_path = os.path.join(self.common_inputs, "tmp", "")
        project_header = self.generate_project_header("rad2daysim", self.common_inputs, tmp_path, self.daysim_dir)
        geometry_header = self.generate_geometry_header(os.path.basename(self.daysim_material_path),
                                                        os.path.basename(self.daysim_geometry_path))

        # create header file for radfiles2daysim
        with open(hea_path, "w") as hea_file:
            building_info = f"{project_header}\n" \
                            f"{geometry_header}\n" \
                            f"radiance_source_files 2, {self.rad_material_path}, {self.rad_geometry_path}\n"

            hea_file.write(building_info)

        command1 = f'radfiles2daysim "{hea_path}" -g -m -d'
        self.run_cmd(command1, self.daysim_dir, self.daysim_lib)


class DaySimProject(object):
    def __init__(self, project_name, project_directory, daysim_bin_directory, daysim_lib_directory,
                 daysim_material_path, daysim_geometry_path, wea_weather_path,
                 site_info, daysim_shading_path):

        # Project info
        self.project_name = project_name
        self.project_directory = project_directory
        # make sure folder paths have trailing slash (gen_dc will fail otherwise)
        self.project_path = os.path.join(project_directory, project_name, "")
        self.tmp_directory = os.path.join(self.project_path, "tmp", "")
        self.daysim_bin_directory = os.path.join(daysim_bin_directory, "")
        self.daysim_lib_directory = os.path.join(daysim_lib_directory)

        # Input files
        self.daysim_material_path = daysim_material_path
        self.daysim_geometry_path = daysim_geometry_path
        self.wea_weather_path = wea_weather_path
        self.sensor_path = os.path.join(self.project_path, "sensors.pts")
        self.daysim_shading_path = daysim_shading_path

        self.hea_path = os.path.join(self.project_path, f"{project_name}.hea")
        # Header Properties
        self.site_info = site_info
        self._create_project_header_file()

    def _ensure_exist(self):
        # Ensure input files exist
        required = [self.daysim_material_path, self.daysim_geometry_path, self.wea_weather_path]
        missing = [file for file in required if not os.path.exists(file)]
        if len(missing):
            raise OSError(
                f"Could not find required input files for Daysim in the following paths: {', '.join(missing)}"
            )

        # Create required folders
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(self.tmp_directory, exist_ok=True)

    def _create_project_header_file(self):
        self._ensure_exist()

        daysim_material_path = os.path.relpath(self.daysim_material_path, self.project_path)
        daysim_geometry_path = os.path.relpath(self.daysim_geometry_path, self.project_path)
        wea_weather_path = os.path.relpath(self.wea_weather_path, self.project_path)

        project_header = CEADaySim.generate_project_header(self.project_name, self.project_path, self.tmp_directory,
                                                           self.daysim_bin_directory)
        geometry_header = CEADaySim.generate_geometry_header(daysim_material_path, daysim_geometry_path)
        site_info_header = CEADaySim.generate_site_info_header(self.site_info, wea_weather_path)

        # The -u- flag disables uncorrelated sampling and uses a fixed seed (0) in rtrace
        # This makes the results reproducible / deterministic
        additional_rtrace_parameter = "additional_rtrace_parameter -u-"

        with open(self.hea_path, "w") as hea_file:
            header = f"{project_header}\n" \
                     f"{site_info_header}\n" \
                     f"{geometry_header}\n" \
                     f"{additional_rtrace_parameter}\n" \

            hea_file.write(header)

    @property
    def shading_exists(self):
        return os.path.exists(self.daysim_shading_path)

    def cleanup_project(self):
        shutil.rmtree(self.project_path)

    def create_sensor_input_file(self, sensor_positions, sensor_normals,
                                 sensor_output_unit: SensorOutputUnit = SensorOutputUnit.w_m2):
        """
        Creates sensor input file and writes its location to the header file

        output_units <integrer n>

        n = 1 solar irradiance (W/m2)
        n = 2 illumiance (lux)

        :param sensor_positions:
        :param sensor_normals:
        :param sensor_output_unit: the unit for all sensor points (w/m2 or lux)
        """
        # create sensor file
        with open(self.sensor_path, "w") as sensor_file:
            sensors = "".join(f"{pos[0]} {pos[1]} {pos[2]} {norm[0]} {norm[1]} {norm[2]}\n"
                              for pos, norm in zip(sensor_positions, sensor_normals))
            sensor_file.write(sensors)

        # add sensor file location to header file
        with open(self.hea_path, "a") as hea_file:
            # write the sensor file location into the .hea
            sensor_path = os.path.relpath(self.sensor_path, self.project_path)
            hea_file.write(f"sensor_file {sensor_path}\n")

            # write unit for sensor points
            hea_file.write(f"output_units {sensor_output_unit.value}\n")

            # Write senor_file_unit to header file
            # Fix to allow Daysim 5.2 binaries to work, not required for compiled binaries from latest branch
            unit_code = {  # 0 = lux, 2 = w/m2
                SensorOutputUnit.lux: "0",
                SensorOutputUnit.w_m2: "2"
            }
            sensor_str = f"{unit_code[sensor_output_unit]} " * len(sensor_positions)
            hea_file.write(f"\nsensor_file_unit {sensor_str}\n")

    def write_radiance_parameters(self, rad_ab, rad_ad, rad_as, rad_ar, rad_aa, rad_lr, rad_st, rad_sj, rad_lw, rad_dj,
                                  rad_ds, rad_dr, rad_dp):
        """
        This function writes the radiance parameters for the Daysim simulation to the header file.

        :param int rad_ab: Number of ambient bounces.
        :param int rad_ad: Number of ambient divisions.
        :param int rad_as: Number of ambient super-samples.
        :param int rad_ar: Ambient resolution.
        :param float rad_aa: Ambient accuracy.
        :param int rad_lr: Maximum number of reflections.
        :param float rad_st: Specular sampling threshold.
        :param float rad_sj: Specular sampling jitter.
        :param float rad_lw: Minimum weight of each ray.
        :param float rad_dj: Direct jitter.
        :param float rad_ds: Direct sampling ration.
        :param int rad_dr: Number of relays from secondary sources.
        :param int rad_dp: Secondary source pre-sampling density.
        """

        with open(self.hea_path, "a") as hea_file:
            radiance_parameters = f"ab {rad_ab}\n" \
                                  f"ad {rad_ad}\n" \
                                  f"as {rad_as}\n" \
                                  f"ar {rad_ar}\n" \
                                  f"aa {rad_aa}\n" \
                                  f"lr {rad_lr}\n" \
                                  f"st {rad_st}\n" \
                                  f"sj {rad_sj}\n" \
                                  f"lw {rad_lw}\n" \
                                  f"dj {rad_dj}\n" \
                                  f"ds {rad_ds}\n" \
                                  f"dr {rad_dr}\n" \
                                  f"dp {rad_dp}\n"

            hea_file.write(radiance_parameters)

    def generate_shading_profile(self):
        """
        The external shading profile should be a comma seperate file with a three line header and the format:
        month, day, hour, shading fraction [0,1] (0=fully opened;1=fully closed) in each line.

        Creates shading profile in the temp directory of the project.
        Uses date values found in the weather file for DAYSIM
        """
        shading_profile = os.path.join(self.tmp_directory, "shading_profile.csv")
        with open(self.wea_weather_path) as wea, open(shading_profile, "w") as f:
            csv_writer = csv.writer(f, delimiter=',')
            wea_reader = csv.reader(wea, delimiter=' ', )

            # Write headers
            csv_writer.writerows([
                ["# Daysim annual blind schdule", "", "", ""],
                ["# time_step 60", "comment:", "", ""],
                ["# month", "day", "time", "shading fraction"]
            ])

            # Skip first 6 rows (headers) in weather file
            for i in range(6):
                next(wea_reader)

            for row in wea_reader:
                date_columns = row[:3]
                csv_writer.writerow(date_columns + [1])

        return shading_profile

    def write_shading_parameters(self):
        """
        This function writes the shading properties into the header file.
        If no shading is found, static shading mode is used.

        `shading 1 <descriptive_string> <file_name.dc> <file_name.ill>`

        The integer 1 represents static/no shading

        If shading if found, generated required files and load shading geometries

        `shading -n
        <base_file_name.dc> <base_file_name_no_blinds.ill>
        [followed by n shading group definitions]
        <shading_group_1_name>
        m
        control_keyword <shading_group_opened.rad> [followed by m lines]
        <shading_group_1_state1.rad> <shading_group_1_state1.dc> <shading_group_1_state1.ill>`

        with n = 1 or 2 = number of shading groups, m = number of states in shading group
        """
        dc_file = f"{self.project_name}.dc"
        ill_file = f"{self.project_name}.ill"

        if not self.shading_exists:
            # Use static system
            shading_parameters = f"shading 1 static_system {dc_file} {ill_file}\n"
        else:
            # # Create empty shading file for base case
            # empty_shading_file = "no_shading.rad"
            # with open(os.path.join(self.project_path, empty_shading_file), 'w') as f:
            #     pass
            #
            # # Generate shading schedule
            # shading_profile = self.generate_shading_profile()
            #
            # shading_parameters = (f"shading -1\n"
            #                       f"{dc_file} {ill_file}\n"
            #                       f"tree_shading_group\n"
            #                       f"1\n"
            #                       f"AnnualShadingSchedule {shading_profile} {empty_shading_file}\n"
            #                       f"{self.daysim_shading_path} shading_{dc_file} shading_{ill_file}")

            shading_parameters = (f"shading -1\n"
                                  f"{dc_file} {ill_file}\n"
                                  f"tree_shading_group\n"
                                  f"0\n"
                                  f"ManualControl {self.daysim_shading_path}\n")

        with open(self.hea_path, "a") as hea_file:
            hea_file.write(shading_parameters)

    def execute_gen_dc(self):
        """
        Calculates daylight coefficient files

        command parameters:

        -dir    calculates direct daylight coefficients only
        -dif    calculates diffuse daylight coefficients only
        -paste  pastes direct and diffuse daylight coefficient output files into a single complete file
        """
        # write the shading header
        self.write_shading_parameters()

        command1 = f'gen_dc "{self.hea_path}" -dir'
        command2 = f'gen_dc "{self.hea_path}" -dif'
        command3 = f'gen_dc "{self.hea_path}" -paste'

        CEADaySim.run_cmd(command1, self.daysim_bin_directory, self.daysim_lib_directory)
        CEADaySim.run_cmd(command2, self.daysim_bin_directory, self.daysim_lib_directory)
        CEADaySim.run_cmd(command3, self.daysim_bin_directory, self.daysim_lib_directory)

    def execute_ds_illum(self):
        command1 = f'ds_illum "{self.hea_path}"'
        CEADaySim.run_cmd(command1, self.daysim_bin_directory, self.daysim_lib_directory)

    def eval_ill(self):
        """
        This function reads the output file from running `ds_illum`, parses the space separated values
        and returns the values as a numpy array.

        Values in the file only have 2 decimal places, so we are using float32 to save memory
        Rows are hours, Columns are sensor. Transpose output to make rows sensors

        :return: Numpy array of hourly irradiance results of sensor points
        """

        ill_path = os.path.join(self.project_path, f"{self.project_name}.ill")
        # if self.shading_exists:
        #     ill_path = os.path.join(self.project_path, f"shading_{self.project_name}.ill")
        with open(ill_path) as f:
            reader = csv.reader(f, delimiter=' ')
            data = np.array([np.array(row[4:], dtype=np.float32) for row in reader]).T

        return data


class RadSurface(object):
    """
    An object that contains all the surface information running a Radiance/Daysim simulation.

    :param str name: Name of surface
    :param OCC.TopoDS.TopoDS_Face occ_face: Polygon (OCC TopoDS_Face) of surface
    :param str material: Name of material
    """
    __slots__ = ['name', 'points', 'material']

    def __init__(self, name, occ_face, material):
        # Make sure there are no spaces in the name, which could affect Daysim parsing the radiance geometry file
        self.name = name.replace(" ", "_")
        self.points = points_frm_occface(occ_face)
        self.material = material

    def rad(self):
        """
        Returns surface information as Radiance string format.

        Format from Radiance manual:
        `modifier` `type` `identifier`
        `number of string arguments` `string arguments`
        `number of integer arguments` `integer arguments`
        `number of decimal arguments` `decimal arguments`

        In this case,
        `modifier` would be the name of the material
        `type` would be 'polygon'
        there will be no string or integer arguments
        decimal arguments would be points of vertices

        :returns str: The surface written into radiance readable string.
        """

        num_of_points = len(self.points) * 3
        points = "\n".join([f"{point[0]}  {point[1]}  {point[2]}" for point in self.points])

        surface = f"{self.material} polygon {self.name}\n" \
                  f"0\n" \
                  f"0\n" \
                  f"{num_of_points}\n" \
                  f"{points}\n"
        return surface


def calc_transmissivity(G_value):
    """
    Calculate window transmissivity from its transmittance using an empirical equation from Radiance.

    :param float G_value: Solar energy transmittance of windows (dimensionless)
    :return float: Transmissivity

    [RADIANCE, 2010] The Radiance 4.0 Synthetic Imaging System. Lawrence Berkeley National Laboratory.
    """
    return (math.sqrt(0.8402528435 + 0.0072522239 * G_value * G_value) - 0.9166530661) / 0.0036261119 / G_value


def add_rad_mat(daysim_mat_file, ageometry_table):
    file_path = daysim_mat_file
    roughness = 0.02
    specularity = 0.03
    with open(file_path, 'w') as write_file:
        # first write the material use for the terrain and surrounding buildings
        string = "void plastic reflectance0.2\n" \
                 "0\n" \
                 "0\n" \
                 "5 0.5360 0.1212 0.0565 0 0"
        write_file.writelines(string + '\n')

        written_mat_name_list = set()
        for geo in ageometry_table.index.values:
            # Wall material
            mat_name = f"wall_{ageometry_table['type_wall'][geo]}"
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_wall'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness
                string = f"void plastic {mat_name}\n" \
                         f"0\n" \
                         f"0\n" \
                         f"5 {mat_value1} {mat_value2} {mat_value3} {mat_value4} {mat_value5}"
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.add(mat_name)

            # Window material
            mat_name = f"win_{ageometry_table['type_win'][geo]}"
            if mat_name not in written_mat_name_list:
                mat_value1 = calc_transmissivity(ageometry_table['G_win'][geo])
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                string = f"void glass {mat_name}\n" \
                         f"0\n" \
                         f"0\n" \
                         f"3 {mat_value1} {mat_value2} {mat_value3}"
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.add(mat_name)

            # Roof material
            mat_name = f"roof_{ageometry_table['type_roof'][geo]}"
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_roof'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness

                string = f"void plastic {mat_name}\n" \
                         f"0\n" \
                         f"0\n" \
                         f"5 {mat_value1} {mat_value2} {mat_value3} {mat_value4} {mat_value5}"
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.add(mat_name)


def create_rad_geometry(file_path, geometry_terrain, building_surface_properties, zone_building_names,
                        surroundings_building_names, geometry_pickle_dir):
    def terrain_to_radiance(tin_occface_terrain):
        for num, occ_face in enumerate(tin_occface_terrain):
            surface_name = f"terrain_srf{num}"
            material_name = "reflectance0.2"
            yield RadSurface(surface_name, occ_face, material_name)

    def zone_building_to_radiance(building_properties, surface_properties):
        name = building_properties.name

        # windows
        for num, occ_face in enumerate(building_properties.windows):
            material = surface_properties['type_win'][name]
            surface_name = f"win_{name}_{num}"
            material_name = f"win_{material}"
            yield RadSurface(surface_name, occ_face, material_name)

        # walls
        for num, occ_face in enumerate(building_properties.walls):
            material = surface_properties['type_wall'][name]
            surface_name = f"wall_{name}_{num}"
            material_name = f"wall_{material}"
            yield RadSurface(surface_name, occ_face, material_name)

        # roofs
        for num, occ_face in enumerate(building_properties.roofs):
            material = surface_properties['type_roof'][name]
            surface_name = f"roof_{name}_{num}"
            material_name = f"roof_{material}"
            yield RadSurface(surface_name, occ_face, material_name)

    def surrounding_building_to_radiance(building_properties):
        name = building_properties.name

        # walls
        for num, occ_face in enumerate(building_properties.walls):
            surface_name = f"surrounding_buildings_wall_{name}_{num}"
            yield RadSurface(surface_name, occ_face, "reflectance0.2")

        # roofs
        for num, occ_face in enumerate(building_properties.roofs):
            surface_name = f"surrounding_buildings_roof_{name}_{num}"
            yield RadSurface(surface_name, occ_face, "reflectance0.2")

    with open(file_path, "w") as rad_file:
        for terrain_surface in terrain_to_radiance(geometry_terrain):
            rad_file.write(terrain_surface.rad())

        for building_name in zone_building_names:
            building_geometry = BuildingGeometry.load(os.path.join(geometry_pickle_dir, 'zone', building_name))
            for building_surface in zone_building_to_radiance(building_geometry, building_surface_properties):
                rad_file.write(building_surface.rad())

        for building_name in surroundings_building_names:
            building_geometry = BuildingGeometry.load(
                os.path.join(geometry_pickle_dir, 'surroundings', building_name))
            for building_surface in surrounding_building_to_radiance(building_geometry):
                rad_file.write(building_surface.rad())
