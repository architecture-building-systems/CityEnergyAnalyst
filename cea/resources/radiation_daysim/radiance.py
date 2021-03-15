import math
import os
import shutil
import subprocess

import pandas as pd

from cea import suppress_3rd_party_debug_loggers
from cea.resources.radiation_daysim.geometry_generator import BuildingGeometry

suppress_3rd_party_debug_loggers()

import py4design.py2radiance as py2radiance
from py4design.py3dmodel.fetch import points_frm_occface


class CEADaySim(object):
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

    def __init__(self, staging_path, daysim_dir):
        self.common_inputs = os.path.join(staging_path, 'common_inputs')
        self.projects_dir = os.path.join(staging_path, 'projects')
        self.daysim_dir = daysim_dir
        self._create_folders()

        # Raw input files (radiance material and geometry)
        self.rad_material_path = os.path.join(self.common_inputs, 'radiance_material.rad')
        self.rad_geometry_path = os.path.join(self.common_inputs, 'radiance_geometry.rad')

        # Common generated input files
        self.daysim_material_path = os.path.join(self.common_inputs, 'daysim_material.rad')
        self.daysim_geometry_path = os.path.join(self.common_inputs, 'daysim_geometry.rad')
        self.wea_weather_path = os.path.join(self.common_inputs, 'weather_60min.wea')

        # Header Properties
        self.site_info = None

    def _create_folders(self):
        if not os.path.exists(self.common_inputs):
            os.makedirs(self.common_inputs)
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def initialize_daysim_project(self, project_name):
        """
        Returns a DaySimProject object that initializes a Daysim project with the name `project_name`

        :param str project_name: Name of Daysim project
        :return DaySimProject:
        """
        return DaySimProject(project_name, self.projects_dir, self.daysim_dir,
                             self.daysim_material_path, self.daysim_geometry_path, self.wea_weather_path,
                             self.site_info)

    def create_radiance_material(self, building_surface_properties):
        add_rad_mat(self.rad_material_path, building_surface_properties)

    def create_radiance_geometry(self, geometry_terrain, building_surface_properties, zone_building_names,
                                 surroundings_building_names, geometry_pickle_dir):
        create_rad_geometry(self.rad_geometry_path, geometry_terrain, building_surface_properties, zone_building_names,
                            surroundings_building_names, geometry_pickle_dir)

    @staticmethod
    def run_cmd(cmd, cwd=None):
        print('Running command `{}`{}'.format(cmd, '' if cwd is None else ' in `{}`'.format(cwd)))
        try:
            # Stops script if commands fail (i.e non-zero exit code)
            subprocess.check_call(cmd, cwd=cwd, stderr=subprocess.STDOUT, env=os.environ)
        except TypeError as error:
            if error.message == "environment can only contain strings":
                for key in os.environ.keys():
                    value = os.environ[key]
                    if not isinstance(value, str):
                        print("Bad ENVIRON key: {key}={value} ({value_type})".format(
                            key=key, value=value, value_type=type(value)))
            raise error

    @staticmethod
    def generate_project_header(project_name, project_directory, tmp_directory, daysim_bin_directory):
        return "project_name {project_name}\n" \
               "project_directory {project_directory}\n" \
               "bin_directory {bin_directory}\n" \
               "tmp_directory {tmp_directory}\n".format(project_name=project_name,
                                                        project_directory=project_directory,
                                                        bin_directory=daysim_bin_directory,
                                                        tmp_directory=tmp_directory)

    @staticmethod
    def generate_geometry_header(daysim_material_path, daysim_geometry_path):
        return "material_file {daysim_material_path}\n" \
               "geometry_file {daysim_geometry_path}\n".format(daysim_material_path=daysim_material_path,
                                                               daysim_geometry_path=daysim_geometry_path)

    @staticmethod
    def generate_site_info_header(site_info, wea_weather_path):
        return "{site_info}" \
               "time_step 60\n" \
               "wea_data_short_file {wea_weather_path}\n" \
               "wea_data_short_file_units 1\n" \
               "lower_direct_threshold 2\n" \
               "lower_diffuse_threshold 2\n".format(site_info=site_info, wea_weather_path=wea_weather_path)

    def execute_epw2wea(self, epw_weather_path, ground_reflectance=0.2):
        command = 'epw2wea "{epw_weather_path}" "{wea_weather_path}"'.format(epw_weather_path=epw_weather_path,
                                                                             wea_weather_path=self.wea_weather_path)
        print(f'Running command `{command}`')

        # get site information from stdout of epw2wea
        epw2wea_result = subprocess.run(command, stdout=subprocess.PIPE)
        site_headers = epw2wea_result.stdout.decode('utf-8')

        self.site_info = "{epw2wea_output}\n" \
                         "ground_reflectance {ground_reflectance}\n".format(
            epw2wea_output="\n".join(site_headers.split("\r\n")),
            ground_reflectance=ground_reflectance)

        # Save info of original epw file
        weather_info_path = os.path.join(self.common_inputs, "weather_info.txt")
        with open(weather_info_path, "w") as weather_info:
            weather_info.write('# Original epw file: {epw_weather_path}'.format(epw_weather_path=epw_weather_path))
            weather_info.write(self.site_info)

    def execute_radfiles2daysim(self):
        hea_path = os.path.join(self.common_inputs, "rad2daysim.hea")
        tmp_path = os.path.join(self.common_inputs, "tmp", "")
        project_header = self.generate_project_header("rad2daysim", self.common_inputs, tmp_path, self.daysim_dir)
        geometry_header = self.generate_geometry_header(os.path.basename(self.daysim_material_path),
                                                        os.path.basename(self.daysim_geometry_path))

        # create header file for radfiles2daysim
        with open(hea_path, "w") as hea_file:
            building_info = "{project_header}\n" \
                            "{geometry_header}\n" \
                            "radiance_source_files 2, {rad_material_path}, {rad_geometry_path}\n".format(
                project_header=project_header,
                geometry_header=geometry_header,
                rad_material_path=self.rad_material_path,
                rad_geometry_path=self.rad_geometry_path)

            hea_file.write(building_info)

        command1 = 'radfiles2daysim "{hea_path}" -g -m -d'.format(hea_path=hea_path)
        self.run_cmd(command1)


