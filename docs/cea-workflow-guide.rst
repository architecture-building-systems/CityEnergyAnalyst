:orphan:

How to do analyses with CEA?
============================

In this tutorial we will be running all scripts of CEA with the exemplary case study included along the installation.

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


Step 1. Set-up your case study
------------------------------

The first step consists on setting-up a case study with CEA. This includes creating a new project and a baseline scenario of your area of analysis.

Follow the next steps:

#. Prepare a shape-file of your zone of analysis OR download one from our `examples <https://github.com/architecture-building-systems/CityEnergyAnalyst/tree/master/cea/examples>`__.
#. Open CEA from your Desktop.
#. Go to tools / create new project.
#. Indicate where your zone of analysis is.
#. Indicate folder where to save the new project
#. Run the tool.

.. note:: The shapefile of your zone of analysis must comply with the structure mentioned
          in the `Input databases of CEA <https://docs.google.com/presentation/d/14cgSAhNGnjTDLx_rco9mWU9FFLk0s50FBd_ud9AK7pU/edit#slide=id.g1d85a4d9be_0_0>`__.


Step 2. Edit the occupancy and age of buildings
-----------------------------------------------

Attributes regarding occupancy and age of buildings is a minimum requirement for CEA to gather databases about buildings, technology and economy.

Follow the next steps:

#. Go to the folder where you have saved YourProject
#. Open CEA from your Desktop.
#. Go to inputs/Occupancy and edit it accordingly to your case study and Save the changes.
#. Go to inputs/Occupancy and edit it accordingly to your case study and Save the changes.

The occupancy and Age files are located in YourProject/YourScenario/inputs/building/properties/ in case you would like to edit these files with a .dBf. reader

.. note:: It is important to maintain the column names of these two files for CEA to work.
          in case you need to check, here is this tutorial `Input databases of CEA <https://docs.google.com/presentation/d/14cgSAhNGnjTDLx_rco9mWU9FFLk0s50FBd_ud9AK7pU/edit#slide=id.g1d85a4d9be_0_0>`__.


Step 3. Gather databases
------------------------

Urban energy systems simulation requires a great deal of data. Use the next tools to gather this data automatically.

Follow the next steps:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to tools/Data Management/Data Helper tool and run this tool. `Check this blog for some help on this <https://cityenergyanalyst.com/blog/2019/4/5/speedinguppart1>`__.
#. Go to tools/Data Management/District Helper tool and run this tool. `Check this blog for some help on this <https://cityenergyanalyst.com/blog/2019/4/5/speedinguppart2>`__.
#. Go to tools/Data Management/Terrain Helper tool and run this tool. `Check this blog for some help on this <https://cityenergyanalyst.com/blog/2019/4/5/speedinguppart2>`__.
#. Go to tools/Data Management/Streets Helper tool and run this tool. `Check this blog for some help on this <https://cityenergyanalyst.com/blog/2019/4/5/speedinguppart3>`__.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tools General, Data Helper, District Helper, Terrain Helper and Streets Helper
#. Go to CityEnergyAnalyst/cea/datamanagement/data_helper.py and run.
#. Go to CityEnergyAnalyst/cea/datamanagement/district_geometry_helper.py and run.
#. Go to CityEnergyAnalyst/cea/datamanagement/terrain_helper.py and run.
#. Go to CityEnergyAnalyst/cea/datamanagement/streets_helper.py and run.


Step 4. Solar radiation calculation
------------------------------------

Once your scenario and databases are ready, we calculate the solar radiation of the baseline scenario. For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to tools/Resources/Solar Radiation and run this tool.
#. Visualize results in the dashboard.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tools solar-radiation
#. Go to CityEnergyAnalyst/cea/resources/radiation_daysim/radiation_main.py  and run.

Raw output files will be are stored in YourProject/YourScenario/outputs/data/solar-radiation

Step 5. Energy demand calculation
------------------------------------

Once your scenario is ready, we calculate the energy demand of the baseline scenario. For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to tools/Demand/Demand and run this tool.
#. Visualize results in the dashboard.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tool demand
#. Go to CityEnergyAnalyst/cea/demand/demand_main.py and run.

Raw output files will be are stored in YourProject/YourScenario/outputs/data/demand


Step 6. Renewable energy potential calculation
-----------------------------------------------

After calculating the solar radiation in building surfaces and the energy demand of buildings, we will calculate the energy potentials of this scenario.
For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to tools/Energy Potentials/Solar collectors and run this tool.
   Run this tool once with type-scpanel = FP, and once with type-scpanel = ET.
   This will account for flat plate (FP) and evacuated tube (ET) technologies.
