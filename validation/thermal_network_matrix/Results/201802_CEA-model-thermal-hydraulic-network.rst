Validation of CEA network model
===============================

:Author: Shanshan Hsieh, Sreepathi Bhargava Krishna, Lennart Rogenhofer
:Date: 01.02.2018

A network model is developed in CEA to provide a detailed calculation of thermal and hydraulic losses.

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

1. Compare the simulated results from CEA network model against the identical thermal network
model using Simulink Thermal Liquid Library
2. The networks in CEA and Simulink have identical layout, demands at substations (flow rate),
pipe properties and plant supply temperatures and the thermal and hydraulic losses are simulated
in both models
3. Three test cases are developed in both CEA and Simulink

+------------------------------------------------------------------+
| Parameters input to Simulink                                     |
+======================================+===========================+
| Pipe insulation thermal conductivity | 0.023 [W/mK]              |
+--------------------------------------+---------------------------+
| Soil thermal conductivity            | 1.6 [W/mK]                |
+--------------------------------------+---------------------------+
| Pipe roughness                       | 2E-5 [m] (steel pipe)     |
+--------------------------------------+---------------------------+
| Pipe length                          | 125 [m]                   |
+--------------------------------------+---------------------------+
| Pipe diameter                        | From CEA network [m]      |
+--------------------------------------+---------------------------+
| Pipe insulation thickness            | From CEA network          |
+--------------------------------------+---------------------------+
| Plant supply temperatures            | Hourly data from CEA [C]  |
+--------------------------------------+---------------------------+
| Substation flow rate                 | Hourly data from CEA      |
|                                      | demand [kg/s]             |
+--------------------------------------+---------------------------+


+--------------------------------------------------+
| Outputs from Simulink                            |
+==================================================+
| Flow rate in each pipe on the supply side [kg/s] |
+--------------------------------------------------+
| Total pressure losses on the supply side [Pa]    |
+--------------------------------------------------+
| Total heat loss on the supply side [kW]          |
+--------------------------------------------------+


Comparison of Results from CEA and Simulink
===========================================

Network 1:

+-------------------------------------------+------------+----------------+-----------------------+
| Parameter                                 | CEA Model  | Simulink Model | Notes                 |
+===========================================+============+================+=======================+
| Annual heat supplied by the heating plant | 2040 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     | 1990 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                |  2.65 MWh  |                | Max plant heat        |
|                                           |            |                | requirement (t = 393) |
+-------------------------------------------+------------+----------------+-----------------------+
| Max thermal loss (t = 393)                | 16.2 kWh   | 15.3 kWh       | difference = 6.1%     |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss supply                | 33.57 MWh/a| 31.42 MWh/a    | difference = 6.8%     |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss supply (t = 417)        |  559 kPa   | 563 kPa        | difference = - 0.7%   |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss supply               |  274.94 MPa|  275.72 MPa    | difference = -0.3%    |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss    (losses/heat supplied)  | 1.65%      |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 6.7% higher|                | 			  |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 4% lower   |                | 		  	  |
+-------------------------------------------+------------+----------------+-----------------------+
| # of Hours when dP% > 10%		    | 293, all at low pressure losses		          |
+-------------------------------------------+-----------------------------------------------------+

Network 3:

+-------------------------------------------+------------+----------------+-----------------------+
| Parameter                                 | CEA Model  | Simulink Model | Notes                 |
+===========================================+============+================+=======================+
| Annual heat supplied by the heating plant |  1770 MWh/a|                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     |  1730 MWh/a|                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                |  2.27 MWh  |                | Max plant heat        |
|                                           |            |                | requirement (t = 393) |
+-------------------------------------------+------------+----------------+-----------------------+
| Max thermal loss (t = 8625)               | 13.54 kWh  |  13.7 kWh      | difference = -1.19%   |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss                       | 27.47 MWh/a| 28.49 MWh/a    | difference = -3.58 %  |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss (t = 421)               |  546 kPa   | 546 kPa        | difference = 0.01%    |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss                      |  237 MPa   | 237 MPa        | difference = 0.26%    |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss    (losses/heat supplied)  |  1.55 %    |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 13.2 % lower, large deviations for low massflows [1]|
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 1.77 % lower   					  |
+-------------------------------------------+------------+----------------+-----------------------+
| # of Hours when dP% > 10%		    | 57, all at low pressure loss                        |
+-------------------------------------------+-----------------------------------------------------+

