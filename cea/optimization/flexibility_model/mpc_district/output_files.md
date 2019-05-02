# Outputs generated

Running `cea\optimization\flexibility_model\planning_and_operation_main.py` generates the following files:

1. `buildingname_controls.csv`: This file consists the air flow in the building, both for space heating and space cooling

2. `buildingname_outputs.csv`: This file consists the temperature of various zones in the building for all the hours in a 
year. CEA uses the temperature for the entire building, so select the minimum temperature of all the zones

3. `maximum_temperature.csv`: This file consists the maximum temperature of all the buildings using the MPC model for
all the hours of the year

4. `minimum_temperature.csv`: This file consists the minimum temperature of all the buildings using the MPC model for
all the hours of the year

5. `electric_grid_stree.pdf`: This file consists of the electric grid, building connections, substation location and the
corresponding line types used by the electrical grid

6. `set_temperature.csv`: This file has the compilation of the set point temeperatures of all buildings for 
all the hours of the year
