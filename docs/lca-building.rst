Building Materials
==================

Data about carbon accounting of building materials are stored in ``..databases/lifecycle/LCA_buildings.xls``.
The data are classified in the following spreadsheets:

-  ``EMBODIED_ENERGY``: non-renewable primary energy demand for material manufacturing, construction and
    decommissioning (in MJ-oil/m².yr).
-  ``EMBODIED_EMISSIONS``: CO₂ equivalent emissions for material manufacturing, construction and decommissioning (in
    kg CO₂-eq/m².yr).

Each spreadsheet relates the properties of construction materials to a building category.
Each contains the following attributes:

+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| Variable           | Type   | Description                                                                                        | Valid Values        | Ref. |
+====================+========+====================================================================================================+=====================+======+
| ``building_use``   | string | Type of building use.                                                                              | ``MULTI_RES``, etc. |      |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``year_start``     | int    | Lower bound of archetype age interval.                                                             | (0...n)             | [1]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``year_end``       | int    | Upper bound of archetype age interval.                                                             | (0...n)             | [1]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``standard``       | int    | Indicates a construction or renovation archetype.                                                  | ``C`` or ``R``.     | [1]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Wall_ext_ag``    | int    | Energy/emissions per unit of area of external walls above ground.                                  | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Wall_ext_bg``    | int    | Energy/emissions per unit of area of external walls bellow ground.                                 | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Floor_int``      | int    | Energy/emissions per unit of area of internal floors.                                              | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Wall_int_sup``   | int    | Energy/emissions per unit of area of internal partitions above ground.                             | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Wall_int_nosup`` | int    | Energy/emissions per unit of area of internal partitions bellow ground.                            | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Roof``           | int    | Energy/emissions per unit of roof area.                                                            | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Floor_g``        | int    | Energy/emissions per unit of basement floor area.                                                  | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Services``       | int    | Energy/emissions per unit of gross floor area attributed to technical installations.               | (0...n)             | [3]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Win_ext``        | int    | Energy/emissions per unit of area of windows.                                                      | (0...n)             | [2]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+
| ``Excavation``     | int    | Energy/emissions per unit of ground floor area attributed to excavation for building construction. | (0...n)             | [3]_ |
+--------------------+--------+----------------------------------------------------------------------------------------------------+---------------------+------+

References
~~~~~~~~~~

.. [1] Girardin, L. (2012). A GIS-based Methodology for the Evaluation of Integrated Energy Systems in Urban Areas.
    École Polytechnique Federale de Lausanne (EPFL).
.. [2] Thoma, E., Fonseca, J. A., and Schlueter, A. (2014). Estimation of base-values for Grey Energy, Primary Energy,
    Global Warming Potential (GWP 100A) and Umweltbelastungspunkte (UBP 2006) for Swiss constructions from before 1920
    until today. In DAKAM (Ed.), Contemporary Urban Issues ’14 (p. 17). Istanbul.
.. [3] Schweizerischer Ingenieur- und Architektenverein (SIA). (2010). Graue Energie von Gebauden SIA 2032. Zurich.