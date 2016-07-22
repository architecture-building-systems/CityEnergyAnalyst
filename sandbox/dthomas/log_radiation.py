"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.resources.radiation
import functionlogger

if __name__ == '__main__':
    path_to_log = os.path.expandvars(r'%TEMP%\cea.radiation.log.sql')
    path_to_md = os.path.expandvars(r'%TEMP%\cea.radiation.log.md')

    functionlogger.connect_to(path_to_log)
    functionlogger.wrap_module(cea.resources.radiation)

    cea.resources.radiation.test_solar_radiation()

    with open(path_to_md, 'w') as writer:
        functionlogger.generate_output(path_to_log, writer)
