"""
Radiation engine and geometry handler for CEA
"""
from __future__ import print_function
from __future__ import division

import os
import shutil
import sys
import pandas as pd
import time
from cea.utilities import epwreader
import math
from cea.resources.radiation_daysim import daysim_main, geometry_generator
import py4design.py3dmodel.fetch as fetch
import py4design.py2radiance as py2radiance
from cea.datamanagement.databases_verification import verify_input_geometry_zone, verify_input_geometry_surroundings
from geopandas import GeoDataFrame as gpdf
import cea.inputlocator
import cea.config
import subprocess

__author__ = "Paul Neitzel, Kian Wee Chen"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel", "Kian Wee Chen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def create_radiance_srf(occface, srfname, srfmat, rad):
    bface_pts = fetch.points_frm_occface(occface)
    py2radiance.RadSurface(srfname, bface_pts, srfmat, rad)


def calc_transmissivity(G_value):
    """
    Calculate window transmissivity from its transmittance using an empirical equation from Radiance.

    :param G_value: Solar energy transmittance of windows (dimensionless)
    :return: Transmissivity

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
            mat_name = "wall" + str(ageometry_table['type_wall'][geo])
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

            mat_name = "win" + str(ageometry_table['type_win'][geo])
            if mat_name not in written_mat_name_list:
                mat_value1 = calc_transmissivity(ageometry_table['G_win'][geo])
                mat_value2 = mat_value1
                mat_value3 = mat_value1

                string = "void glass " + mat_name + "\n0\n0\n3 " + str(mat_value1) + " " + str(mat_value2) + " " + str(
                    mat_value3)
                write_file.writelines('\n' + string + '\n')
                written_mat_name_list.append(mat_name)

            mat_name = "roof" + str(ageometry_table['type_roof'][geo])
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


def terrain_to_radiance(rad, tin_occface_terrain):
    for id, face in enumerate(tin_occface_terrain):
        create_radiance_srf(face, "terrain_srf" + str(id), "reflectance0.2", rad)


def buildings_to_radiance(rad, building_surface_properties, geometry_3D_zone, geometry_3D_surroundings):
    # translate buildings into radiance surface
    fcnt = 0
    for bcnt, building_surfaces in enumerate(geometry_3D_zone):
        building_name = building_surfaces['name']
        for pypolygon in building_surfaces['windows']:
            create_radiance_srf(pypolygon, "win" + str(bcnt) + str(fcnt),
                                "win" + str(building_surface_properties['type_win'][building_name]), rad)
            fcnt += 1
        for pypolygon in building_surfaces['walls']:
            create_radiance_srf(pypolygon, "wall" + str(bcnt) + str(fcnt),
                                "wall" + str(building_surface_properties['type_wall'][building_name]), rad)
            fcnt += 1
        for pypolygon in building_surfaces['roofs']:
            create_radiance_srf(pypolygon, "roof" + str(bcnt) + str(fcnt),
                                "roof" + str(building_surface_properties['type_roof'][building_name]), rad)
            fcnt += 1

    for building_surfaces in geometry_3D_surroundings:
        ## for the surrounding buildings only, walls and roofs
        id = 0
        for pypolygon in building_surfaces['walls']:
            create_radiance_srf(pypolygon, "surroundingbuildings" + str(id), "reflectance0.2", rad)
            id += 1
        for pypolygon in building_surfaces['roofs']:
            create_radiance_srf(pypolygon, "surroundingbuildings" + str(id), "reflectance0.2", rad)
            id += 1

    return


def reader_surface_properties(locator, input_shp):
    """
    This function returns a dataframe with the emissivity values of walls, roof, and windows
    of every building in the scene
    :param input_shp:
    :return:
    """

    # local variables
    architectural_properties = gpdf.from_file(input_shp).drop('geometry', axis=1)
    surface_database_windows = pd.read_excel(locator.get_database_envelope_systems(), "WINDOW")
    surface_database_roof = pd.read_excel(locator.get_database_envelope_systems(), "ROOF")
    surface_database_walls = pd.read_excel(locator.get_database_envelope_systems(), "WALL")

    # querry data
    df = architectural_properties.merge(surface_database_windows, left_on='type_win', right_on='code')
    df2 = architectural_properties.merge(surface_database_roof, left_on='type_roof', right_on='code')
    df3 = architectural_properties.merge(surface_database_walls, left_on='type_wall', right_on='code')
    fields = ['Name', 'G_win', "type_win"]
    fields2 = ['Name', 'r_roof', "type_roof"]
    fields3 = ['Name', 'r_wall', "type_wall"]
    surface_properties = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')

    return surface_properties.set_index('Name').round(decimals=2)


def radiation_singleprocessing(rad, geometry_3D_zone, locator, settings):

    weather_path = locator.get_weather_file()
    # check inconsistencies and replace by max value of weather file
    weatherfile = epwreader.epw_reader(weather_path)
    max_global = weatherfile['glohorrad_Whm2'].max()

    if settings.buildings == []:
        # get chunks of buildings to iterate
        chunks = [geometry_3D_zone[i:i + settings.n_buildings_in_chunk] for i in
                  range(0, len(geometry_3D_zone),
                        settings.n_buildings_in_chunk)]
    else:
        list_of_building_names = settings.buildings
        chunks = []
        for bldg_dict in geometry_3D_zone:
            if bldg_dict['name'] in list_of_building_names:
                chunks.append([bldg_dict])

    for chunk_n, building_dict in enumerate(chunks):
        daysim_main.isolation_daysim(chunk_n, rad, building_dict, locator, settings, max_global, weatherfile)


def check_daysim_bin_directory(path_hint):
    """
    Check for the Daysim bin directory based on ``path_hint`` and return it on success.

    If the binaries could not be found there, check in a folder `Depencencies/Daysim` of the installation - this will
    catch installations on Windows that used the official CEA installer.

    Check the RAYPATH environment variable. Return that.

    Check for ``C:\Daysim\bin`` - it might be there?

    If the binaries can't be found anywhere, raise an exception.

    :param str path_hint: The path to check first, according to the `cea.config` file.
    :return: path_hint, contains the Daysim binaries - otherwise an exception occurrs.
    """
    required_binaries = ["ds_illum", "epw2wea", "gen_dc", "oconv", "radfiles2daysim", "rtrace_dc"]
    required_libs = ["rayinit.cal", "isotrop_sky.cal"]

    def contains_binaries(path):
        """True if all the required binaries are found in path - note that binaries might have an extension"""
        try:
            found_binaries = set(bin for bin, _ in map(os.path.splitext, os.listdir(path)))
        except:
            # could not find the binaries, bogus path
            return False
        return all(bin in found_binaries for bin in required_binaries)

    def contains_libs(path):
        try:
            found_libs = set(os.listdir(path))
        except:
            # could not find the libs, bogus path
            return False
        return all(lib in found_libs for lib in required_libs)

    def contains_whitespace(path):
        """True if path contains whitespace"""
        return len(path.split()) > 1

    folders_to_check = [
        path_hint,
        os.path.join(os.path.dirname(sys.executable), "..", "Daysim"),
    ]
    # user might have a DAYSIM installation
    folders_to_check.extend(os.environ["RAYPATH"].split(";"))
    if sys.platform == "win32":
        folders_to_check.append(r"C:\Daysim\bin")
    folders_to_check = list(set(os.path.abspath(os.path.normpath(os.path.normcase(p))) for p in folders_to_check))

    for path in folders_to_check:
        if contains_binaries(path):
            # If path to binaries contains whitespace, provide a warning
            if contains_whitespace(path):
                print("ATTENTION: Daysim binaries found in '{}', but its path contains whitespaces. Consider moving the binaries to another path to use them.")
                continue

            if contains_libs(path):
                return path
            else:
                # might be C:\Daysim\bin, try adding C:\Daysim\lib
                lib_path = os.path.abspath(os.path.normpath(os.path.join(path, "..", "lib")))
                if contains_libs(lib_path):
                    return path + os.pathsep + lib_path

    raise ValueError("Could not find Daysim binaries - checked these paths: {}".format(", ".join(folders_to_check)))


class CEARad(py2radiance.Rad):
    """Overrides some methods of py4design.rad that run DAYSIM commands"""
    def __init__(self, base_file_path, data_folder_path, debug=False):
        super(CEARad, self).__init__(base_file_path, data_folder_path)
        self.debug = debug

    def run_cmd(self, cmd, cwd=None):
        # Verbose output if debug is true
        print('Running command `{}`{}'.format(cmd, '' if cwd is None else ' in `{}`'.format(cwd)))
        if self.debug:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)
            while p.poll() is None:
                line = p.stdout.readline()
                if len(line.strip()):
                    print(line)
            print(p.stdout.read())
            print('`{}` completed'.format(cmd))
        else:
            # Stops script if commands fail (i.e non-zero exit code)
            subprocess.check_call(cmd, cwd=cwd, stderr=subprocess.STDOUT, env=os.environ)

    def execute_epw2wea(self, epwweatherfile, ground_reflectance=0.2):
        daysimdir_wea = self.daysimdir_wea
        if daysimdir_wea == None:
            raise NameError("run .initialise_daysim function before running execute_epw2wea")
        head, tail = os.path.split(epwweatherfile)
        wfilename_no_extension = tail.replace(".epw", "")
        weaweatherfilename = wfilename_no_extension + "_60min.wea"
        weaweatherfile = os.path.join(daysimdir_wea, weaweatherfilename)
        command1 = 'epw2wea "{}" "{}"'.format(epwweatherfile, weaweatherfile)
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()

        # TODO: Might not need `shell`. Check on a Windows machine that has a space in the username
        proc = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
        site_headers = proc.stdout.read()
        site_headers_list = site_headers.split("\r\n")
        hea_filepath = self.hea_file
        hea_file = open(hea_filepath, "a")
        for site_header in site_headers_list:
            if site_header:
                hea_file.write("\n" + site_header)

        hea_file.write("\nground_reflectance" + " " + str(ground_reflectance))
        # get the directory of the long weatherfile
        hea_file.write("\nwea_data_file" + " " + os.path.join(head, wfilename_no_extension + "_60min.wea"))
        hea_file.write("\ntime_step" + " " + "60")
        hea_file.write("\nwea_data_short_file" + " " + os.path.join("wea", wfilename_no_extension + "_60min.wea"))
        hea_file.write("\nwea_data_short_file_units" + " " + "1")
        hea_file.write("\nlower_direct_threshold" + " " + "2")
        hea_file.write("\nlower_diffuse_threshold" + " " + "2")
        hea_file.close()
        # check for the sunuphours
        results = open(weaweatherfile, "r")
        result_lines = results.readlines()
        result_lines = result_lines[6:]
        sunuphrs = 0
        for result in result_lines:
            words = result.replace("\n", "")
            words1 = words.split(" ")
            direct = float(words1[-1])
            diffuse = float(words1[-2])
            total = direct + diffuse
            if total > 0:
                sunuphrs = sunuphrs + 1

        results.close()
        self.sunuphrs = sunuphrs

    def execute_radfiles2daysim(self):
        hea_filepath = self.hea_file
        head, tail = os.path.split(hea_filepath)
        radfilename = tail.replace(".hea", "")
        radgeomfilepath = self.rad_file_path
        radmaterialfile = self.base_file_path
        if radgeomfilepath == None or radmaterialfile == None:
            raise NameError("run .create_rad function before running radfiles2daysim")

        hea_file = open(hea_filepath, "a")
        hea_file.write("\nmaterial_file" + " " + os.path.join("rad", radfilename + "_material.rad"))
        hea_file.write("\ngeometry_file" + " " + os.path.join("rad", radfilename + "_geometry.rad"))
        hea_file.write("\nradiance_source_files 2," + radgeomfilepath + "," + radmaterialfile)
        hea_file.close()
        command1 = 'radfiles2daysim "{}" -g -m -d'.format(hea_filepath)
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()
        self.run_cmd(command1)

    def execute_gen_dc(self, output_unit):
        hea_filepath = self.hea_file
        hea_file = open(hea_filepath, "a")
        sensor_filepath = self.sensor_file_path
        if sensor_filepath == None:
            raise NameError(
                "run .set_sensor_points and create_sensor_input_file function before running execute_gen_dc")

        daysim_pts_dir = self.daysimdir_pts
        if daysim_pts_dir == None:
            raise NameError("run .initialise_daysim function before running execute_gen_dc")

        # first specify the sensor pts
        sensor_filename = os.path.basename(sensor_filepath)
        # move the pts file to the daysim folder
        dest_filepath = os.path.join(daysim_pts_dir, sensor_filename)
        shutil.move(sensor_filepath, dest_filepath)
        # write the sensor file location into the .hea
        hea_file.write("\nsensor_file {rel_sensor_filename}".format(
            rel_sensor_filename=os.path.join("pts", sensor_filename)))
        # write the shading header
        self.write_static_shading(hea_file)
        # write analysis result file
        nsensors = len(self.sensor_positions)
        sensor_str = ""
        if output_unit == "w/m2":
            hea_file.write("\noutput_units" + " " + "1")
            for scnt in range(nsensors):
                # 0 = lux, 2 = w/m2
                if scnt == nsensors - 1:
                    sensor_str = sensor_str + "2"
                else:
                    sensor_str = sensor_str + "2 "

        if output_unit == "lux":
            hea_file.write("\noutput_units" + " " + "2")
            for scnt in range(nsensors):
                # 0 = lux, 2 = w/m2
                if scnt == nsensors - 1:
                    sensor_str = sensor_str + "0"
                else:
                    sensor_str = sensor_str + "0 "

        hea_file.write("\nsensor_file_unit " + sensor_str)

        hea_file.close()
        # copy the .hea file into the tmp directory
        with open(hea_filepath, "r") as hea_file_read:
            lines = hea_file_read.readlines()

        tmp_directory = os.path.join(self.daysimdir_tmp, "")

        # update path to tmp_directory in temp_hea_file
        lines_modified = []
        for line in lines:
            if line.startswith('tmp_directory'):
                lines_modified.append('tmp_directory {}\n'.format(tmp_directory))
            else:
                lines_modified.append(line)

        hea_basename = os.path.splitext(os.path.basename(hea_filepath))[0]
        temp_hea_filepath = os.path.join(self.daysimdir_tmp, hea_basename + "temp.hea")

        with open(temp_hea_filepath, "w") as temp_hea_file:
            temp_hea_file.write('\n'.join(lines_modified))

        # execute gen_dc
        command1 = 'gen_dc "{}" -dir'.format(temp_hea_filepath)
        command2 = 'gen_dc "{}" -dif'.format(temp_hea_filepath)
        command3 = 'gen_dc "{}" -paste'.format(temp_hea_filepath)
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.write(command2)
        f.write("\n")
        f.write(command3)
        f.write("\n")
        f.close()
        self.run_cmd(command1)
        self.run_cmd(command2)
        self.run_cmd(command3)

    def execute_ds_illum(self):
        hea_filepath = self.hea_file
        head, tail = os.path.split(hea_filepath)

        # execute ds_illum
        command1 = 'ds_illum "{}"'.format(hea_filepath)
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()
        self.run_cmd(command1)

def main(config):
    """
    This function makes the calculation of solar insolation in X sensor points for every building in the zone
    of interest. The number of sensor points depends on the size of the grid selected in the config file and
    are generated automatically.

    :param config: Configuration object with the settings (genera and radiation)
    :type config: cea.config.Configuartion
    :return:
    """

    #  reference case need to be provided here
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    #  the selected buildings are the ones for which the individual radiation script is run for
    #  this is only activated when in default.config, run_all_buildings is set as 'False'

    # BUGFIX for #2447 (make sure the Daysim binaries are there before starting the simulation)
    config.radiation.daysim_bin_directory = check_daysim_bin_directory(config.radiation.daysim_bin_directory)

    # BUGFIX for PyCharm: the PATH variable might not include the daysim-bin-directory, so we add it here
    os.environ["PATH"] = config.radiation.daysim_bin_directory + os.pathsep + os.environ["PATH"]
    os.environ["RAYPATH"] = config.radiation.daysim_bin_directory
    if not "PROJ_LIB" in os.environ:
        os.environ["PROJ_LIB"] = os.path.join(os.path.dirname(sys.executable), "Library", "share")
    if not "GDAL_DATA" in os.environ:
        os.environ["GDAL_DATA"] = os.path.join(os.path.dirname(sys.executable), "Library", "share", "gdal")

    print("verifying geometry files")
    print(locator.get_zone_geometry())
    verify_input_geometry_zone(gpdf.from_file(locator.get_zone_geometry()))
    verify_input_geometry_surroundings(gpdf.from_file(locator.get_surroundings_geometry()))

    # import material properties of buildings
    print("getting geometry materials")
    building_surface_properties = reader_surface_properties(locator=locator,
                                                            input_shp=locator.get_building_architecture())
    building_surface_properties.to_csv(locator.get_radiation_materials())
    print("creating 3D geometry and surfaces")
    # create geometrical faces of terrain and buildingsL
    elevation, geometry_terrain, geometry_3D_zone, geometry_3D_surroundings = geometry_generator.geometry_main(locator,
                                                                                                               config)

    print("Sending the scene: geometry and materials to daysim")
    # send materials
    daysim_mat = locator.get_temporary_file('default_materials.rad')
    rad = CEARad(daysim_mat, locator.get_temporary_folder(), debug=config.debug)
    print("\tradiation_main: rad.base_file_path: {}".format(rad.base_file_path))
    print("\tradiation_main: rad.data_folder_path: {}".format(rad.data_folder_path))
    print("\tradiation_main: rad.command_file: {}".format(rad.command_file))
    add_rad_mat(daysim_mat, building_surface_properties)
    # send terrain
    terrain_to_radiance(rad, geometry_terrain)
    # send buildings
    buildings_to_radiance(rad, building_surface_properties, geometry_3D_zone, geometry_3D_surroundings)
    # create scene out of all this
    rad.create_rad_input_file()
    print("\tradiation_main: rad.rad_file_path: {}".format(rad.rad_file_path))

    time1 = time.time()
    radiation_singleprocessing(rad, geometry_3D_zone, locator, config.radiation)

    print("Daysim simulation finished in %.2f mins" % ((time.time() - time1) / 60.0))


if __name__ == '__main__':
    main(cea.config.Configuration())
