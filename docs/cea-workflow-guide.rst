:orphan:

How to do analyses with CEA?
============================

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


Step 2. Set up a new project and baseline scenario
--------------------------------------------------

The second step consists on setting up a new project or case study. Every case study has a baseline scenario. This baseline
scenario describes the current condition of the neighborhood or district you want to analyze and improve.

CEA holds a particular folder structure in order to allow calls between scripts and tools.
In order to use a new case study and a baseline scenario of your own just follow the guide :doc:`new-project-guide`.

For this tutorial we will be using the case study and baseline scenario delivered with CEA.
To get the example case study ready we will do the following steps:

#. Open Pycharm and the project CityEnergyAnalyst (located where you installed CEA).
#. From the project tab on the left copy and unzip the example case study to C:/. The file with the case study
   is stored in CityEnergyAnalyst>cea>examples>reference-case-open.zip

Step 3. Analyze the Energy demand
----------------------------------

Once your scenario is ready, we calculate the energy demand of the baseline scenario. For this we will run the next tools:

in Pycharm:

#. Solar radiation: run this tool located in CityEnergyAnalyst > cea > resources > radiation_daysim > radiation_main.py
#. Demand: run this tool located in CityEnergyAnalyst> cea > demand > demand_main.py

in ArcGIS:

#. Solar radiation: run this tool located in CityEnergyAnalyst > Energy Potentials > Solar radiation
#. Demand: run this tool located in CityEnergyAnalyst > Demand Forecasting > Demand


A helpful tool is the data-helper found in CityEnergyAnalyst>cea>datamanagement>data_helper.py. The data helper
ensures that all necessary input databases exists and assumes default values from databases for missing values.

raw output files will be are stored in YourProject > YourScenario > outputs > data > demand

Step 4. Analyze the Energy Potentials
---------------------------------------

After calculating the solar radiation in building surfaces and energy demand, we will calculate the energy potentials of this scenario.
For this we will run the next tools:

In PyCharm:

#. Solar collector: run this tool located in CityEnergyAnalyst > cea > technologies>solar>solar_collector.py
   Run this tool once with type-scpanel = FP, and once with type-scpanel = ET.
   This will account for flat plate (FP) and evacuated tube (ET) technologies.
#. Photovoltaic: run this tool located in CityEnergyAnalyst > cea > technologies > solar > photovoltaic.py
#. Photovoltaic thermal: run this tool located in CityEnergyAnalyst > cea > technologies > solar > photovoltaic_thermal.py
#. Sewage: run this tool located in CityEnergyAnalyst > cea > resources > sewage_heat_exchanger.py
#. Lake Potential: run this tool located in CityEnergyAnalyst > cea > resources > lake_potential.py

In ArcGIS:

#. Solar collector: run this tool located in CityEnergyAnalyst > Energy Potentials > Solar collectors
   Run this tool once with type-scpanel = FP, and once with type-scpanel = ET.
   This will account for flat plate (FP) and evacuated tube (ET) technologies.
#. Photovoltaic: run this tool located in CityEnergyAnalyst > Energy Potentials > Photovoltaic panels
#. Photovoltaic thermal: run this tool located in CityEnergyAnalyst > Energy Potentials > Photovoltaic-thermal Panel
#. Sewage: run this tool located in CityEnergyAnalyst > Energy Potentials > Sewage potential
#. Lake Potential: run this tool located in CityEnergyAnalyst > Energy Potentials > Lake potential

raw output files will be are stored in YourProject > YourScenario > outputs > data > energy potentials

Step 5. Life Cycle Analysis
----------------------------

After calculating the energy demand of the baseline scenario and energy potentials of the site, we proceed to a life cycle
analysis of emissions, primary energy and associated costs of the buildings on site.

For this we will run the next tools:

In PyCharm:

#. Emissions and Primary Energy: run this tool located in CityEnergyAnalyst > cea > analysis > lca > main.py
#. Associated costs due to building operation: run this tool located in CityEnergyAnalyst > cea > costs > operation_costs.py

In ArcGIS:

