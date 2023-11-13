"""
Batch processing CEA commands over all scenarios in a project.
"""

import os
import pandas as pd
import cea.config
import cea.inputlocator
from SALib.sample import saltelli

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"
