"""
=====================================
Network optimization
=====================================

"""
from __future__ import division

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

class network_opt_main(object):
    """
    This class just sets-ip constants of the linear model of the distribution.
    These results are extracted form the work of Florian at the chair.
    Unfortunately his work only worked for this case study and could not be used else where
    See the paper of Fonseca et al 2015 of the city energy analyst for more info on how that procedure used to work.
    """
    def __init__(self):
        self.pipesCosts_DHN = 58310     # CHF
        self.pipesCosts_DCN = 64017     # CHF
        self.DeltaP_DHN = 77743         # Pa
        self.DeltaP_DCN = 86938        # Pa
