"""
This class is used to record selections of supply systems in a district in a simplified way.
The 'combination' list is made up of:
   1. the selected connectivity string for the district e.g. '0_0_1_2_1_1_2_0'
   2. the short-handle for the supply system selected for the n-th network of the district e.g. ['N1001-9', 'N1002-3']

This information is very contextual and is only meant to be recorded and interpreted within the same loop of the
connectivity-optimization.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


from cea.optimization_new.helperclasses.optimization.fitness import Fitness


class SystemCombination(object):

    def __init__(self, encoding):
        self.encoding = encoding
        self.fitness = Fitness()