[1] Source of losses is assumed in the simulink model, as here heat losses appear in pipes connecting nodes with 0 node demand. 
Occurs at values with small total loss, so despite large % deviation, only small deviation of absolute values. 


1. The plant capacity is sized at the maximum heat requirement, which include the heating demand
from buildings and the thermal loss. At the time step with the maximum heating demand, the difference
in thermal loss between CEA and Simulink is 6.1% or 1.19% for Networks 1 and 3 respectively. Relative to the total plant size
(determined at the timsestep of maximum demand) this is equivalent to less than 0.01% of the total plant capacity.

2. The differences in total thermal losses between CEA and Simulink over 8760 hours is around 1 MWh,
which corresponds to 4% of annual heat loss. Since the total thermal losses over 8760 hours at the
supply network accounts for 1.55% of the total heat supplied by the heating plant, the 4% difference
in the thermal loss calculation is in acceptable range.

3. There are several instances where the hydraulic losses deviate more than 10% between the results from CEA and Simulink. 
This phenomeno occurs at times of low pressure losses and are most likely due to deviations in the methods used to model laminar
and transitional flows.

4. Updating the thermal network script to include laminar and transitional pressure losses and convection heat transfer resistance has
slightly increased the total accuracy of the pressure and heat losses calculated by CEA compared to the simulink model. 

.. figure:: network1.png


.. figure:: network3.png


Multiple Plants
===================

Network 2:

+-------------------------------------------+------------+----------------+-----------------------+
| Parameter                                 | CEA Model  | Simulink Model | Notes                 |
+===========================================+============+================+=======================+
| Annual heat supplied by the heating plant | 1571 MWh/a |                | two plants            |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     | 1522 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                | 19.81 MWh  |                | Max plant heat        |
|                                           |            |                | requirement (t = 393) |
+-------------------------------------------+------------+----------------+-----------------------+
| Max thermal loss (t = 323 CEA, 8625 Sim)  | 15.52 kWh  |  14.62 kWh     | difference = 6.2 %    |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss                       | 34.14 MWh/a|  31.72 MWh/a   | difference = 7.6 %    |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss (t = 421)               | 543 kPa    |   536 kPa      | difference = 1.41 %   |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss                      | 329 MPa    |   245 MPa      | difference = 34.44 %  |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss                            |  2.17 %    |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 5.65% higher                			  |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 980% higher                 			  |
+-------------------------------------------+------------+----------------+-----------------------+

For the case of two supply plants in network 2, large differences between the results of the CEA model and the 
simulink model were found, especially for the pressure losses. The large deviation stems from one primary source:
in the CEA model, the node demand mass flow is split evenly between the two supply plants. In the simulink model
the mass flow rates are optimized to reduce the total pressure losses in the pipes. The two severely different
edge mass flows lead to the large deviations of pressure and thermal losses. 

Since this deviation is caused by a question of system controls and not the equations calculating network losses, 
the large deviations from simulink to CEA for network 2 do not influence the validation of the CEA network equations. 
The deviations are most notable for cases in which one or several nodes have 0 heating demand in that timestep. 

.. figure:: network2.png


Future Improvements
===================

1. Implement a control strategy to terminate operation when flow rate is too low
2. Include pressure and thermal losses in corners, valves, etc. 
3. Adapt simulink model for network 2 to evenly distribute massflows between supply plants. 

Conclusion
==========

The simulation output from CEA network model is able to calculate the maximum heat loss with an accuracy of around 6%, 
leading to a decision of the plant capacity within 0.01% difference from Simulink. 
