:orphan:

How to do analyses with CEA?
==============================

In this tutorial we will be running all scripts of CEA with the exemplary case study included along the installation.
The workflow we will be pursuing is described next:

Step 1. Define Target values
----------------------------

We encourage you to think about urban energy systems analysis as a series of processes required to assess the combination
of urban and energy systems design that best fit local social, economic and environmental targets. For this, it is
necessary that the we define Key Performance Metrics to determine whether an energy system is or is not suitable for a given area.
We also encourage you to define this at the beginning of every project as it will help you to build intuition about what
you would like to achieve.

In CEA 2.6 we will be able to benchmark urban scenarios against the next Key Performance Indicators (KPIs) of the `2000-Watt Society standard <http://www.2000-watt-society.ch/>`__.
You are encouraged to define from local standards the value of those KPIs

#. Costs: Total Annualized Energy Costs per unit of built area [$/m2.yr].
#. Emissions: Green House Gas emissions per unit of built area [kg CO2-eq/m2.yr]
#. End-use demand: End-use energy intensity[kWh/m2.yr].
#. Primary energy demand: Non-renewable primary energy intensity [MJ oil-eq/m2.yr].


Step 2. Set up a new project / baseline
---------------------------------------------

The second step consists on setting up a new project or case study. Every case study has a baseline scenario. This baseline
scenario describes the current condition of the neighborhood or district you want to analyze and improve.

For this example we will be using the case study and baseline scenario delivered with CEA. CEA holds a particular
folder structure in order to allow calls between scripts and tools.
To get the example case study ready we will do the following steps:

#. Open Pycharm and the project CityEnergyAnalyst (located where you installed CEA).
#. From the project tab on the left copy and unzip the example case study to C:/. The file with the case study
   is stored in CityEnergyAnalyst>cea>examples>config_editor>reference-case-open.zip

In order to use a new case study and a baseline scenario of your own just follow the guide :doc:`new-project-guide`.

Step 3. Analyze Energy demand
-------------------------------

After calculating the energy potentials, we calculate the energy demand of the baseline scenario. For this we
will run the next tools:

#. Solar radiation: run this tool located in CityEnergyAnalyst>cea>resources>radiation_daysim>radiation_main.py
#. Demand: run this tool located in CityEnergyAnalyst>cea>demand>demand_main.py

A helpful tool is the data-helper found in CityEnergyAnalyst>cea>datamanagement>data_helper.py. The data helper
ensures that all necessary input databases exists and assumes default values from databases for missing values.

After the tools have finished running, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 4. Analyze energy potentials
-----------------------------------

After setting up the case study and baseline scenario, we will calculate the energy potentials of this scenario.
For this we will run the next tools from PyCharm:

#. Solar collector: run this tool located in CityEnergyAnalyst>cea>technologies>solar>solar_collector.py
   Run this tool with the options of solar collector type = 1 and solar collector type = 2.
   This will account for flat plate and evacuated tube technologies.
#. Photovoltaic: run this tool located in CityEnergyAnalyst>cea>technologies>solar>photovoltaic.py
#. Photovoltaic thermal: run this tool located in CityEnergyAnalyst>cea>technologies>solar>photovoltaic_thermal.py
#. Sewage: run this tool located in CityEnergyAnalyst>cea>technologies>sewage_heat_exchanger.py

After the tools have finished running, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 5. Life Cycle Analysis
----------------------------

After calculating the energy demand of the baseline scenario and energy potentials of site, we proceed to a life cycle
analysis of emissions, primary energy and associated costs of the buildings on site.
For this we will run the next tools:

#. Emissions and Primary Energy due to building construction: run this tool located in CityEnergyAnalyst>cea>analysis>lca>embodied.py
#. Emissions and Primary Energy due to building operation: run this tool located in CityEnergyAnalyst>cea>analysis>lca>operation.py
#. Emissions and Primary Energy due to mobility: run this tool located in CityEnergyAnalyst>cea>analysis>lca>mobility.py
#. Associated costs due to building operation: run this tool located in CityEnergyAnalyst>cea>analysis>lca>operation_costs.py

After the tools have finished running, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 6. Create a new scenario
----------------------------

After running steps 1 to 4, we have enough information to analyze what might be good opportunities or strategies
to improve the baseline scenario. Follow the next steps:

#. Copy and paste the baseline scenario and give it a new name. e.g., strategy-1
#. For the new scenario Strategy-1 proceed to edit the input databases of CEA according to the strategy you would like to pursue.
#. Repeat steps 1 to 4 for this scenario.

Step 7. Benchmark scenarios
----------------------------

Once you have one or more scenarios, we will calculate the targets of performance according to the
2000-Watt Society approach. The 2000-Watt society is a Swiss metric widely used to assess the performance of energy systems
in neighborhoods and districts.

#. Benchmarking: run this tool located in CityEnergyAnalyst>cea>analysis>benchmark.py

After the tools have finished running, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 8. Optimization
---------------------

Right after Step 3 or Step 6, CEA offers tools to optimize the energy system of a standing scenario.
This idea will be pursued in the next steps.

#. District heating and cooling networks layout: run this tool located in CityEnergyAnalyst>cea>technologies>thermal_network>network_layout>main.py
#. District heating and cooling networks thermo-hydraulic model: run this tool located in CityEnergyAnalyst>cea>technologies>thermal_network>thermal_network_matrix.py
#. Optimization of Individual Building Energy systems: run this tool located in CityEnergyAnalyst>cea>optimization>preprocessing>disconnected_building_main.py
#. Optimization of District Energy system: run this tool located in CityEnergyAnalyst>cea>optimization>optimization_main.py

After the tools have finished running, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

