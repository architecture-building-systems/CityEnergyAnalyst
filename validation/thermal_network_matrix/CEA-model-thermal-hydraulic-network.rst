Validation of CEA network model
===============================

:Author: Shanshan Hsieh, Sreepathi Bhargava Krishna
:Date: 30-June-2017

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
| Annual heat supplied by the heating plant | 2685 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     | 2303 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                | 2.7 MWh    |                | Max plant heat        |
|                                           |            |                | requirement (t = 419) |
+-------------------------------------------+------------+----------------+-----------------------+
| Max thermal loss (t = 419)                | 12.8 kWh   | 12.1 kWh       | difference = 6%       |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss                       | 34 MWh/a   | 32 MWh/a       | difference = 6.4%     |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss (t = 419)               | 676 kPa    | 686 kPa        | difference = -1.5%     |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss                      | 192 MPa    | 195 MPa        | difference = -1%      |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss                            | 1.3%       |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 7% higher  |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 2% lower   |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Hours when dP% > 10%,  t = 438            | 0.1% of the maximum flow rate                       |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8304            | 1.27% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8667            | 0.01% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8668            | 1.94% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+

Network 2:

+-------------------------------------------+------------+----------------+-----------------------+
| Parameter                                 | CEA Model  | Simulink Model | Notes                 |
+===========================================+============+================+=======================+
| Annual heat supplied by the heating plant | 1014 MWh/a |                | two plants            |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     | 2303 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                | 1028 MWh   |                | Max plant heat        |
|                                           |            |                | requirement (t = 419) |
+-------------------------------------------+------------+----------------+-----------------------+
| Max thermal loss (t = 419)                | 12.8 kWh   |   12.1 kWh     | difference = 5.8 %    |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss                       | 34.8 MWh/a |   32.7 MWh/a   | difference = 6.4 %    |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss (t = 419)               | 675 kPa    |   686 kPa      | difference = -1.6 %   |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss                      | 191 MPa    |   195 MPa      | difference = -2%      |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss                            | 1.7 %      |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 7% higher  |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 4% lower   |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Hours when dP% > 10%,  t = 438            | 0.1% of the maximum flow rate                       |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8304            | 1.27% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8667            | 0.01% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+
| Hours with dP% > 10%, t = 8668            | 1.94% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+

Network 3:

+-------------------------------------------+------------+----------------+-----------------------+
| Parameter                                 | CEA Model  | Simulink Model | Notes                 |
+===========================================+============+================+=======================+
| Annual heat supplied by the heating plant | 2350 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual heating demand                     | 2303 MWh/a |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Plant size                                | 2.4 MWh    |                | Max plant heat        |
|                                           |            |                | requirement (t = 419) |
+-------------------------------------------+------------+----------------+-----------------------+
| Thermal loss @ t = 419 (max)              | 11.2 kWh   | 10.4 kWh       | difference = 7.8%     |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual thermal loss                       | 30 MWh/a   | 27 MWh/a       | difference = 11%      |
+-------------------------------------------+------------+----------------+-----------------------+
| Max pressure loss  (t=419)                | 653 kPa    | 662 kPa        | difference = -1%      |
+-------------------------------------------+------------+----------------+-----------------------+
| Annual pressure loss                      | 185 MPa    | 187 MPa        | difference = -1%      |
+-------------------------------------------+------------+----------------+-----------------------+
| % thermal loss                            | 1.3%       |                |                       |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in thermal loss        | 7% higher  |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Average difference in pressure loss       | 2% lower   |                | Excluding t=438, 8667 |
+-------------------------------------------+------------+----------------+-----------------------+
| Hours with maximum difference t = 438     | 0.1% of the maximum flow rate                       |
+-------------------------------------------+-----------------------------------------------------+
| Hours with maximum difference t = 8667    | 0.01% of the maximum flow rate                      |
+-------------------------------------------+-----------------------------------------------------+


1. The plant capacity is sized at the maximum heat requirement, which include the heating demand
from buildings and the thermal loss. At the time step with the maximum heating demand, the difference
in thermal loss between CEA and Simulink is 0.03% of the total plant capacity.

2. The differences in total thermal losses between CEA and Simulink over 8760 hours is around 3 MWh,
which corresponds to 10% of annual heat loss. Since the total thermal losses over 8760 hours at the
supply network accounts for 1.3% of the total heat supplied by the heating plant, the 10% difference
in th thermal loss calculation is in acceptable range.

3. There are four instances (t = 438, 8304, 8667, 8668) where the thermal/hydraulic losses deviate
more than 10% between the results from CEA and Simulink. This is because we assume all flows are
turbulent in CEA, while Simulink considers different heat transfer resistances with different flow
regimes (laminar, turbulent and transitional).

.. figure:: network1.png


.. figure:: network2.png


.. figure:: network3.png



Future Improvements
===================

1. To improve the heat transfer calculation at laminar and transitional flow regime
2. Implement a control strategy to terminate operation when flow rate is too low

Conclusion
==========

The simulation output from CEA network model is able to decide the plant capacity within 0.4%
difference from Simulink