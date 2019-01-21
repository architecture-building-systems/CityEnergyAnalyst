"""
Create individuals

"""
from __future__ import division
import random

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def generate_main(nBuildings, config):

    if config.district_heating_network:
        heating_network_block = [0] * nBuildings
        for i in range(nBuildings):
            choice_buildCon = random.randint(0, 1)
            heating_network_block[i] = choice_buildCon
        individual = heating_network_block

    # DCN
    if config.district_cooling_network:
        cooling_network_block = [0] * nBuildings
        for j in range(nBuildings):
            choice_buildCon = random.randint(0, 1)
            cooling_network_block[j] = choice_buildCon
        individual = cooling_network_block

    return individual