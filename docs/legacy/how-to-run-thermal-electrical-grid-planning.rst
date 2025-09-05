:orphan:

How to Run Thermal & Electrical Grid Planning in CEA.
=====================================================
Independently from the CEA optimization for energy systems, this tool aims to provide the thermal network route that
yields the lowest total costs from both thermal network and electrical grid.

This tool explores the trade-offs between the costs of thermal networks and electricity grid. When buildings are connected
to the thermal network, the loads on electricity grid is decreased.

Assumptions
-----------
#. For buildings connected to the thermal networks, the electricity loads include: lighting, appliance, and hot water.
#. For buildings disconnected from the thermal networks, the electricity loads include: **cooling**, lighting, appliance, and hot water.


Prerequisites
-------------

1. Install the license of Gurobi on your computer. you can obtain one in `gurobi.com
<http://www.gurobi.com/registration/download-reg>`_ for free for academic purposes.

2. Add Gurobi package to the cea environment:
   
  * open anaconda
  * do ``conda env update``
  * do ``activate cea``
  * do ``grbgetkey xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx``
    (where xxxxxxxxxxxxxxxxxxxxxxxxxx is the key of your license.)
   
3. If you are having problems running from pycharm. get today's version 06.03.2019 or later one. This includes a fix to paths in conda.


Steps
-----
#. Run demand simulation of the case study you wish to optimize.
#. Assign optimization parameters in ``cea.config``::
      
      [electrical-thermal-optimization]
      network-type = DC (this tool is only running for District Cooling networks for the moment) 
      initialind = number of individuals at the start of the optimization (parameter for genetic algorithm)
      halloffame = number of individuals to be stored in hall of fame
      ngen = number of generations in the optimization (parameter for genetic algorithm)
      fcheckpoint = frequency for the saving of checkpoints
      maxtime = maximum allowed time in seconds, 604800 is equivalent of 7 days
      recoverycheckpoint = in case the optimization stops, it can be resumed from this checkpoint
      random-seed = random seed to make it easy to replicate the results of the scenarios
      crossoverprobability = for optimization crossover
      mutationprobability = for optimization mutation

#. Update the electricity price database with the hourly electricity prices for your cases. The database is located here: ``..\CityEnergyAnalyst\cea\databases\Region\systems\electricity_costs.xlsx``

#. Run ``electrical_thermal_optimization_main.py`` under this path ``cea\optimization\flexibility_model\electric_and_thermal_grid_planning\electrical_thermal_optimization_main.py``
#. Check results from optimization in ``...scenario\outputs\electrical_and_thermal_network\optimization``


Outputs
-------
In the evaluation of each individual, all the following aspects of thermal network and electricity grid design are saved.
The results can be found in ``...scenario\outputs\electrical_and_thermal_network\optimization``

Individuals
^^^^^^^^^^^
The individuals generated are saved in ``scenario\outputs\electrical_and_thermal_network\optimization\slave\geneneration_number``. The following information is included:

Thermal Network Design
""""""""""""""""""""""
* Buildings connected to thermal networks
* Route
* Pipe sizes
* Annualized Capital costs (CAPEX) and Operation costs (OPEX)

Electricity Grid Design
"""""""""""""""""""""""
* Size of lines
* Size of transformers
* Size of substations
* Annualized Capital costs (CAPEX) including operation and maintenance



Check Points
^^^^^^^^^^^^
When the optimization is interrupted, the intermediate results can be found in ``scenario\outputs\electrical_and_thermal_network\optimization\master``


Calculation flowchart
---------------------

.. image:: /_static/flowchart_thermal_electric_network_planning.png
    :align: center



Limitation
----------
#. The objective function inside the **Main optimization** block only includes the costs of thermal networks. And the costs of electrical grid is minimized separately inside the **Electric Grid Optimization** block. The **Main optimization** can also include the cost of the electric grid in the objective function.

#. This optimisation routine is only running for the cases with District Cooling network for the moment.
