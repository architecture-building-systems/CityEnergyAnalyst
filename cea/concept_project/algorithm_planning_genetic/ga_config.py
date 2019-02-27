import os

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# +++++++++++++++++++++++++++++++++++++
# Config Variables
# ++++++++++++++++++++++++++++++++++++++

PLOTTING = 0
LINE_PROBABILITY = 0.7

SCENARIO = '/reference-case-WTP-reduced/WTP_MIX_m/'
# SCENARIO = '/reference-case-WTP/MIX_high_density/'

# +++++++++++++++++++++++++++++++++++++
# Variables for Genetic Algorithm
# ++++++++++++++++++++++++++++++++++++++

POP_SIZE = 3  # Number of Individuals in Population
N_GENERATIONS = 1  # Number of Generations
IND_CROSS_RATE = 0.4  # Probability for Individual to cross
CROSS_RATE = 0.05  # Probability for each gene to change
IND_MUTATE_RATE = 0.4  # Probability for Individual to mutate
MUTATE_RATE = 0.02  # Probability for each gene to be flipped
TOURNAMENT_SIZE = 3  # The number of individuals to select for Tournament

# +++++++++++++++++++++++++++++++++++++
# Global variables - this object contains context information and is expected to be refactored away in future.
# ++++++++++++++++++++++++++++++++++++++

LOCATOR = os.path.dirname(__file__) + '/../../data/'

# Economics data
INTEREST_RATE = 0.05  # 5% interest rate
ELECTRICITY_COST = 0.23  # Euro per kWh

# Technical Data
APPROX_LOSS_HOURS = 5518.2
