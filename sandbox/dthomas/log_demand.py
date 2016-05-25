"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.demand
import functionlogger

if __name__ == '__main__':
    path_to_log = os.path.expandvars(r'%TEMP%\cea.demand.log.sql')
    path_to_md = os.path.expandvars(r'%TEMP%\cea.demand.log.md')

    functionlogger.connect_to(path_to_log)
    functionlogger.wrap_module(cea.demand)
    functionlogger.wrap_module(cea.demand.f)

    cea.demand.test_demand()

    with open(path_to_md) as writer:
        functionlogger.generate_output(path_to_log, writer)
