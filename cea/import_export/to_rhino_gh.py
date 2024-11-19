"""
Export CEA files into Rhino/Grasshopper-ready format.

"""

import os
import pandas as pd
import cea.config
import time
from datetime import datetime
import cea.inputlocator

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


