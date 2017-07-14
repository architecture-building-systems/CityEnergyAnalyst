# coding=utf-8
"""
Create external .py to create .shp
"""

import os

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT ??"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


string_output = 'hahahahaah'
with open('C:/UBG_to_CEA/baseline/inputs/temporary/zone_shp.py', 'a') as f:
    f.write(string_output)
string_output = 'hahahahaah'
with open('C:/UBG_to_CEA/baseline/inputs/temporary/district_shp.py', 'a') as f:
    f.write(string_output)

#abspath= r"C:/UBG_to_CEA/baseline/inputs/temporary"
#for filename in os.listdir(os.path.dirname(os.path.abspath(__file__))):
 # base_file, ext = os.path.splitext(filename)
  #if ext == ".txt":
   # os.rename(filename, base_file + ".py")