#. Emissions and Primary Energy: run this tool located in CityEnergyAnalyst > Life cycle analysis > District emissions
#. Associated costs due to building operation: run this tool located in CityEnergyAnalyst > Cost analysis > Building operation costs

After the tools have finished running, we will visualize the results by either checking the raw output files or launching :doc:`dashboard`.
raw output files will be stored in YourProject > YourScenario > outputs > data > lca

Step 6. Visualize data
----------------------------

Now it is time we visualize the raw output files with CEA.

For this we will run the next tool:

In PyCharm:

#. Plots basic: run this tool located in CityEnergyAnalyst > cea > plots > plots_main.py

In PyCharm:

#. Plots basic: run this tool located in CityEnergyAnalyst > Visualization > Plots basic

Output files will be stored in YourProject > YourScenario > outputs > plots

Step 7. Create a new scenario
-----------------------------

After running steps 1 to 6, we have enough information to analyze what might be good opportunities or strategies
to improve the baseline scenario. Follow the next steps:

#. Copy and paste the baseline scenario and give it a new name. e.g., strategy-1
#. For the new scenario Strategy-1 proceed to edit the input databases of CEA according to the strategy you would like to pursue.
   The steps to edit your input databases are described in the tutorial `How to edit the input databases of CEA? <https://docs.google.com/presentation/d/16LXsu0vbllRL-in_taABuiThJ2uMP9Q05m3ORdaQrvU/edit?usp=sharing>`__.
#. Repeat steps 1 to 5 for this scenario.

Step 8. Compare scenarios
----------------------------

Once you have one or more scenarios, we will proceed to compare them one to one with a series of plots.

We will run:

In PyCharm:

#. Comparisons: run this tool located in CityEnergyAnalyst > cea > plots > comparisons > main.py

In Arcgis:

#. Comparisons: run this tool located in CityEnergyAnalyst > Visualization > Plots Comparison

After the tools have finished running, the plots will be stored in YourProject > YourScenario > outputs > plots

Step 9. Optimization
---------------------

Right after Step 3 or Step 5, CEA offers tools to optimize the energy system of a standing scenario.

This idea will be pursued in the next tools:

In Pycharm:

#. District heating and cooling networks layout: run this tool located in CityEnergyAnalyst>cea>technologies > thermal_network > network_layout > main.py
#. District heating and cooling networks thermo-hydraulic model: run this tool located in CityEnergyAnalyst > cea > technologies>thermal_network > thermal_network_matrix.py
#. Optimization of Individual Building Energy systems: run this tool located in CityEnergyAnalyst > cea > optimization > preprocessing > disconnected_building_main.py
#. Optimization of District Energy system: run this tool located in CityEnergyAnalyst > cea > optimization > optimization_main.py
#. Multi-criteria analysis: run this tool located in CityEnergyAnalyst > cea > analysis > multicriteria > main.py

In Arcgis:

#. District heating and cooling networks layout: run this tool located in CityEnergyAnalyst > Thermal Networks > Network Layout
#. District heating and cooling networks thermo-hydraulic model: run this tool located in CityEnergyAnalyst > Thermal Networks > Thermo-Hydraulic network
#. Optimization of Individual Building Energy systems: run this tool located in CityEnergyAnalyst > Optimization > Decentralized supply System
#. Optimization of District Energy system: run this tool located in CityEnergyAnalyst > Optimization > Central supply system
#. Multi-criteria analysis: run this tool located in CityEnergyAnalyst > Analysis > multicriteria analysis

The output data will be stored in YourProject > YourScenario > outputs > data > optimization

After the tools have finished running, go back to step 8. to compare scenarios.

In order to better understand the results of the optimization routine. You can visualize the results with the next tools:

In Pycharm:

#. optimization results overview: run this tool located in CityEnergyAnalyst > cea > plots > optimization > main.py
#. optimization results detailed:run this tool located in CityEnergyAnalyst > cea > plots > supply_system > main.py

In Arcgis:

#. optimization results overview: run this tool located in CityEnergyAnalyst > Visualization > Plots optimization overview
#. optimization results detailed: run this tool located in CityEnergyAnalyst > Visualization > Plots optimization detailed
