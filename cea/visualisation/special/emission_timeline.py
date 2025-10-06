# -*- coding: utf-8 -*-




import math
import os
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go
from plotly.offline import plot

import cea.config
import cea.plots.demand
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB
from cea.import_export.result_summary import filter_buildings

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"
