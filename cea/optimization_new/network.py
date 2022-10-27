"""
Network Class:
defines the properties of a thermal network, including:
- Its layout (graph)
- The location of its substation
- The length of its segments
- The pipe types used for each of its segments
- The thermal losses incurred across the network
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


class Network(object):
    def __init__(self):
        self.network_layout = 'xxx'
        self.network_length = 'xxx'
        self.pipe_types = 'xxx'
        self.substation_location = 'xxx'
        self.network_losses = 'xxx'

    def start_steiner_tree_optimisation(self,):

        return self.network_layout

    def dimension_pipes(self):

        return self.pipe_types

    def calculate_losses(self):

        return self.network_losses
