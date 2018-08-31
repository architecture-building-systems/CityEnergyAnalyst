import os
import data.datalocator

"""
=================
Config Variables
=================
"""

LOCATOR = data.datalocator.get_data_path()

SCENARIO = '\\reference-case-WTP-reduced\\WTP_MIX_m\\'
# SCENARIO = '\\reference-case-WTP\\MIX_high_density\\'

if os.name == 'nt':  # Windows
    # LOCATOR_DATA = data_path
    # LOCATOR = data_path + '\\' + scenario
    # LOCATOR = 'data/reference-case-WTP-reduced/reference-case-WTP-reduced/WTP_MIX_m/'
    # LOCATOR = 'C:/reference-case-WTP/MIX_high_density/'
    THREADS = 0
elif os.name == 'posix':  # Linux
    LOCATOR = '/home/thanhphong.huynh/WTP_MIX_m/'
    # LOCATOR = '/home/thanhphong.huynh/MIX_high_density/'
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
