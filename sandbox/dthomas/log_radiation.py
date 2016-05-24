"""log_radiation.py
run the radiation.py script with the functionlogger.
"""
import os

import cea.inputlocator
import cea.globalvar
import cea.radiation
import functionlogger
import inspect

if __name__ == '__main__':
    locator = cea.inputlocator.InputLocator(r'C:\reference-case\baseline')
    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))
    gv = cea.globalvar.GlobalVariables()

    functionlogger.connect_to(locator.get_temporary_file('cea.radiation.log.sql'))

    # wrap all the functions in radiation.py with the logger
    for member in dir(cea.radiation):
        if inspect.isfunction(getattr(cea.radiation, member)):
            setattr(cea.radiation, member, functionlogger.log_args(getattr(cea.radiation, member)))


    cea.radiation.solar_radiation_vertical(locator=locator, path_arcgis_db=path_default_arcgis_db,
                             latitude=46.95240555555556, longitude=7.439583333333333, timezone=1, year=2014, gv=gv)
