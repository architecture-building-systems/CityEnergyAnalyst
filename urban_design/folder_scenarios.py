# coding=utf-8
"""
Create scenario folders in Grasshopper
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT ??"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Create scenario folder tree.
# If exists, delete all the files and maintain the folder tree.
# If not, make one folder tree.

import os

# make folder "UBG_to_CEA"
dir = "C:/UBG_to_CEA/"
dir_geometry = "C:/UBG_to_CEA/baseline/inputs/building-geometry"
dir_metering = "C:/UBG_to_CEA/baseline/inputs/building-metering"
dir_properties = "C:/UBG_to_CEA/baseline/inputs/building-properties"
dir_topography = "C:/UBG_to_CEA/baseline/inputs/topography"
dir_temporary = "C:/UBG_to_CEA/baseline/inputs/temporary"

# make the scenario folder tree
if not os.path.exists(dir): # if the directory does not exist
    os.makedirs(dir) # make the directory
    os.makedirs(dir_geometry)
    os.makedirs(dir_metering)
    os.makedirs(dir_properties)
    os.makedirs(dir_topography)
    os.makedirs(dir_temporary)

else: # the directory exists
    #removes all files in a folder
    for the_file in os.listdir(dir_geometry):
        file_path_geometry = os.path.join(dir_geometry, the_file)
        try:
            if os.path.isfile(file_path_geometry):
                os.unlink(file_path_geometry) # unlink (delete) the file
        except Exception, e:
            print e

    for the_file in os.listdir(dir_metering):
        file_path_metering = os.path.join(dir_metering, the_file)
        try:
            if os.path.isfile(file_path_metering):
                os.unlink(file_path_metering) # unlink (delete) the file
        except Exception, e:
            print e

    for the_file in os.listdir(dir_properties):
        file_path_properties = os.path.join(dir_properties, the_file)
        try:
            if os.path.isfile(file_path_properties):
                os.unlink(file_path_properties) # unlink (delete) the file
        except Exception, e:
            print e

    for the_file in os.listdir(dir_topography):
        file_path_topography = os.path.join(dir_topography, the_file)
        try:
            if os.path.isfile(file_path_topography):
                os.unlink(file_path_topography) # unlink (delete) the file
        except Exception, e:
            print e

    for the_file in os.listdir(dir_temporary):
        file_path_temporary = os.path.join(dir_temporary, the_file)
        try:
            if os.path.isfile(file_path_temporary):
                os.unlink(file_path_temporary) # unlink (delete) the file
        except Exception, e:
            print e