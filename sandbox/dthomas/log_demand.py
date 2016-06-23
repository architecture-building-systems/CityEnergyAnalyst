"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.demand
import functionlogger
import cea.thermal_loads
import cea.hvac_kaempf
import contributions.thermal_loads_new_ventilation.simple_window_generator
import contributions.thermal_loads_new_ventilation.ventilation

if __name__ == '__main__':
    path_to_log = os.path.expandvars(r'%TEMP%\cea.demand.log.sql')
    path_to_md = os.path.expandvars(r'%TEMP%\cea.demand.log.md')

    functionlogger.connect_to(path_to_log)
    functionlogger.wrap_module(cea.demand, first_only=True)
    functionlogger.wrap_module(cea.demand.f, first_only=True)
    functionlogger.wrap_module(cea.thermal_loads, first_only=True)
    functionlogger.wrap_module(cea.hvac_kaempf, first_only=True)
    functionlogger.wrap_module(contributions.thermal_loads_new_ventilation.simple_window_generator, first_only=True)
    functionlogger.wrap_module(contributions.thermal_loads_new_ventilation.ventilation, first_only=True)

    cea.demand.test_demand()

    with open(path_to_md, 'w') as writer:
        functionlogger.generate_output(path_to_log, writer)
