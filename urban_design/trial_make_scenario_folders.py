# coding=utf-8
"""
Create scenario folders in Grasshopper
"""
from __future__ import division

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT ??"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



# define the function to check if a folder exists.
# If so, delete it and make a new one.
# If not, make one.

def mkdir(path):

    import os
    import shutil

    isExists = os.path.exists(path)

    #if the folder not exists, make the folder
    if not isExists:
        os.makedirs(path)

    #if the folder exists, delete is and make a new one
    else:
        shutil.rmtree(path)
        os.makedirs(path)

if __name__ == '__main__':

    import os

    # make folder "reference-case-test"
    mkpath = "C:/reference-case-test/"
    mkdir(mkpath)

    # make the scenario folder tree
    os.makedirs("C:/reference-case-test/baseline/inputs/building-geometry")
    os.makedirs("C:/reference-case-test/baseline/inputs/building-metering")
    os.makedirs("C:/reference-case-test/baseline/inputs/building-properties")
    os.makedirs("C:/reference-case-test/baseline/inputs/topography")

