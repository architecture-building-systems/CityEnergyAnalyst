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
| Pipe roughness                       | 2E-5 (steel pipe)         |
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