#. Go to tools/Energy Potentials/Photovoltaic panels and run this tool.
#. Go to tools/Energy Potentials/Photovoltaic-thermal Panel and run this tool.
#. Go to tools/Energy Potentials/Sewage potential.
#. Go to tools/Energy Potentials/Lake potential.
#. Visualize results in the dashboard.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tool solar
#. Go to CityEnergyAnalyst/cea/technologies>solar>solar_collector.py and run.
   Run this tool once with type-scpanel = FP, and once with type-scpanel = ET.
   This will account for flat plate (FP) and evacuated tube (ET) technologies.
#. Go to CityEnergyAnalyst/cea/technologies/solar/photovoltaic.py
#. Go to CityEnergyAnalyst/cea/technologies/solar/photovoltaic_thermal.py
#. Go to CityEnergyAnalyst/cea/resources/sewage_heat_exchanger.py
#. Go to CityEnergyAnalyst/cea/resources/lake_potential.py

Raw output files will be are stored in YourProject/YourScenario/outputs/data/energy potentials


Step 7. Thermal networks analysis
--------------------------------------------------

Either in parallel or after step 6, we can use the tools of CEA to determine close-to optimal thermal networks connecting 2 or more buildings.
For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tool network-layout and thermal-network
#. Go to CityEnergyAnalyst/Thermal Networks/Network Layout and run this tool.
#. Go to CityEnergyAnalyst/Thermal Networks/Thermo-Hydraulic network and run this tool.
#. Visualize results in the dashboard.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters for the tool network-layout and thermal-network
#. Go to CityEnergyAnalyst/cea/technologies/thermal_network/network_layout/main.py
#. Go to CityEnergyAnalyst/cea/technologies/thermal_network/thermal_network.py

Raw output files will be are stored in YourProject/YourScenario/inputs/networks/energy potentials


Step 8. Life Cycle Analysis (Operation costs and LCA emissions)
---------------------------------------------------------------

After calculating the energy demand of the baseline scenario and energy potentials of the site, we proceed to a life cycle
analysis of emissions, primary energy and associated costs of the buildings on site.

For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to tools/Life cycle analysis/District emissions and run this tool.
#. Go to tools/Cost analysis/Building operation costs and run this tool.
#. Visualize results in the dashboard.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters of life-cycle tools
#. Go to CityEnergyAnalyst/cea/analysis/lca/main.py and run this tool.
#. Go to CityEnergyAnalyst/cea/costs/operation_costs.py and run this tool.

Raw output files will be stored in YourProject/YourScenario/outputs/data/lca

Step 8. Create a new scenario
-----------------------------

After running steps 1 to 7, we have enough information to analyze what might be good opportunities or strategies
to improve the baseline scenario. Follow the next steps:

#. Copy and paste the baseline scenario and give it a new name. e.g., strategy-1
#. For the new scenario Strategy-1 proceed to edit the input databases of CEA according to the strategy you would like to pursue.
   The steps to edit your input databases are described in the tutorial `How to edit the input databases of CEA? <https://docs.google.com/presentation/d/16LXsu0vbllRL-in_taABuiThJ2uMP9Q05m3ORdaQrvU/edit?usp=sharing>`__.
#. Repeat steps 1 to 7 for this scenario.

Step 9. Compare scenarios
----------------------------

Once you have one or more scenarios, you can compare scenarios with the plots included in the CEA dashboard

Step 10. Optimization and multi-criteria analysis
--------------------------------------------------

Right after Step 6, CEA offers tools to optimize the energy system of an urban scenario.

For this we will run the next tools:

With the CEA dashboard:

#. Open CEA from your Desktop.
#. Go to CityEnergyAnalyst/Optimization/Decentralized supply System and run this tool.
#. Go to CityEnergyAnalyst/Optimization/Central supply system and run this tool.
#. Go to  CityEnergyAnalyst/Analysis/multicriteria analysis and run this tool.

Alternatively with Pycharm:

#. Open PyCharm from your Desktop.
#. Go to the cea.config file stored in %userprofile% and edit the parameters related to optimization and multicriteria
#. Go to CityEnergyAnalyst/cea/optimization/preprocessing/disconnected_building_main.py and run it.
#. Go to CityEnergyAnalyst/cea/optimization/optimization_main.py and run it.
#. Go to CityEnergyAnalyst/cea/analysis/multicriteria/main.py and run it.

Raw data will be stored in YourProject/YourScenario/outputs/data/optimization

After the tools have finished running, go back to step 9. to compare scenarios.

