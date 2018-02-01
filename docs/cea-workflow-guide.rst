:orphan:

How to run simulations in CEA?
==============================

In this tutorial we will be running all scripts of CEA with the exemplary case study included along the installation.
The workflow we will be pursuing is described next:


Step 1. Set up a baseline
---------------------------------------------

The first step consists on setting up a new case study. Every case study has a baseline scenario. This baseline
scenario describes the current condition of the neighborhood or district you want to analyze and improve.

For this example we will be using the case study and baseline scenario delivered with CEA. CEA holds a particular
folder structure in order to do calls between scripts and tools. So we recommend to keep it like that.
To get the example case study ready we will do the following steps:

#. Open Pycharm and the project CityEnergyAnalyst (located where you installed CEA).
#. From the project tab on the left copy and unzip the example case study to C:/. The file with the case study
   is stored in CityEnergyAnalyst>cea>examples>config_editor>reference-case-open.zip

In order to use a new case study and a baseline scenario of your own just follow the guide :doc:`new-project-guide`.

Step 2. Analyze energy potentials
-----------------------------------

After setting up the case study and baseline scenario, we will calculate the energy potentials of this scenario.
For this we will run the next tools from PyCharm:

#. Solar radiation: run this tool located in CityEnergyAnalyst>cea>resources>radiation_daysim>radiation_main.py
#. Solar collector: run this tool located in CityEnergyAnalyst>cea>technologies>solar>solar_collector.py
#. Photovoltaic: run this tool located in CityEnergyAnalyst>cea>technologies>solar>photovoltaic.py
#. Photovoltaic thermal: run this tool located in CityEnergyAnalyst>cea>technologies>solar>photovoltaic_thermal.py
#. Sewage: run this tool located in CityEnergyAnalyst>cea>technologies>sewage_heat_exchanger.py

After finished, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 3. Analyze Energy demand
-------------------------------

After calculating the energy potentials, we calculate the energy demand of the baseline scenario. For this we
will run the next tool:

#. Demand: run this tool located in CityEnergyAnalyst>cea>demand>demand_main.py

After finished, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 4. Life Cycle Analysis
----------------------------

After calculating the energy demand of the baseline scenario and energy potentials of site, we proceed to do a life cycle
analysis of emissions, primary energy and associated costs to the opeartion of buildings on site.
For this we will run the next tools:

#. Emissions and Primary Energy due to building construction: run this tool located in CityEnergyAnalyst>cea>analysis>lca>embodied.py
#. Emissions and Primary Energy due to building operation: run this tool located in CityEnergyAnalyst>cea>analysis>lca>operation.py
#. Emissions and Primary Energy due to mobility: run this tool located in CityEnergyAnalyst>cea>analysis>lca>mobility.py
#. Associated costs due to building operation: run this tool located in CityEnergyAnalyst>cea>analysis>lca>operation_costs.py

After finished, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 5 Create a new scenario
----------------------------

After running steps 1 to 4, we should have enough information to analyze what might be good opportunities or strategies
to improve the baseline scenario. Follow the next steps:

#. Copy and paste the baseline scenario and give it a new name. e.g., strategy-1
#. For the new scenario Strategy-1 proceed to edit the input databases of CEA according to the strategy you would like to pursue.
#. Repeat steps 1 to 4 for this scenario.

Step 6. Benchmark scenarios
----------------------------

Once you have one or more scenarios. This step will entail calcualting the targets of performance according to the
2000-Watt Society approach. The 2000-Watt society is a Swii metric widely used to assess the performance of energy systems
in neighborhoods and districts.

#. Benchmarking: run this tool located in CityEnergyAnalyst>cea>analysis>benchmark.py

After finished, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

Step 7. Optimization
---------------------

Right after Step 4 or Step 6, CEA offers tools to optimize the energy system of an standing scenario.
This idea will be pursued in the next steps.

#. District heating and cooling networks: run this tool located in CityEnergyAnalyst>cea>technologies>thermal_network>thermal_network_matrix.py
#. Optimization of District Energy system: run this tool located in CityEnergyAnalyst>cea>optimization>optimization_main.py

After finished, we will visualize the results by either checking the raw data files or launching :doc:`dashboard`.

