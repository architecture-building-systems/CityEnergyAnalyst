Building Properties
===================

CEA ships with Archetypes for the Swiss-European context as a default in `..databases/archetypes/Archetypes_properties.xlsx`. Each archetype is stored in a single spreadsheet, which relates the typology of buildings to properties of:

- [Architecture](##architecture)
- [Indoor comfort](##indoor-comfort)
- [Internal loads](##internal-loads)
- [Thermal properties](##thermal-properties)
- [Mechanical systems](#mechanical-systems)
- [Embodied energy](#embodied-energy)
- [Embodied emissions](#embodied-emissions)

Data about carbon accounting of building energy supply systems are
stored in ``..db/CH/Systems/supply_systems.xls``. The data are
classified in a spreadsheet according the next type of energy services
attended.

-  ``dhw``: domestic hot water.
-  ``heating``: Single Dwelling Unit.
-  ``cooling``: space cooling.
-  ``electricity``: space cooling.

The spreadsheet ``ARCHITECTURE`` relates architecture properties of
buildings to a building category. It contains the next attributes:

+----------+--------+------------------+-----------------------------------------------------------------------------------------------------------------+----------------+-------+
| Variable | Type   | Unit             | Description                                                                                                     | Valid Values   | Ref.  |
+==========+========+==================+=================================================================================================================+================+=======+
| Code     | string | \-               | code of type of main energy supply system (e.g., solar collector, natural gas in district heating network etc.) | T0,T1,T2,...Tn | -     |
+----------+--------+------------------+-----------------------------------------------------------------------------------------------------------------+----------------+-------+
| PEN      | float  | MJ-oil/m2.yr     | Non-renewable Primary energy factor (only fossil fuels contribution)                                            | (0.0.....4)    | [1]_  |
+----------+--------+------------------+-----------------------------------------------------------------------------------------------------------------+----------------+-------+
| CO2      | float  | kg CO2-eq/m2.yyr | CO22 equivalent emissions factor (only fossil fuels contribution)                                               | (0.0.....0.2)  | [1]_  |
+----------+--------+------------------+-----------------------------------------------------------------------------------------------------------------+----------------+-------+

References
~~~~~~~~~~

.. [1] Schweizerischer Ingenieur- und Architektenverein (SIA). (2006).
    Standard-Nutzungsbedingungen für die Energie- und Gebäudetechnik Merkbatt 2024. Zürich.
