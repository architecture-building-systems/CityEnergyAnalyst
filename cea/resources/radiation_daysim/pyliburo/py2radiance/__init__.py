#==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
#   Authors: Patrick Janssen <patrick@janssen.name>
#           Chen Kian Wee <chenkianwee@gmail.com>
# ==================================================================================================

import os
import ntpath
import subprocess
import shutil

import write_rad

class Rad(object):
    def __init__(self, base_file_path, data_folder_path):
        #paths
        self.base_file_path = base_file_path
        self.data_folder_path = data_folder_path
        self.command_file = os.path.join(data_folder_path, "command.txt")
        if os.path.exists(self.command_file):
            open(self.command_file, "w").close()
        if not os.path.isdir(data_folder_path):
            os.mkdir(data_folder_path)     
        #data
        self.surfaces = []
        self.sensor_positions = None
        self.sensor_normals = None
        #input files
        self.sensor_file_path = None
        self.rad_file_path = None
        self.sky_file_path = None
        self.oconv_file_path = None
        self.cumulative_sky_file_path = None
        self.cumulative_oconv_file_path = None
        #output files
        self.result_file = None
        self.cumulative_result_file_path = None
        #daysim stuff
        self.daysimdir_ies = None
        self.daysimdir_pts = None
        self.daysimdir_rad = None
        self.daysimdir_res = None
        self.daysimdir_tmp = None
        self.daysimdir_wea = None
        self.hea_file = None
        self.hea_filename = None
        self.sunuphrs = None
        
    def set_sensor_points(self, sensor_positions,sensor_normals):
        self.sensor_positions = sensor_positions
        self.sensor_normals = sensor_normals
        
    def set_sky(self, gensky_command, sky_colour, ground_colour):
        self.gensky_command = gensky_command
        self.sky_colour = sky_colour
        self.ground_colour = ground_colour
        
    def create_sensor_input_file(self):
        sensor_file_path = os.path.join(self.data_folder_path, "sensor_points.pts")
        sensor_file = open(sensor_file_path,  "w")
        sensor_pts_data = write_rad.sensor_file(self.sensor_positions, self.sensor_normals)
        sensor_file.write(sensor_pts_data)
        sensor_file.close()
        self.sensor_file_path = sensor_file_path
        
    def create_rad_input_file(self):
        rad_file_path = os.path.join(self.data_folder_path, "geometry.rad")
        rad_building_data = []
        rad_file = open(rad_file_path,  "w")
        for surface in self.surfaces:
            rad_data = surface.rad()
            rad_building_data.append(rad_data)
            
        for data in rad_building_data:
            rad_file.write(data)
        rad_file.close()
        self.rad_file_path = rad_file_path 

    def create_sky_input_file(self):
        sky_file_path = os.path.join(self.data_folder_path, "sky.rad")
        sky_file = open(sky_file_path,  "w")
        sky_glow = write_rad.glow("sky_glow", self.sky_colour)
        grd_glow = write_rad.glow("ground_glow", self.ground_colour)
        sky_source = write_rad.source("sky", "sky_glow", (0,0,1))
        grd_source = write_rad.source("ground", "ground_glow", (0,0,-1))
        sky_data = self.gensky_command + "\n\n" + sky_glow + "\n\n" + grd_glow + "\n\n" + sky_source + "\n\n" + grd_source
        sky_file.write(sky_data)
        sky_file.close()
        self.sky_file_path = sky_file_path

    #=============================================================================================
        #FOR GENCUMULATIVE SKY MODULE // START //
    #=============================================================================================
    def create_cumulative_sky_input_file(self, time, date, weatherfile_path, output = "irradiance"):
        #execute epw2wea 
        head,tail = ntpath.split(weatherfile_path)
        wfilename_no_extension = tail.replace(".epw", "")
        weaweatherfilename = wfilename_no_extension + "_60min.wea"
        weaweatherfile = os.path.join(self.data_folder_path, weaweatherfilename)
        command1 =  "epw2wea" + " " + weatherfile_path + " " + weaweatherfile
        proc = subprocess.Popen(command1, stdout=subprocess.PIPE)
        site_headers = proc.stdout.read()
        site_headers_list = site_headers.split("\r\n")
        latitude = site_headers_list[1].split(" ")[1]
        longtitude = site_headers_list[2].split(" ")[1]
        meridian = site_headers_list[3].split(" ")[1]
        if output == "irradiance":
            #gencumulative sky command  
            cumulative_cal_file_name = "input_cumulative_sky.cal"
            cumulative_cal_file_path = os.path.join(self.data_folder_path, cumulative_cal_file_name)
            #with -p command the output is in kwh, without -p the output is in wh
            cumulative_sky_command = "GenCumulativeSky +s1 -a " + latitude + " -o " + longtitude + " -m " + meridian + " -p -E -time " +\
                                     time +" -date " + date + " " + weatherfile_path + " > " + cumulative_cal_file_path
                                     
        elif output == "illuminance":
            #gencumulative sky command  
            cumulative_cal_file_name = "input_cumulative_sky.cal"
            cumulative_cal_file_path = os.path.join(self.data_folder_path, cumulative_cal_file_name)
            cumulative_sky_command = "GenCumulativeSky +s1 -a " + latitude + " -o " + longtitude + " -m " + meridian + " -E -time " +\
                                     time +" -date " + date + " " + weatherfile_path + " > " + cumulative_cal_file_path
                                     
        f = open(self.command_file, "a")
        f.write(cumulative_sky_command)
        f.write("\n")
        f.close()
        os.system(cumulative_sky_command)#EXECUTE
        #create the sky file using the .cal file created
        cumulative_sky_file_path = os.path.join(self.data_folder_path, "cumulative_sky.rad")
        cumulative_sky_file = open(cumulative_sky_file_path,  "w")
        csky_brightfunc = write_rad.brightfunc(cumulative_cal_file_name)
        csky_glow = write_rad.glow("sky_glow", (1,1,1))
        csky_source = write_rad.source("sky", "sky_glow", (0,0,1))
        cumulative_sky_data = "# cumulative sky file\n\n" +  csky_brightfunc + "\n\n" + csky_glow + "\n\n" + csky_source
        cumulative_sky_file.write(cumulative_sky_data)
        cumulative_sky_file.close()
        self.cumulative_sky_file_path = cumulative_sky_file_path

    def execute_cumulative_oconv(self, time, date, weatherfile_path, output = "irradiance"): 
        '''
        time format = 0 24, date format = 1 1 12 31 (all in string)
        '''
        if output == "irradiance":
            self.create_cumulative_sky_input_file(time, date, weatherfile_path)
        if output == "illuminance":
            self.create_cumulative_sky_input_file(time, date, weatherfile_path, output = "illuminance")
            
        self.create_rad_input_file() #what about interior??
        cumulative_oconv_file_path = os.path.join(self.data_folder_path, "cumulative_input.oconv")
        #make sure the dir is at where the .cal file is
        cur_dir = os.getcwd()
        os.chdir(self.data_folder_path)
        command2 = "oconv -f " + self.base_file_path + " "\
        + self.cumulative_sky_file_path + " " + self.rad_file_path +\
        " " + ">" + " " + cumulative_oconv_file_path
        f = open(self.command_file, "a")
        f.write(command2)
        f.write("\n")
        f.close()
        os.system(command2) #EXECUTE!!
        os.chdir(cur_dir)
        self.cumulative_oconv_file_path = cumulative_oconv_file_path

    def execute_cumulative_rtrace(self, ab):
        if self.cumulative_oconv_file_path == None:
            raise Exception
        #execute rtrace
        cur_dir = os.getcwd()
        os.chdir(self.data_folder_path)
        self.create_sensor_input_file()
        cumulative_result_file_path = os.path.join(self.data_folder_path, "cumulative_radmap_results.txt")
        command = "rtrace -I -h -dp 2048 -ms 0.063 -ds .2 -dt .05 -dc .75 -dr 3 -st .01 -lr 12 -lw .0005 -ab " + ab + " -ad 1000 -as 20 -ar 300 -aa 0.1   "+\
        self.cumulative_oconv_file_path + " " + " < " + self.sensor_file_path +\
        " " + " > " + " " + cumulative_result_file_path
        f = open(self.command_file, "a")
        f.write(command)
        f.write("\n")
        f.close()
        os.system(command)#EXECUTE!!
        os.chdir(cur_dir)
        self.cumulative_result_file_path = cumulative_result_file_path

    def eval_cumulative_rad(self, output = "irradiance"):
        if self.cumulative_result_file_path == None:
            raise Exception
        results = open(self.cumulative_result_file_path)
        results_read = results.read()
        lines = results_read.split("\n")
        del lines[-1]
        result_list = []    
        for line in lines:
            words  = line.split("\t")
            words.remove("")
            numbers = map(float, words)
            #IRRADIANCE RESULTS 
            irradiance = round((0.265 * numbers[0]) + (0.670 * numbers[1]) + (0.065 * numbers[2]), 1)
            if output == "irradiance":
                result_list.append(irradiance)
            if output == "illuminance":
                #ILLUMINANCE RESULTS            
                illuminance = irradiance * 179
                result_list.append(illuminance)
            
        return result_list

    #=============================================================================================
        #FOR GENCUMULATIVE SKY MODULE //END//
    #=============================================================================================
    def execute_oconv(self): 
        self.create_sky_input_file()
        self.create_rad_input_file() #what about interior??
        oconv_file_path = os.path.join(self.data_folder_path, "input.oconv")
        command = "oconv " + self.sky_file_path + " " + self.base_file_path + " "\
		+ self.rad_file_path +\
        " " + ">" + " " + oconv_file_path
        #process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #result = process.communicate()
        #print result
        f = open(self.command_file, "a")
        f.write(command)
        f.write("\n")
        f.close()
        os.system(command) #EXECUTE!!
        self.oconv_file_path = oconv_file_path 
    
    def execute_rtrace(self, dict_parm):
        if self.oconv_file_path == None:
            raise Exception
        #execute rtrace 
        self.create_sensor_input_file()
        result_file_path = os.path.join(self.data_folder_path, "results.txt")
        command = "rtrace -h -w -I+ -ab " +  dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
        " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
        " " + self.oconv_file_path + " " + " < " + self.sensor_file_path +\
        " " + " > " + " " + result_file_path
        #process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #result = process.communicate()
        #print result
        f = open(self.command_file, "a")
        f.write(command)
        f.write("\n")
        f.close()
        os.system(command)#EXECUTE!!
        self.result_file_path = result_file_path 
        
    def execute_rvu(self, vp, vd, dict_parm):
        if self.oconv_file_path == None:
            raise Exception
        #execute rvu
        operating_sys = os.name
        if operating_sys == "posix":
            command = "rvu -vp " + vp + " -vd " + vd +\
            " -ab " + dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
            " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
            " -pe " + dict_parm["exp"] + " " + self.oconv_file_path + " &"
        elif operating_sys == "nt":
            command = "rvu -vp " + vp + " -vd " + vd +\
            " -ab " + dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
            " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
            " -pe " + dict_parm["exp"] + " " + self.oconv_file_path + " &"
        f = open(self.command_file, "a")
        f.write(command)
        f.write("\n")
        f.close()
        os.system(command)#EXECUTE!!
         
    def execute_rpict(self, filename, x_resolution, y_resolution, vp, vd, dict_parm):
        if self.oconv_file_path == None:
            raise Exception("oconv file is missing")
        #execute rpict
        image_folder_path = os.path.join(self.data_folder_path,"images")
        if not os.path.isdir(image_folder_path):
            os.mkdir(image_folder_path)
        image_file_path = os.path.join(image_folder_path, filename)
        
        command1 = "rpict -x " + x_resolution + " -y " + y_resolution + " -vp " + vp +\
         " -vd " + vd +\
		 " -vh 200 -vv 100 -vta" + \
         " -ab " +  dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
         " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
         " -i " + self.oconv_file_path + " > " + image_file_path + "out_i.hdr" 
          
        command2 = "rpict -x " + x_resolution + " -y " + y_resolution + " -vp " +\
        vp + " -vd " + vd +\
		" -vh 200 -vv 100 -vta" + \
        " -ab " +  dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
        " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
        " " + self.oconv_file_path + " > " + image_file_path + "out.hdr"
          
        command3 = "pfilt -e " + dict_parm["exp"] + " " + image_file_path + "out_i.hdr" + " > " +\
		image_file_path + "out_i_filt.hdr"
        command4 = "pfilt -e " + dict_parm["exp"] + " " + image_file_path + "out.hdr" + " > " +\
		image_file_path + "out_filt.hdr"
		
        command5 = "ra_tiff " + image_file_path + "out.hdr" + " " + image_file_path + "out.tif"
        command6 = "ra_tiff " + image_file_path + "out_i.hdr" + " " + image_file_path + "out_i.tif"
        command7 = "ra_tiff " + image_file_path + "out_filt.hdr" + " " + image_file_path + "out_filt.tif"    
        command8 = "ra_tiff " + image_file_path + "out_i_filt.hdr" + " " + image_file_path + "out_i_filt.tif"
        
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.write(command2)
        f.write("\n")
        f.write(command3)
        f.write("\n")
        f.write(command4)
        f.write("\n")
        f.write(command5)
        f.write("\n")
        f.write(command6)
        f.write("\n")
        f.write(command7)
        f.write("\n")
        f.write(command8)
        f.write("\n")
        os.system(command1)#EXECUTE!!
        os.system(command2)#EXECUTE!!
        os.system(command3)#EXECUTE!!
        os.system(command4)#EXECUTE!!
        os.system(command5)#EXECUTE!!
        os.system(command6)#EXECUTE!!
        os.system(command7)#EXECUTE!!
        os.system(command8)#EXECUTE!!
        
    def execute_falsecolour(self,i_basefilename, l_basefilename, filename, range_max, 
                            range_division, illuminance = True):
        image_folder_path = os.path.join(self.data_folder_path, "images")
        if not os.path.isdir(image_folder_path):
            os.mkdir(image_folder_path)
        i_base_image_path = os.path.join(image_folder_path, i_basefilename)
        l_base_image_path = os.path.join(image_folder_path, l_basefilename)
        falsecolour_folder_path = os.path.join(image_folder_path, "falsecolour")
        if not os.path.isdir(falsecolour_folder_path):
            os.mkdir(falsecolour_folder_path)
        falsecolour_file_path = os.path.join(falsecolour_folder_path, filename)
        if illuminance == True:
            #command = "falsecolor -i " + i_base_image_path + " -p " +\
             #l_base_image_path + " -n " + range_division + " -s " + range_max +\
             #" -l lux > " + falsecolour_file_path + "_illum.hdr"

            command = "falsecolor2 -i " + i_base_image_path + " -p " +\
             l_base_image_path + " -cl -n " + range_division + " -s " + range_max +\
             " -l lux > " + falsecolour_file_path + "_illum.hdr"
            
            command2 = "ra_tiff " + falsecolour_file_path + "_illum.hdr" + " " + falsecolour_file_path + "illum.tif"

        else:
            command = "falsecolor2 -ip " + l_base_image_path +\
             " -n " + range_division + " -s " + range_max +\
             " -l cd/m2 > " + falsecolour_file_path + "_luminance.hdr"

            #command = "falsecolor2 -ip " + l_base_image_path +\
             #" -cl -n " + range_division + " -s " + range_max +\
             #" -l cd/m2 > " + falsecolour_file_path + "_luminance.hdr"
            
            command2 = "ra_tiff " + falsecolour_file_path + "_luminance.hdr" + " " + falsecolour_file_path + "luminance.tif"

            
        f = open(self.command_file, "a")
        f.write(command)
        f.write("\n")
        f.write(command2)
        f.write("\n")
        f.close()
        os.system(command)#EXECUTE!!
        os.system(command2)#EXECUTE!!

    def render(self, filename, x_resolution, y_resolution, vp, vd, dict_parm):
        if self.oconv_file_path == None:
            raise Exception("oconv file is missing")
        #execute rpict
        image_folder_path = os.path.join(self.data_folder_path,"render")
        if not os.path.isdir(image_folder_path):
            os.mkdir(image_folder_path)
        image_file_path = os.path.join(image_folder_path, filename)
          
        command1 = "rpict -x " + x_resolution + " -y " + y_resolution + " -vp " +\
         vp + " -vd " + vd +\
         " -ab " +  dict_parm["ab"] + " -aa " + dict_parm["aa"] +\
        " -ar " + dict_parm["ar"] + " -ad " + dict_parm["ad"] + " -as " + dict_parm["as"] +\
         " " + self.oconv_file_path + " > " + image_file_path + "out.hdr"
         
        command2 = "pfilt -e " + dict_parm["exp"] + " " + image_file_path + "out.hdr" + " > " +\
         image_file_path + "out_filt.hdr"

        command3 = "ra_tiff " + image_file_path + "out_filt.hdr" + " " + image_file_path + "out_filt.tif"

        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.write(command2)
        f.write("\n")
        f.write(command3)
        f.write("\n")
        f.close()
        os.system(command1)#EXECUTE!!  
        os.system(command2)#EXECUTE!!  
        os.system(command3)#EXECUTE!!   
        
    def eval_rad(self):
        if self.result_file_path == None:
            raise Exception
        results = open(self.result_file_path, "r")
        irradiance_list = []        
        illuminance_list = []
        for result in results:
            words  = result.split()
            numbers = map(float, words)
            #IRRADIANCE RESULTS 
            irradiance = round((0.265 * numbers[0]) + (0.670 * numbers[1]) + (0.065 * numbers[2]), 1)
            irradiance_list.append(irradiance)
            #ILLUMINANCE RESULTS            
            illuminance = irradiance * 179
            illuminance_list.append(illuminance)
        return irradiance_list, illuminance_list
    
