# -*- coding: utf-8 -*-
"""
Constant variables for radiation_daysim
"""

# GRID FOR THE SENSORS
SEN_PARMS = {
'X_DIM': 100, # maximum so there is only one point per surface
'Y_DIM': 100, # maximum so there is only one point per surface
}
# terrain parameters
TERRAIN_PARAMS = {'e_terrain': 0.8} #reflection for the terrain.

# simulation parameters
SIMUL_PARAMS = {'n_build_in_chunk':10, # min number of buildings for multiprocessing
                'multiprocessing': False}  # limit the number if running out of memory

# geometry simplification
SIMPLIFICATION_PARAMS = {'zone_geometry': 2,     #level of simplification of the zone geometry
                         'surrounding_geometry':5,#level of simplification of the district geometry
                         'consider_windows': True, #boolean to consider or not windows in the geometry
                         'consider_floors':True} #boolean to consider or not floors in the geometry


# characteristics
