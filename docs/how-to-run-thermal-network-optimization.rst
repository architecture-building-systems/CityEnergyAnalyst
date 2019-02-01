:orphan:

How to Run Thermal Network Optimization in CEA.
===============================================
Independently from the CEA optimization for energy systems, it is also possible to only optimize thermal networks in districts.
Different from the CEA optimization for energy systems, this tool is design to answer more detailed questions regarding network design in a timely manner.
For example, numbers of plants in a district and the respective plant locations.


Limitations
-----------
#. This tool is still under development, currently, it is only running for :
- District Cooling Networks
- Tropical Regions (``region = SG`` in CEA v2.9)

#. To constrain the solving time, the operation of energy supply system is carried out in a simplified manner:
- One energy conversion technology to produce cooling: Vapor compression chiller powered by electricity grid.

Steps
-----
#. Run demand simulation of the case study you wish to optimize.
#. Assign optimization `parameters <#Optimization-Parameters>` and `variables <#Optimization Variables>`.
#. Make sure there are no files from previous runs in ``...outputs/data/optimization/network/`` folder.
#. Run thermal_network_optimization.py or the equivalent toolbox
#. Check results from optimization in ``...outputs/data/optimization/network/all_individuals.csv``


Optimization Parameters
-----------------------
For this optimization, the users can adjust four optimization parameters or use the default numbers.

- number of individuals (float): default 6
- number of mutation (float): default 20
- number of generations: default 20
- lucky few: default 1

These parameters are case-study dependent and need to be tuned based on the user requirement. The default values
provided are to act like a beacon in the research.

NOTE: As Genetic Algorithm, which is stochastic in nature, is being used as an optimization algorithm, the results
might not always be exact. So if there are 5 runs of the optimization, there is no guarantee that all 5 runs will
yield the same solution, but the solutions will be in close proximity. For example, if in a minimization problem, the
result in first run is 30056712, the second run might be 30045891 and the third run might be 30050025. But if the
results are normalized they are within 0.1% of the each other. An ideal way to run Genetic Algorithm is to do multiple
runs and take the best out of it and also note the worst result you might get from the optimization.

Optimization Variables
----------------------
For each optimization, the users can decide some variables related to thermal network design:

Plant location
^^^^^^^^^^^^^^
This is a default variable, meaning that the optimization algorithm will always search for the optimal plant location(s).
And it is not possible to disable this variable at the moment (v2.10).

Number of Plants
^^^^^^^^^^^^^^^^
The optimization can determine the optimal number of plants.
To enable this variable, simply set the ``min-number-of-plants`` and ``max-number-of-plants``.
The optimization algorithm will search for the optimal plant number between the min and max set by users.

Building connections
^^^^^^^^^^^^^^^^^^^^
The optimization can determine how many and which buildings in a district should be connected to the centralized network.
The costs of the buildings that are disconnected from the centralized network are also evaluated.
To enable this function, set ``optimize-building-connections = True``.

Network Layout
^^^^^^^^^^^^^^
The optimization can compare two types of network layout: branch or loop.
To enable this variable, set the ``optimize-loop-branch = True``.
The default layout is branch when ``optimize-loop-branch = False``.

Network Load
^^^^^^^^^^^^
**WARNING: This functionality is not available yet, see github issue `#1757 <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/1757>`_. **

The optimization can evaluate which loads from the space heating/cooling systems to supply by the network.
The space heating/cooling loads are divided into the loads from three units: Air Handling Units (AHU), Recirculated Air Units (RAU), and Sensible Cooling/Heating Units (SCU/SHU).
Since all three units require different supply temperatures, therefore, it will affect thermal network performance.
To enable this variable, set ``optimize-network-loads = True``


Rule-based Approximation
^^^^^^^^^^^^^^^^^^^^^^^^
It is possible to enable some pre-defined constraints to save time for optimization.
The constraints includes:
#. When there are more than one plants in a network, always place one plant close to the anchor load.
#. When setting ``optimize-building-connections = True``, always connect the building with the anchor load to the network.
#. When setting ``optimize-network-loads = True``, always connect/disconnect both AHU and RAU to/from the network at the same time.