class DaySimProject(object):
    def __init__(self, project_name, project_directory, daysim_bin_directory,
                 daysim_material_path, daysim_geometry_path, wea_weather_path,
                 site_info):

        # Project info
        self.project_name = project_name
        self.project_directory = project_directory
        # make sure folder paths have trailing slash (gen_dc will fail otherwise)
        self.project_path = os.path.join(project_directory, project_name, "")
        self.tmp_directory = os.path.join(self.project_path, "tmp", "")
        self.daysim_bin_directory = os.path.join(daysim_bin_directory, "")
        self._create_folders()

        # Input files
        self.daysim_material_path = daysim_material_path
        self.daysim_geometry_path = daysim_geometry_path
        self.wea_weather_path = wea_weather_path
        self.sensor_path = os.path.join(self.project_path, "sensors.pts")

        self.hea_path = os.path.join(self.project_path, "{project_name}.hea".format(project_name=project_name))
        # Header Properties
        self.site_info = site_info
        self._create_project_header_file()

    def _create_folders(self):
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)
        if not os.path.exists(self.tmp_directory):
            os.makedirs(self.tmp_directory)

    def _create_project_header_file(self):
        daysim_material_path = os.path.relpath(self.daysim_material_path, self.project_path)
        daysim_geometry_path = os.path.relpath(self.daysim_geometry_path, self.project_path)
        wea_weather_path = os.path.relpath(self.wea_weather_path, self.project_path)

        project_header = CEADaySim.generate_project_header(self.project_name, self.project_path, self.tmp_directory,
                                                           self.daysim_bin_directory)
        geometry_header = CEADaySim.generate_geometry_header(daysim_material_path, daysim_geometry_path)
        site_info_header = CEADaySim.generate_site_info_header(self.site_info, wea_weather_path)

        with open(self.hea_path, "w") as hea_file:
            header = "{project_header}\n" \
                     "{site_info_header}\n" \
                     "{geometry_header}\n".format(project_header=project_header, geometry_header=geometry_header,
                                                  site_info_header=site_info_header)
            hea_file.write(header)

    def cleanup_project(self):
        shutil.rmtree(self.project_path)

    def create_sensor_input_file(self, sensor_positions, sensor_normals, num_sensors, sensor_file_unit):
        """
        Creates sensor input file and writes its location to the header file

        output_units <integrer n>

        n = 1 solar irradiance (W/m2)
        n = 2 illumiance (lux)

        :param sensor_positions:
        :param sensor_normals:
        :param str sensor_file_unit: the unit for all sensor points (w/m2 or lux)
        """
        sensor_pts_data = py2radiance.write_rad.sensor_file(sensor_positions, sensor_normals)

        # create sensor file
        with open(self.sensor_path, "w") as sensor_file:
            sensor_file.write(sensor_pts_data)

        # add sensor file location to header file
        with open(self.hea_path, "a") as hea_file:
            # write the sensor file location into the .hea
            sensor_path = os.path.relpath(self.sensor_path, self.project_path)
            hea_file.write("sensor_file {sensor_path}\n".format(sensor_path=sensor_path))

            # write unit for sensor points
            if sensor_file_unit == "w/m2":
                hea_file.write("output_units 1\n")
            if sensor_file_unit == "lux":
                hea_file.write("output_units 2\n")

            # Write senor_file_unit to header file
            # Fix to allow Daysim 5.2 binaries to work, not required for complied binaries from latest branch
            unit_num = "0" if sensor_file_unit == 'lux' else "2"  # 0 = lux, 2 = w/m2
            sensor_str = (unit_num + " ") * num_sensors

            hea_file.write("\nsensor_file_unit {sensor_str}\n".format(sensor_str=sensor_str))

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
            radiance_parameters = "ab {rad_ab}\n" \
                                  "ad {rad_ad}\n" \
                                  "as {rad_as}\n" \
                                  "ar {rad_ar}\n" \
                                  "aa {rad_aa}\n" \
                                  "lr {rad_lr}\n" \
                                  "st {rad_st}\n" \
                                  "sj {rad_sj}\n" \
                                  "lw {rad_lw}\n" \
                                  "dj {rad_dj}\n" \
                                  "ds {rad_ds}\n" \
                                  "dr {rad_dr}\n" \
                                  "dp {rad_dp}\n".format(rad_ab=rad_ab, rad_ad=rad_ad, rad_as=rad_as, rad_ar=rad_ar,
                                                         rad_aa=rad_aa, rad_lr=rad_lr, rad_st=rad_st, rad_sj=rad_sj,
                                                         rad_lw=rad_lw, rad_dj=rad_dj, rad_ds=rad_ds, rad_dr=rad_dr,
                                                         rad_dp=rad_dp)

            hea_file.write(radiance_parameters)

    def write_static_shading(self):
        """
        This function writes the static shading into the header file.

        `shading 1 <descriptive_string> <file_name.dc> <file_name.ill>`

        The integer 1 represents static/no shading
        """
        dc_file = "{file_name}.dc".format(file_name=self.project_name)
        ill_file = "{file_name}.ill".format(file_name=self.project_name)
        with open(self.hea_path, "a") as hea_file:
            static_shading = "shading 1 static_system {dc_file} {ill_file}\n".format(dc_file=dc_file, ill_file=ill_file)
            hea_file.write(static_shading)

    def execute_gen_dc(self):
        """
        Calculates daylight coefficient files

        command parameters:

        -dir    calculates direct daylight coefficients only
        -dif    calculates diffuse daylight coefficients only
        -paste  pastes direct and diffuse daylight coefficient output files into a single complete file
        """
        # write the shading header
        self.write_static_shading()

        command1 = 'gen_dc "{hea_path}" -dir'.format(hea_path=self.hea_path)
        command2 = 'gen_dc "{hea_path}" -dif'.format(hea_path=self.hea_path)
        command3 = 'gen_dc "{hea_path}" -paste'.format(hea_path=self.hea_path)

        CEADaySim.run_cmd(command1)
        CEADaySim.run_cmd(command2)
        CEADaySim.run_cmd(command3)

    def execute_ds_illum(self):
        command1 = 'ds_illum "{hea_path}"'.format(hea_path=self.hea_path)
        CEADaySim.run_cmd(command1)

    def eval_ill(self):
        """
        This function reads the output file from running `ds_illum`, parses the space separated values
        and returns the values as a numpy array.

        :return: Numpy array of hourly irradiance results of sensor points
        """

        ill_path = os.path.join(self.project_path, "{file_name}.ill".format(file_name=self.project_name))
        ill_result = pd.read_csv(ill_path, delimiter=' ', header=None).iloc[:, 4:].T.values

        return ill_result


