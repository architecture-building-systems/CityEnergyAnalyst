import os

"""
=================
Config Variables
=================
"""

LOCATOR = os.path.dirname(__file__) + '/../../data/'

SCENARIO = '/reference-case-WTP-reduced/WTP_MIX_m/'
# SCENARIO = '/reference-case-WTP/MIX_high_density/'
# SCENARIO = '/newcase/med/'

if os.name == 'nt':  # Windows
    THREADS = 0
elif os.name == 'posix':  # Linux
    THREADS = 24

PLOTTING = 0
PLOT_LINES_ON_STREETS = 1
PLOT_ALL_LINES_ON_STREETS = 1

"""
=================
Global variables
=================
"""

# Economics data
INTEREST_RATE = 0.05  # 5% interest rate
ELECTRICITY_COST = 0.23  # SGD per kWh

# Technical Data
V_BASE = 20.0  # in kV
S_BASE = 10.0  # in GW
I_BASE = ((S_BASE/V_BASE) * (10**3))
APPROX_LOSS_HOURS = 5518.2
