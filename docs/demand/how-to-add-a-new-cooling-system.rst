How to add a heating/cooling system in CEA
==========================================

Step 0: Make an issue and create a branch
------------------------------------------
As this procedure requires adding scripts in CEA master, please make a branch before performing the changes.


Step 1: Add the new system to the database
------------------------------------------
#. Open ``cea/databases/systems/emission_systems.xls``
#. In the tab ``heating`` or ``cooling``, add a row for the new system.
#. Specify the operating conditions of the new system, for cooling systems:
- ``code``: add a new code ``Tx`` that has not been used.
- ``Qcsmax_Wm2``: maximum cooling capacity of the system.
- ``dTcs_C``:
For Air Handling Units (ahu), if applicable:
- ``Tscs0_ahu_C``: coolant (water) supply temperature at the primary side
- ``dTcs0_ahu_C``: temperature change of the coolant at the primary side
- ``Tc_sup_air_ahu_C``: air supply temperature from ahu to the room
For Air Recirculation Units (aru), if applicable:
- ``Tscs0_aru_C``: coolant (water) supply temperature at the primary side
- ``dTcs0_aru_C``: temperature change of the coolant at the primary side
- ``Tc_sup_air_aru_C``: air supply temperature from ahu to the room
For Sensible Cooling Units (scu), if applicable:
- ``Tscs0_scu_C``: coolant (water) supply temperature at the primary side
- ``dTcs0_scu_C``: temperature change of the coolant at the primary side


Step 2: Add the new system to the options
------------------------------------------
#. Go to script ``cea/demand/control_heating_cooling_systems.py``
#. Add the code of the new systems (Tx) to function ``has_cooling_systems`` or ``has_heating_systems``
#. Add a new function that check the type of the system, similar to ``has_3for2_cooling_systems``


Step 3: Add a new function to model new technologies
----------------------------------------------------
Currently, there are models for AHU, ARU, SCU running wiht heating/cooling coil.
If the new systems is utilizing different technologies, the models should be added to `airconditioning_model.py`.


Step 3: Add a new function to calculate cooling/heating loads
-------------------------------------------------------------
#. Go to script ``cea/demand/hourly_procedure_heating_cooling_system_load.py``
#. Add a new function to set up the calculation procedure for cooling/heating loads, similar to ``calc_cool_loads_3for2``


Step 4: Add distribution losses
-------------------------------
#. Go to `cea/demand/sensible_loads.py`
#. Update `calc_q_dis_ls_heating_cooling`

Step 5: Calculate temperature and mass flow primary supply systems 
------------------------------------------------------------------
#. Go to `cea/demand/sensible_loads.py`
#. Update `calc_temperatures_emission_systems`


Step 6: Calculate auxiliary electricity
----------------------------------------
`calc_Eauxf_cs_dis`
`calc_Eauxf_hs_dis`