class RadSurface(object):
    """
    An object that contains all the surface information running a Radiance/Daysim simulation.

    :param str name: Name of surface
    :param OCC.TopoDS.TopoDS_Face occ_face: Polygon (OCC TopoDS_Face) of surface
    :param str material: Name of material
    """
    __slots__ = ['name', 'points', 'material']

    def __init__(self, name, occ_face, material):
        self.name = name
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
        points = ""
        for point in self.points:
            points = points + "{point_x}  {point_y}  {point_z}\n".format(point_x=point[0], point_y=point[1],
                                                                         point_z=point[2])
        surface = "{material} polygon {name}\n" \
                  "0\n" \
                  "0\n" \
                  "{num_of_points}\n" \
                  "{points}\n".format(material=self.material, name=self.name, num_of_points=num_of_points,
                                      points=points)
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
        string = "void plastic reflectance0.2\n0\n0\n5 0.5360 0.1212 0.0565 0 0"
        write_file.writelines(string + '\n')

        written_mat_name_list = []
        for geo in ageometry_table.index.values:
            mat_name = "wall_" + str(ageometry_table['type_wall'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_wall'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness
                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(
                    mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)

                write_file.writelines('\n' + string + '\n')

                written_mat_name_list.append(mat_name)

            mat_name = "win_" + str(ageometry_table['type_win'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = calc_transmissivity(ageometry_table['G_win'][geo])
                mat_value2 = mat_value1
                mat_value3 = mat_value1

                string = "void glass " + mat_name + "\n0\n0\n3 " + str(mat_value1) + " " + str(mat_value2) + " " + str(
                    mat_value3)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)

            mat_name = "roof_" + str(ageometry_table['type_roof'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = ageometry_table['r_roof'][geo]
                mat_value2 = mat_value1
                mat_value3 = mat_value1
                mat_value4 = specularity
                mat_value5 = roughness

                string = "void plastic " + mat_name + "\n0\n0\n5 " + str(mat_value1) + " " + str(
                    mat_value2) + " " + str(mat_value3) \
                         + " " + str(mat_value4) + " " + str(mat_value5)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)

        write_file.close()


def terrain_to_radiance(tin_occface_terrain):
    return [RadSurface("terrain_srf" + str(num), face, "reflectance0.2")
            for num, face in enumerate(tin_occface_terrain)]


def zone_building_to_radiance(building_geometry, building_surface_properties):
    building_name = building_geometry.name
    building_surfaces = []

    # windows
    for num, occ_face in enumerate(building_geometry.windows):
        surface_name = "win_{building_name}_{num}".format(building_name=building_name, num=num)
        material_name = "win_{material}".format(material=building_surface_properties['type_win'][building_name])
        building_surfaces.append(RadSurface(surface_name, occ_face, material_name))

    # walls
    for num, occ_face in enumerate(building_geometry.walls):
        surface_name = "wall_{building_name}_{num}".format(building_name=building_name, num=num)
        material_name = "wall_{material}".format(material=building_surface_properties['type_wall'][building_name])
        building_surfaces.append(RadSurface(surface_name, occ_face, material_name))

    # roofs
    for num, occ_face in enumerate(building_geometry.roofs):
        surface_name = "roof_{building_name}_{num}".format(building_name=building_name, num=num)
        material_name = "roof_{material}".format(material=building_surface_properties['type_roof'][building_name])
        building_surfaces.append(RadSurface(surface_name, occ_face, material_name))

    return building_surfaces


def surrounding_building_to_radiance(building_geometry):
    building_name = building_geometry.name
    building_surfaces = []

    # walls
    for num, occ_face in enumerate(building_geometry.walls):
        surface_name = "surrounding_buildings_wall_{building_name}_{num}".format(building_name=building_name, num=num)
        building_surfaces.append(RadSurface(surface_name, occ_face, "reflectance0.2"))

    # roofs
    for num, occ_face in enumerate(building_geometry.roofs):
        surface_name = "surrounding_buildings_roof_{building_name}_{num}".format(building_name=building_name, num=num)
        building_surfaces.append(RadSurface(surface_name, occ_face, "reflectance0.2"))

    return building_surfaces


def create_rad_geometry(file_path, geometry_terrain, building_surface_properties, zone_building_names,
                        surroundings_building_names, geometry_pickle_dir):
    out = []
    for terrain_surface in terrain_to_radiance(geometry_terrain):
        out.append(terrain_surface.rad())

    for building_name in zone_building_names:
        building_geometry = BuildingGeometry.load(os.path.join(geometry_pickle_dir, 'zone', building_name))
        for building_surface in zone_building_to_radiance(building_geometry, building_surface_properties):
            out.append(building_surface.rad())

    for building_name in surroundings_building_names:
        building_geometry = BuildingGeometry.load(os.path.join(geometry_pickle_dir, 'surroundings', building_name))
        for building_surface in surrounding_building_to_radiance(building_geometry):
            out.append(building_surface.rad())

    with open(file_path, "w") as rad_file:
        rad_file.write(''.join(out))
