Energy Infrastructure
=====================

Data about carbon accounting of building energy supply systems are
stored in ``..databases/lifecycle/LCA_infrastructure.xls``. The data are
classified in a spreadsheet according the next type of energy services
attended.

-  ``dhw``: domestic hot water.
-  ``heating``: space heating.
-  ``cooling``: space cooling.
-  ``electricity``: electricity.

Each spreadsheet contains the following attributes:

+----------+--------+-----------------+-------------------------------------------------------------------------------------+-------------------------------+-------+
| Variable | Type   | Unit            | Description                                                                         | Valid Values                  | Ref.  |
+==========+========+=================+=====================================================================================+===============================+=======+
| Code     | string | \-              | Code of type of main energy supply system (solar collector, oil-fired boiler, etc.) | ``T0``, ``T1``, ..., ``Tn``   |       |
+----------+--------+-----------------+-------------------------------------------------------------------------------------+-------------------------------+-------+
| ``PEN``  | float  | MJ-oil/m².yr    | Non-renewable Primary energy factor (only fossil fuel contribution)                 | (0.0.....n)                   | [1]_  |
+----------+--------+-----------------+-------------------------------------------------------------------------------------+-------------------------------+-------+
| ``CO2``  | float  | kg CO₂-eq/m².yr | CO2 equivalent emissions factor (only fossil fuel contribution)                     | (0.0.....n)                   | [1]_  |
+----------+--------+-----------------+-------------------------------------------------------------------------------------+-------------------------------+-------+


References
~~~~~~~~~~

.. [1] Die Koordinationskonferenz der Bau- und Liegenschaftsorgane der Oeffentlichen Bauherren (KBOB) (2012).
    “Ökobilanzdaten Im Baubereich: 2009/1.”
