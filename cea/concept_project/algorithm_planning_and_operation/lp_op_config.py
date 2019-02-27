import os
import pandas as pd

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


"""
=================
Config Variables
=================
"""

USE_ITERATOR = True

LOCATOR = os.path.dirname(__file__) + '/../../data/'

# SCENARIO = '/reference-case-WTP-reduced/WTP_MIX_m/'
# SCENARIO = '/reference-case-WTP/MIX_high_density/'
# SCENARIO = '/newcase/med/'
SCENARIO = 'IBPSA/Office/'
# SCENARIO = 'IBPSA/Retail/'
# SCENARIO = 'IBPSA/Residential/'
# SCENARIO = 'IBPSA/Retail_Office/'
# SCENARIO = 'IBPSA/Office_Residential/'
# SCENARIO = 'IBPSA/Retail_Residential/'
# SCENARIO = 'IBPSA/Office_Retail_Residential/'

# SOLVER_NAME = 'cplex'
SOLVER_NAME = 'gurobi'
THREADS = 16
TIME_LIMIT = 3600  # Interrupt solver after given time limit (set to 0 for unlimited)

PLOTTING = 0
PLOT_LINES_ON_STREETS = 1
PLOT_ALL_LINES_ON_STREETS = 0

PLOT_COLORS = [
    '#ffc130',
    # '#ebbb53',
    # '#d7b56d',
    # '#beb086',
    '#a3aa9c',
    # '#82a5b2',
    # '#519fc7',
    # '#5c92c7',
    '#6984c5',
    # '#7276c3',
    # '#7969c1',
    # '#7f58be',
    '#8447bc'
]

"""
=================
Global variables
=================
"""

# Economics data
INTEREST_RATE = 0.05  # 5% interest rate
ELECTRICITY_COST = 0.23  # SGD per kWh (not used for integrated implementation)

# Technical Data
VOLTAGE_NOMINAL = 22000  # 22 kV in SG
# APPROX_LOSS_HOURS = 5518.2
APPROX_LOSS_HOURS = 0


# Weighting Factors
ALPHA = 365.25  # related to objective_function_electricity_price
# ALPHA = 1  # related to objective_function_electricity_price
BETA = 1.0 * (10 ** 6)  # related to objective_function_set_temperature (if active, must be bigger than other terms)

LOAD_FACTOR = 10.0  # TODO: This is a hack to get nicer results
POWER_FACTOR = 0.9  # real power / apparent power

# If using iterator, select config variables for current iteration
if USE_ITERATOR:
    lp_op_config_df = pd.DataFrame.from_csv(os.path.join(LOCATOR, 'lp_op_config.csv'))
    lp_op_config_iterator_df = pd.DataFrame.from_csv(os.path.join(LOCATOR, 'lp_op_config_iterator.csv'), index_col=None)

    SCENARIO = lp_op_config_df['SCENARIO'][lp_op_config_iterator_df['current_id'][0]]
    BETA = float(lp_op_config_df['BETA'][lp_op_config_iterator_df['current_id'][0]])
    LOAD_FACTOR = float(lp_op_config_df['LOAD_FACTOR'][lp_op_config_iterator_df['current_id'][0]])
