Validation of CEA Looped network model
===============================

:Authors: Shanshan Hsieh, Lennart Rogenhofer
:Date: 27.02.2018

A network model is developed in CEA to provide a detailed calculation of thermal and hydraulic losses, expanded with looped networks.

Reason to develop network model in CEA
======================================

1. It is easier to convert geo-data (.shp files) into a node-edge matrix through python than to
create them in Simulink.
2. Simulink, a software used for simulating process and implementing them in MATLAB, requires a
paid license

Purpose of network model
========================

The network model is used in:

1. Plant sizing
2. Pump sizing
3. Calculate thermal loss in network
4. Calculate hydraulic loss in network

Validation Method
=================

Branched Networks
-----------------
1. Run Branched Code for Networks 1 & 2
2. Run Master Branch Code (v2.7) for Networks 1 & 2
3. Compare results

Looped and Mixed Networks
-------------------------
1. Run CEA code for networks 4 - 7
2. Matlab is run for each network to validate that Kirchhoff laws are fulfilled.
3. Select timesteps for EPANET Validation
4. Input CEA values for node mass flows, pipe lengths, pipe diameters into EPANET
5. Compare output massflows

Results
===========================================

Branched Networks
-----------------

Comparing results between the network script in CEA v2.7 and the new script updated on 27.02.2018.

+-------------------------------------------+------------+----------------+-----------------------+
| Network 1				                    | CEA v2.7	 | new script	  | Relative Difference   |
+===========================================+============+================+=======================+
| Mass flow total [kg]			            | 47343	     | 47343          | 0.00%                 |
+-------------------------------------------+------------+----------------+-----------------------+
| Heat loss total [kWh]                     | 40733	     | 40733          | 0.00%                 |
+-------------------------------------------+------------+----------------+-----------------------+
| Pressure loss total [kPa]                 | 561243     | 561243         | 0.00%	              |
+-------------------------------------------+------------+----------------+-----------------------+
| Heat supply total [kWh]	                | 2049417    | 2049417        | 0.00%		          |
+-------------------------------------------+-----------------------------------------------------+

+-------------------------------------------+------------+----------------+-----------------------+
| Network 2				                    | CEA v2.7	 | new script	  | Relative Difference   |
+===========================================+============+================+=======================+
| Mass flow total [kg]			            | 40670	     | 40654	      | 0.04%                 |
+-------------------------------------------+------------+----------------+-----------------------+
| Heat loss total [kWh]                     | 41523	     | 41540          | -0.04%                |
+-------------------------------------------+------------+----------------+-----------------------+
| Pressure loss total [kPa]                 | 669486     | 668982         | 0.08%	              |
+-------------------------------------------+------------+----------------+-----------------------+
| Heat supply total [kWh]	                | 1580685    | 1580744        | 0.00%		          |
+-------------------------------------------+-----------------------------------------------------+


Looped and Mixed Networks
-------------------------

Matlab Verification
-------------------

+-------------------------------------------+------------+----------------+
| 					                        | Kirchoff 1 | Kirchoff 2	  |
+===========================================+============+================+
| Network 4		    		                | 10^-5	     | 7.28*10^-7     |
+-------------------------------------------+------------+----------------+
| Network 5		    		                | 10^-5	     | 6.55*10^-11    |
+-------------------------------------------+------------+----------------+
| Network 6		    		                | 3.55*10^-15| 5.82*10^-11    |
+-------------------------------------------+------------+----------------+
| Network 7		    		                | 10^-5      | 5.82*10^-11    |
+-------------------------------------------+-----------------------------+


EPANET 2 Validation
---------------------

+-------------------------------------------+------------+----------------+----------------+
| 					                        | Timestep #1| Timestep #2	  |Timestep #3	   |
+===========================================+============+================+================+
| Network 4		    	             	    | 0.18%	     | 0.36%     	  | 0.20%	       |
+-------------------------------------------+------------+----------------+----------------+
| Network 5		    		                | 0.40%	     | 0.62%          | 0.41%	       |
+-------------------------------------------+------------+----------------+----------------+
| Network 6		    		                | 1.95%	     | 1.78%          | 1.62%	       |
+-------------------------------------------+------------+----------------+----------------+
| Network 7		    		                | 0.20%      | 0.11%  	      | 0.27%	       |
+-------------------------------------------+-----------------------------+----------------+



1. Branched networks are validated by comparison to the master branch. The differences between the modified and original code for branched networks is negligible. 
The source of the small deviations between results stems from the introduction of the rounding of mass 
flows to five decimals in the branch code.

2. The verification in Matlab is carried out by recalculating the Kirchoff first and second
laws. The CEA output values of edge mass 
ows are given as an input to Matlab. The maximum deviations vary between 10^-5
and 10^-11, and are thus negligible.

3. EPANET is an open source software used in a variety of applications for the calcula-
tion of 
ows in hydraulic networks. Three random time steps with different node
demands were chosen as a basis for comparison of the two networks. For these time steps, the node demands
of each node are extracted from CEA and given as an input to EPANET. The resulting mass 
flows over each
edge in EPANET are compared to the edge mass 
ows calculated by the CEA code.
High deviation between the EPANET 2 and CEA models occurs in loops of the network, at
low mass fl
ows relative to the total system mass fl
ow. This deviation most likely stems from differences in the
calculation methods for pressure losses at low mass fl
ows. To evaluate the scope of the dierences between
CEA and EPANET, the maximum absolute deviation for each time step is evaluated relative to the plant mass

flow. As the largest deviation is below 2%, the deviations are in an acceptable range.
Four primary deviations in the hydraulic network model were identified between the CEA and EPANET model. 

3a. Limits of laminar, transitional flow
CEA: 	laminar < 2300, 2300 < transitional < 5000, 5000 < turbulent
EPANET: laminar < 2000, 2000 < transitional < 4000, 4000 < turbulent
This could cause minor deviations in results for low mass flows.

3b. Transitional equations
CEA: 	0.316*Re^-0.25
EPANET:	cubic interpolation of Moody Diagram (Dunlop 1991)
In the transitional range at low mass flows this could cause minor deviations. 

3c. Losses in bends, valves, elbows
CEA:	not included
EPANET:	included
This causes deviations at all mass flows, larger differences at high mass flows. 

3d. Solving loop equations
CEA:	Hardy Cross
EPANET: Jacobian, Todini Gradient Method
This could influence the acceptable tolernace for convergence and convergence speed, but has a minimal influence on calculated solutions. 


.. figure:: network1.png

.. figure:: network2.png

.. figure:: network4.png

.. figure:: network5.png

.. figure:: network6.png

.. figure:: network7.png


Future Improvements
===================

1. Adapt EPANET 2 models to have unified pipe lengths (currently some non-standard values). 

Conclusion
==========

The looped network calculations are validated and are functioning within an acceptable margin of error of EPANET software.  
