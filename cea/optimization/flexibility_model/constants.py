"""
Configuration for operation / planning and operation
"""

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


PARAMETER_SET = 'parameters_default'
TIME_STEP_TS = '01:00:00'
INTEREST_RATE = 0.05  # 5% interest rate\
VOLTAGE_NOMINAL = 22000  # 22 kV in SG
POWER_FACTOR = 0.9  # real power / apparent power
APPROX_LOSS_HOURS = 0 #or 5518.2
SOLVER_NAME = "gurobi"
LOAD_FACTOR = 10.0  # TODO: This is a hack to get nicer results
TIME_LIMIT = 3600  # Interrupt solver after given time limit (set to 0 for unlimited)
ALPHA = 1.0  # Factor for electricity costs
BETA = 1.0 * (10 ** 6)  # Factor for set temperature tracking (if active, must be bigger than other terms)