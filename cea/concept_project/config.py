"""
Configuration for operation / planning and operation
"""
import os

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

#
# Scenario settings
#

scenario_data_path = os.path.abspath(os.path.join(os.path.dirname(os.path.normpath(__file__)), '..', 'concept_project\data'))

country = 'SIN'  # If changing this, supply appropriate data in scenario files

# scenario = 'reference-case-WTP/MIX_high_density'
# scenario = 'reference-case-WTP-reduced/WTP_MIX_m'
scenario = 'IBPSA/Office'
# scenario = 'IBPSA/Office_Residential'
# scenario = 'IBPSA/Office_Retail_Residential'
# scenario = 'IBPSA/Residential'
# scenario = 'IBPSA/Retail'
# scenario = 'IBPSA/Retail_Office'
# scenario = 'IBPSA/Retail_Residential'

scenario = os.path.normpath(scenario)  # Convert to proper path name

time_start = '2005-01-01 00:00:00'
# time_end = '2005-12-31 23:30:00'
time_end = '2005-01-01 23:30:00'  # Adapt alpha when running for shorter periods
time_step_ts = '01:00:00'  # TODO: Currently only hourly time step works

#
# Model parameters
#

interest_rate = 0.05  # 5% interest rate

voltage_nominal = 22000  # 22 kV in SG
power_factor = 0.9  # real power / apparent power

# approx_loss_hours = 5518.2
approx_loss_hours = 0

# Objective function weighting factors
alpha = 1.0  # Factor for electricity costs
beta = 1.0 * (10 ** 6)  # Factor for set temperature tracking (if active, must be bigger than other terms)

load_factor = 10.0  # TODO: This is a hack to get nicer results

pricing_scheme = 'constant_prices'  # Uses constant_price for all time steps
# pricing_scheme = 'dynamic_prices'  # Loads prices from file
constant_price = 255.2  # SGD/MWh from https://www.spgroup.com.sg/what-we-do/billing

# PLEASE NOTE: Optimization will fail if set temperature doesn't respect the constraints!
# set_temperature_goal = 'set_setback_temperature'
# set_temperature_goal = 'follow_cea'
set_temperature_goal = 'constant_temperature'
constant_temperature = 25  # For 'constant_temperature'

# min_max_source == 'from building.py'
# min_max_source = 'from occupancy variations'
min_max_source = 'constants'

delta_set = 3  # For 'from occupancy variations'
delta_setback = 5  # For 'from occupancy variations'

min_constant_temperature = 20  # For 'constants'
max_constant_temperature = 25  # For 'constants'

parameter_set = 'parameters_default'  # Building definition parameter set

#
# Solver settings
#

solver_name = 'gurobi'
# solver_name = 'cplex'

threads = 30
time_limit = 3600  # Interrupt solver after given time limit (set to 0 for unlimited)

#
# Potting settings
#

plot_all_lines_on_streets = 0  # Plots all possible lines, even if not utilised
plot_colors = [
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
]  # Number of colors should match number of line types in 'electric_line_data.csv'
