"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.radiation
import functionlogger

if __name__ == '__main__':
    path_to_log = r'%TEMP%\cea.radiation.log.sql'
    path_to_md = r'%TEMP%\cea.radiation.log.md'

    functionlogger.connect_to(locator.get_temporary_file(path_to_log))
    functionlogger.wrap_module(cea.radiation)

    cea.radiation.test_solar_radiation()

    with open(os.path.expandvars(path_to_md)) as writer:
        functionlogger.generate_output(path_to_log, writer)
