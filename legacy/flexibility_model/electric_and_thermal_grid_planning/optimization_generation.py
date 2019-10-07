"""
Create individuals

"""
from __future__ import division
import random

__author__ =  "Thanh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def generate_main(nBuildings):

    network_block = [0] * nBuildings
    for i in range(nBuildings):
        choice_buildCon = random.randint(0, 1)
        network_block[i] = choice_buildCon
    individual = network_block

    return individual