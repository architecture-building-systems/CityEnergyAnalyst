"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.demand.demand_main
import cea.demand.occupancy_model
import cea.demand.thermal_loads
import cea.demand.ventilation_model
import cea.demand.airconditioning_model
import cea.demand.electrical_loads
import cea.demand.hotwater_loads
import cea.demand.sensible_loads
import functionlogger

if __name__ == '__main__':
    path_to_log = os.path.join(os.path.dirname(__file__), 'cea.demand.log.sql')
    path_to_md = os.path.join(os.path.dirname(__file__), 'cea.demand.log.md')

    if os.path.exists(path_to_log):
        os.remove(path_to_log)

    functionlogger.connect_to(path_to_log)
    functionlogger.wrap_module(cea.demand.demand_main, first_only=True)
    functionlogger.wrap_module(cea.demand.occupancy_model, first_only=True)
    functionlogger.wrap_module(cea.demand.thermal_loads, first_only=True)
    functionlogger.wrap_module(cea.demand.ventilation_model, first_only=True)
    functionlogger.wrap_module(cea.demand.airconditioning_model, first_only=True)
    functionlogger.wrap_module(cea.demand.electrical_loads, first_only=True)
    functionlogger.wrap_module(cea.demand.hotwater_loads, first_only=True)
    functionlogger.wrap_module(cea.demand.sensible_loads, first_only=True)

    cea.demand.demand_main.run_as_script()

    with open(path_to_md, 'w') as writer:
        functionlogger.generate_output(path_to_log, writer)
