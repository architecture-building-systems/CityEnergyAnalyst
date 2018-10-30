import os
import data.datalocator

"""
=================
Config Variables
=================
"""


if os.name == 'nt':  # Windows
    THREADS = 0
elif os.name == 'posix':  # Linux
    THREADS = 8
else:
    raise ValueError('No Linux or Windows OS!')


"""
=================
Global variables
=================
"""

# Economics data
INTEREST_RATE = 0.05  # 5% interest rate
ELECTRICITY_COST = 0.23  # SGD per kWh
THERMAL_COST = 0.00000000000000000000000020

# Technical Data
V_BASE = 22.0  # in kV
S_BASE = 10.0  # in MVA
I_BASE = ((S_BASE/V_BASE) * (10**3))
APPROX_LOSS_HOURS = 3500
