from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import csv

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# GET SHORT NAMES OF VARIABLES IN CEA
from cea.plots.colors import COLORS_TO_RGB

NAMING_FILE_PATH = os.path.join(os.path.dirname(__file__), "naming.csv")

with open(NAMING_FILE_PATH) as naming_file:
    NAMING = {row['VARIABLE']: row['SHORT_DESCRIPTION'] for row in csv.DictReader(naming_file)}

# GET LOGO OF CEA
LOGO = [dict(
    source="https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/master/logo/CEA.png",
    xref="paper", yref="paper",
    x=0.0, y=1.15,
    sizex=0.15, sizey=0.15,
    xanchor="center", yanchor="top")]

# GET COLORS OF CEA


# GET COLORS IN ARRAY FORMAT
def get_color_array(color):
    return [int(x) for x in COLORS_TO_RGB[color].split('(')[1].split(')')[0].split(',')]


# GET COLORS OF VARIABLES IN CEA
with open(NAMING_FILE_PATH) as naming_file:
    COLOR = {row['VARIABLE']: COLORS_TO_RGB[row['COLOR']] for row in csv.DictReader(naming_file)}