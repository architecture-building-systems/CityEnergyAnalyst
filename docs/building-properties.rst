Construction Properties
=======================

CEA ships with Archetypes for the Swiss-European context as a default in
``..databases/archetypes/construction_properties.xlsx``. Each archetype is stored in a single spreadsheet, which relates
the typology of buildings to properties of:

- Architecture
- Heating, ventilation and air-conditioning (HVAC)
- Indoor comfort
- Internal loads


Architecture
~~~~~~~~~~~~

The spreadsheet ``ARCHITECTURE`` relates architecture properties of buildings to a building category.
It contains the following attributes:

+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| Variable         | Type   | Description                                       | Valid Values                           | Ref. |
+==================+========+===================================================+========================================+======+
| ``building_use`` | string | Type of building use.                             | ``MULTI_RES``, ``HOTEL``, etc.         |      |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``year_start``   | int    | Lower bound of archetype age interval.            | (0...n)                                | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``year_end``     | int    | Upper bound of archetype age interval.            | (0...n)                                | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``standard``     | int    | Indicates a construction or renovation archetype. | ``C`` or ``R``.                        | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``Hs``           | float  | Share of gross floor area that is heated.         | (0.0...1.0)                            | [2]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``wwr_north``    | float  | Window-to-wall ratio of north-facing wall.        | (0.0...1.0)                            | [2]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``wwr_south``    | float  | Window-to-wall ratio of south-facing wall.        | (0.0...1.0)                            | [2]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``wwr_east``     | float  | Window-to-wall ratio of east-facing wall.         | (0.0...1.0)                            | [2]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``wwr_west``     | float  | Window-to-wall ratio of west-facing wall.         | (0.0...1.0)                            | [2]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_cons``    | string | Construction type (heavy/lightweight).            | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_leak``    | string | Building leakage (tight/leaky).                   | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_win``     | string | Type of windows.                                  | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_roof``    | string | Type of external finishing of roof.               | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_wall``    | string | Type of external finishing of walls.              | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_shade``   | string | Type of shading system.                           | See ``..systems/envelope_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+


HVAC
~~~~

The spreadsheet ``HVAC`` relates properties of Heating, ventilation and air-conditioning (HVAC) systems in buildings
according to their year of construction, retrofit and type of building use. It contains the next attributes:

+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| Variable         | Type   | Description                                       | Valid Values                           | Ref. |
+==================+========+===================================================+========================================+======+
| ``building_use`` | string | Type of building use.                             | ``MULTI_RES``, ``HOTEL``, etc.         |      |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``year_start``   | int    | Lower bound of archetype age interval.            | (0...n)                                | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``year_end``     | int    | Upper bound of archetype age interval.            | (0...n)                                | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``standard``     | int    | Indicates a construction or renovation archetype. | ``C`` or ``R``.                        | [1]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_hs``      | string | Type of emission system for space heating.        | See ``..systems/emission_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_cs``      | string | Type of emission system for space heating.        | See ``..systems/emission_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_dhw``     | string | Type of emission system for space heating.        | See ``..systems/emission_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_ctrl``    | string | Type of room temperature control.                 | See ``..systems/emission_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+
| ``type_vent``    | string | Type of ventilation system.                       | See ``..systems/emission_systems.xls`` | [5]_ |
+------------------+--------+---------------------------------------------------+----------------------------------------+------+


Indoor comfort
~~~~~~~~~~~~~~

The spreadsheet ``INDOOR COMFORT`` relates the typical comfort standard of buildings to a type of building use. It 
contains the next attributes:

+-----------------+--------+-------+------------------------------------------+---------------------+------+
| Variable        | Type   | Unit  | Description                              | Valid Values        | Ref. |
+=================+========+=======+==========================================+=====================+======+
| ``Code``        | string | \-    | Type of building use.                    | ``MULTI_RES``, e.g. |      |
+-----------------+--------+-------+------------------------------------------+---------------------+------+
| ``T_cs_set_C``  | float  | °C    | Set-point temperature for space cooling. | (0.1...n)           | [3]_ |
+-----------------+--------+-------+------------------------------------------+---------------------+------+
| ``T_hs_set_C``  | float  | °C    | Set-point temperature for space heating. | (0.1...n)           | [3]_ |
+-----------------+--------+-------+------------------------------------------+---------------------+------+
| ``T_cs_setb_C`` | float  | °C    | Set-back temperature for space cooling.  | (0.1...n)           | [5]_ |
+-----------------+--------+-------+------------------------------------------+---------------------+------+
| ``T_hs_setb_C`` | float  | °C    | Set-back temperature for space heating.  | (0.1...n)           | [5]_ |
+-----------------+--------+-------+------------------------------------------+---------------------+------+
| ``Ve_lps``      | float  | l/p/s | Minimum air ventilation rate per person. | (0.1...n)           | [3]_ |
+-----------------+--------+-------+------------------------------------------+---------------------+------+


Internal loads
~~~~~~~~~~~~~~

The spreadsheet ``INTERNAL_LOADS`` relates typical internal loads in buildings to a type of building use. It contains
the next attributes:

+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| Variable       | Type   | Unit  | Description                                                                                | Valid Values        | Ref. |
+================+========+=======+============================================================================================+=====================+======+
| ``Code``       | string | \-    | Type of building use.                                                                      | ``MULTI_RES``, e.g. | [2]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Qs_Wp``      | float  | W/p   | Sensible heat gain due to occupancy.                                                       | (0.1...n)           | [3]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``X_ghp``      | float  | g/h/p | Humidity release due to occupancy.                                                         | (0.1...n)           | [3]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Ea_Wm2``     | float  | W/m²  | Maximum electrical consumption due to appliances per unit of gross floor area.             | (0.1...n)           | [3]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``El_Wm2``     | float  | W/m²  | Maximum electrical consumption due to lighting per unit of gross floor area.               | (0.1...n)           | [3]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Epro_Wm2``   | float  | W/m²  | Maximum electrical consumption due to processes per unit of gross floor area.              | (0.1...n)           | [4]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Ere_Wm2``    | float  | W/m²  | Maximum electrical consumption due to refrigeration services per unit of gross floor area. | (0.1...n)           | [5]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Ed_Wm2``     | float  | W/m²  | Maximum electrical consumption due to servers per unit of gross floor area.                | (0.1...n)           | [5]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Vww_lpd``    | float  | l/p/d | Maximum daily consumption of domestic hot water per person.                                | (0.1...n)           | [5]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Vw_lpd``     | float  | l/p/d | Maximum daily consumption of water per person.                                             | (0.1...n)           | [5]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Qhpro_Wm2``  | float  | W/m²  | Maximum process heat consumption per unit of gross floor area.                             | (0.1...n)           | [4]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+
| ``Qcpro_Wm2``  | float  | W/m²  | Maximum process cooling consumption per unit of gross floor area.                          | (0.1...n)           | [5]_ |
+----------------+--------+-------+--------------------------------------------------------------------------------------------+---------------------+------+


References
~~~~~~~~~~

.. [1] Girardin, L. (2012). A GIS-based Methodology for the Evaluation of Integrated Energy Systems in Urban Areas. 
    École Polytechnique Federale de Lausanne (EPFL).
.. [2] Schlueter A., Fonseca J. A., Willmann A., Wirz C., Moebus S., Hofstetter S., Stauffacher M., Moser C., Muggli N.,
    Schaer M., and Gruenewald, T. (2015). Nachhaltige, softwaregestützte Arealtransformation vom Industriestandort zum
    Stadtquartier. Zurich.
.. [3] Schweizerischer Ingenieur- und Architektenverein (SIA). (2006).
    Standard-Nutzungsbedingungen für die Energie- und Gebäudetechnik Merkbatt 2024. Zurich.
.. [4] Bachmann S., Scherer R., Salamin P.A., Ferster M., and Gulden J. (2013).
    Energieverbrauch in der Industrie und im Dienstleistungssektor: Resultate 2012. Bern.
.. [5] Values assumed or without reference.
