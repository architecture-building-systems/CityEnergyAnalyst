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
- number of mutation (float): default
- number of generations:
- lucky few:

Optimization Variables
----------------------
For each optimization, the users can decide some variables related to thermal network design:

Plant location
^^^^^^^^^^^^^^
This is a default variable, meaning that the optimization algorithm will always search for the optimal plant location(s).
And it is not possible to disable this variable at the moment (v2.9).

Number of Plants
^^^^^^^^^^^^^^^^
The optimization can determine the optimal number of plants.
To enable this variable, simply set the ``min-number-of-plants`` and ``max-number-of-plants``.
The optimization algorithm will search for the optimal plant number between the min and max set by users.

Building connections
^^^^^^^^^^^^^^^^^^^^
The optimization can determine how many and which buildings in a district should be connected to the centralized network.
The costs of the buildings that are disconnected from the centralized network are also evaluated.

Network Layout
^^^^^^^^^^^^^^

Network Load
^^^^^^^^^^^^

Rule-based Approximation
^^^^^^^^^^^^^^^^^^^^^^^^




