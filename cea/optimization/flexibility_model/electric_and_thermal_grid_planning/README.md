# '''CONCEPT - Connecting District Energy and Power Systems in Future Singaporean New Towns
Electric and Thermal Grid Planning:

1. Create a folder `scenario\inputs\electric_networks` and copy the `electric_line_data.csv` into that folder
   The file is present in `cea\optimization\flexibility_model\electric_and_thermal_grid_planning\electric_line_data.csv`

2. Run the `cea\optimization\flexibility_model\electric_and_thermal_grid_planning\electrical_thermal_optimization_main.py`

3. The outputs are saved in `scenario\outputs\electrical_and_thermal_network\optimization`

4. The checkpoints are saved in `scenario\outputs\electrical_and_thermal_network\optimization\master`

5. The individuals generated are saved in `scenario\outputs\electrical_and_thermal_network\optimization\slave\geneneration_number`

6. All the individuals of a generation are saved in `generation_number_individuals`. This has the columns as follows:
   
   - generation
   - individual
   - Buildings connected to the DCN or not (for all the buildings in the scenario)
   - CAPEX total
   - Opex total
   
   
7. The scripts also generate plots corresponding to the networks on streets in each `generation` folder