#==========================================================================================================================
    #FUNCTION FOR DAYSIM
#==========================================================================================================================
    def initialise_daysim(self, daysim_dir):
        #create the directory if its not existing
        if not os.path.isdir(daysim_dir):
            os.mkdir(daysim_dir)
            
        head,tail = ntpath.split(daysim_dir)
        #create an empty .hea file
        hea_filepath = os.path.join(daysim_dir, tail + ".hea")
        hea_file = open(hea_filepath,  "w")
        #the project name will take the name of the folder
        hea_file.write("project_name" + " " + tail + "\n")
        #write the project directory
        hea_file.write("project_directory" + " " + os.path.join(daysim_dir,"")+ "\n")
        #bin directory, assumes daysim is always installed at the default c drive
        hea_file.write("bin_directory" + " " + os.path.join("c:/daysim", "bin","") + "\n")
        #write tmp directory
        hea_file.write("tmp_directory" + " " + os.path.join("tmp","") + "\n")
        #write material directory
        hea_file.write("material_directory" + " " + os.path.join("c:/daysim","") + "\n")
        #write ies directory
        hea_file.write("ies_directory" + " " + os.path.join("c:/daysim","") + "\n")
        hea_file.close()
        self.hea_file = hea_filepath
        
        #create all the subdirectory
        sub_hea_folders = ["ies","pts", "rad", "res","tmp", "wea"]
        for folder in range(len(sub_hea_folders)):
            sub_hea_folder = sub_hea_folders[folder]
            sub_hea_folders_path = os.path.join(daysim_dir,sub_hea_folder)
            if folder == 0:
                self.daysimdir_ies = sub_hea_folders_path
            if folder == 1:
                self.daysimdir_pts = sub_hea_folders_path
            if folder == 2:
                self.daysimdir_rad = sub_hea_folders_path
            if folder == 3:
                self.daysimdir_res = sub_hea_folders_path
            if folder == 4:
                self.daysimdir_tmp = sub_hea_folders_path
            if folder == 5:
                self.daysimdir_wea = sub_hea_folders_path
                
            #if the directories are not existing create them 
            if not os.path.isdir(sub_hea_folders_path):
                os.mkdir(sub_hea_folders_path)
                
            #if they are existing delete all of the files
            if os.path.isdir(sub_hea_folders_path):
                files_in_dir = os.listdir(sub_hea_folders_path)
                for filename in files_in_dir:
                    rmv_path = os.path.join(sub_hea_folders_path, filename)
                    os.remove(rmv_path)
                    
    def execute_epw2wea(self, epwweatherfile, ground_reflectance = 0.2):
        daysimdir_wea = self.daysimdir_wea
        if daysimdir_wea == None:
            raise NameError("run .initialise_daysim function before running execute_epw2wea")
        head,tail = ntpath.split(epwweatherfile)
        wfilename_no_extension = tail.replace(".epw", "")
        weaweatherfilename = wfilename_no_extension + "_60min.wea"
        weaweatherfile = os.path.join(daysimdir_wea, weaweatherfilename)
        command1 =  "epw2wea" + " " + epwweatherfile + " " + weaweatherfile
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()
        
        proc = subprocess.Popen(command1, stdout=subprocess.PIPE)
        site_headers = proc.stdout.read()
        site_headers_list = site_headers.split("\r\n")
        hea_filepath = self.hea_file
        hea_file = open(hea_filepath,  "a")
        for site_header in site_headers_list:
            if site_header:
                hea_file.write("\n" + site_header)
                
        hea_file.write("\nground_reflectance" + " " + str(ground_reflectance))
        #get the directory of the long weatherfile 
        hea_file.write("\nwea_data_file" + " " + os.path.join(head, wfilename_no_extension + "_60min.wea" ))
        hea_file.write("\ntime_step" + " " + "60")
        hea_file.write("\nwea_data_short_file" + " " + os.path.join("wea",wfilename_no_extension + "_60min.wea" ))
        hea_file.write("\nwea_data_short_file_units" + " " + "1")
        hea_file.write("\nlower_direct_threshold" + " " + "2")
        hea_file.write("\nlower_diffuse_threshold" + " " + "2")
        hea_file.close()
        #check for the sunuphours
        results = open(weaweatherfile, "r")
        result_lines = results.readlines()
        result_lines = result_lines[6:]
        sunuphrs = 0
        for result in result_lines:
            words = result.replace("\n", "")
            words1  = words.split(" ")   
            direct = float(words1[-1])
            diffuse = float(words1[-2])
            total = direct+diffuse
            if total > 0:
                sunuphrs = sunuphrs+1
                
        results.close()
        self.sunuphrs = sunuphrs
        
    def execute_radfiles2daysim(self):
        hea_filepath = self.hea_file
        head,tail = ntpath.split(hea_filepath)
        radfilename = tail.replace(".hea", "")
        radgeomfilepath = self.rad_file_path
        radmaterialfile = self.base_file_path
        if radgeomfilepath == None or radmaterialfile == None:
            raise NameError("run .create_rad function before running radfiles2daysim")
        
        hea_file = open(hea_filepath,  "a")
        hea_file.write("\nmaterial_file" + " " + os.path.join("rad", radfilename + "_material.rad"))
        hea_file.write("\ngeometry_file" + " " + os.path.join("rad", radfilename + "_geometry.rad"))
        hea_file.write("\nradiance_source_files 2," +  radgeomfilepath + "," + radmaterialfile)
        hea_file.close()
        command1 = "radfiles2daysim" + " " + hea_filepath + " " + "-g" + " " + "-m" + " " + "-d"
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()
        os.system(command1)
        
    def write_static_shading(self, hea_file):
        hea_filepath = self.hea_file
        head,tail = ntpath.split(hea_filepath)
        tail = tail.replace(".hea", "")
        self.hea_filename = tail
        dc_file = os.path.join("res",tail + ".dc")
        ill_file = os.path.join("res",tail + ".ill")
        hea_file.write("\nshading" + " " + "1" + " " + "static_system" + " " + dc_file + " " + ill_file)
    
    def write_radiance_parameters(self,rad_ab,rad_ad,rad_as,rad_ar,rad_aa,rad_lr,rad_st,rad_sj,rad_lw,rad_dj,rad_ds,rad_dr,rad_dp):
        hea_file = open(self.hea_file, "a")        
        hea_file.write("\nab" + " " + str(rad_ab))
        hea_file.write("\nad" + " " + str(rad_ad))
        hea_file.write("\nas" + " " + str(rad_as))
        hea_file.write("\nar" + " " + str(rad_ar))
        hea_file.write("\naa" + " " + str(rad_aa))
        hea_file.write("\nlr" + " " + str(rad_lr))
        hea_file.write("\nst" + " " + str(rad_st))
        hea_file.write("\nsj" + " " + str(rad_sj))
        hea_file.write("\nlw" + " " + str(rad_lw))
        hea_file.write("\ndj" + " " + str(rad_dj))
        hea_file.write("\nds" + " " + str(rad_ds))
        hea_file.write("\ndr" + " " + str(rad_dr))
        hea_file.write("\ndp" + " " + str(rad_dp))
        hea_file.close()
    
    def write_default_radiance_parameters(self): 
        rad_ab = 2
        rad_ad = 1000
        rad_as = 20
        rad_ar = 300
        rad_aa = 0.1
        rad_lr = 6
        rad_st = 0.15
        rad_sj = 1.0
        rad_lw = 0.004
        rad_dj = 0.0
        rad_ds = 0.2
        rad_dr = 2
        rad_dp = 512
        self.write_radiance_parameters(rad_ab,rad_ad,rad_as,rad_ar,rad_aa,rad_lr,
                                       rad_st,rad_sj,rad_lw,rad_dj,rad_ds,rad_dr,rad_dp)
        
    def execute_gen_dc(self, output_unit):
        hea_filepath = self.hea_file
        hea_file = open(hea_filepath,  "a")
        sensor_filepath = self.sensor_file_path
        if sensor_filepath == None:
            raise NameError("run .set_sensor_points and create_sensor_input_file function before running execute_gen_dc")
        
        daysim_pts_dir = self.daysimdir_pts
        if daysim_pts_dir == None:
            raise NameError("run .initialise_daysim function before running execute_gen_dc")
        
        #first specify the sensor pts
        head,tail = ntpath.split(sensor_filepath)
        #move the pts file to the daysim folder
        dest_filepath = os.path.join(daysim_pts_dir, tail)
        shutil.move(sensor_filepath, dest_filepath)
        #write the sensor file location into the .hea
        hea_file.write("\nsensor_file" + " " + os.path.join("pts", tail))
        #write the shading header
        self.write_static_shading(hea_file)
        #write analysis result file
        head,tail = ntpath.split(hea_filepath)
        tail = tail.replace(".hea", "")
        #hea_file.write("\nDDS_sensor_file" + " " + os.path.join("res", tail + ".dds"))
        #hea_file.write("\nDDS_file" + " " + os.path.join("res", tail + ".sen"))
        #write output unit
        nsensors = len(self.sensor_positions)
        sensor_str = ""
        if output_unit  == "w/m2":
            hea_file.write("\noutput_units" + " " + "1")
            for scnt in range(nsensors):
                #0 = lux, 2 = w/m2
                if scnt == nsensors-1:
                    sensor_str = sensor_str + "2"
                else:
                    sensor_str = sensor_str + "2 "
            
        if output_unit  == "lux":
            hea_file.write("\noutput_units" + " " + "2")
            for scnt in range(nsensors):
                #0 = lux, 2 = w/m2
                if scnt == nsensors-1:
                    sensor_str = sensor_str + "0"
                else:
                    sensor_str = sensor_str + "0 "
                    
        hea_file.write("\nsensor_file_unit " + sensor_str)
            
        hea_file.close()
        #copy the .hea file into the tmp directory
        hea_file_read = open(hea_filepath, "r")
        lines = hea_file_read.read()
        hea_file_read.close()
        tmp_directory = os.path.join(self.daysimdir_tmp, "")
        lines_modified = lines.replace(os.path.join("tmp",""), tmp_directory)
        temp_hea_filepath = os.path.join(self.daysimdir_tmp, tail+"temp.hea")
        temp_hea_file = open(temp_hea_filepath, "w")
        temp_hea_file.write(lines_modified)
        temp_hea_file.close()
        #execute gen_dc
        command1 = "gen_dc" + " " + temp_hea_filepath + " " + "-dir"
        command2 = "gen_dc" + " " + temp_hea_filepath + " " + "-dif"
        command3 = "gen_dc" + " " + temp_hea_filepath + " " + "-paste"
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.write(command2)
        f.write("\n")
        f.write(command3)
        f.write("\n")
        f.close()
        os.system(command1)
        os.system(command2)
        os.system(command3)
        
    def execute_ds_illum(self):
        hea_filepath = self.hea_file
        #execute ds_illum
        command1 = "ds_illum" + " " + hea_filepath
        f = open(self.command_file, "a")
        f.write(command1)
        f.write("\n")
        f.close()
        os.system(command1)
        
    def eval_ill(self):
        if self.hea_filename == None :
            raise Exception("run ds_illum to simulate results")
        ill_path = os.path.join(self.daysimdir_res,self.hea_filename + ".ill")
        ill_file = open(ill_path, "r")
        ill_results = ill_file.readlines()
        result_dict = {}
        for ill_result in ill_results:
            ill_result = ill_result.replace("\n","")
            ill_resultlist = ill_result.split(" ")
            date = ill_resultlist[0] + " " + ill_resultlist[1] + " " + ill_resultlist[2]
            resultlist = ill_resultlist[4:]
            resultlist_f = []
            for r in resultlist:
                resultlist_f.append(float(r))
            result_dict[date] = resultlist_f

        return result_dict
#==========================================================================================================================
#==========================================================================================================================
class Surface(object):
    def __init__(self, name, points, material):
        self.name = name
        self.points = points
        self.material = material
		
class RadSurface(Surface):
    def __init__(self, name, points, material, radgeom):
        super(RadSurface, self).__init__(name,  points, material)
        self.radgeom = radgeom
        radgeom.surfaces.append(self)
        
    def rad(self):
        name = self.name
        material = self.material
        points = self.points[:]
        return write_rad.surface(name, material, points)
#==========================================================================================================================
#==========================================================================================================================
def calculate_reflectance(r,g,b):
    reflectance = (0.2125 * r) + (0.7154 * g) + (0.0721 * b)
    return reflectance