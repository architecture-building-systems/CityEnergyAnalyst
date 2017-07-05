Occupancy schedules
===================

CEA ships with schedules for the Swiss-European context as a default in
``..databases/archetypes/occupancy_schedules_SIA.xlsx``. These schedules describe a daily probability distribution of
occupancy, appliance and lighting use, and water consumption in buildings. The data are classified in a spreadsheet
according the next building occupancy types:

- ``MULTI_RES``: Multiple Dwelling Unit.
- ``SINGLE_RES``: Single Dwelling Unit.
- ``OFFICE``: offices / administration uses.
- ``INDUSTRIAL``: lightweight industrial uses.
- ``RETAIL``: retail store.
- ``RESTAURANT``: restaurant.
- ``SERVERROOM``: server / data center.
- ``SWIMMING``: swimming pool complex.
- ``SCHOOL``: educational.
- ``HOSPITAL``: hospital.
- ``FOODSTORE``: supermarket.
- ``HOTEL``: hotel.
- ``GYM``: gym / sport center.
- ``COOLROOM``: cooling room.
- ``PARKING``: deposit (storage room, not air-conditioned, parking lots etc.).
- ``LAB``: laboratory.
- ``MUSEUM``: museum / exhibition space.
- ``LIBRARY``: library.

The contents of every spreadsheet are:

+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| Variable       | Type  | Unit | Description                                                                  | Valid Values | Ref.       |
+================+=======+======+==============================================================================+==============+============+
| ``Weekday_1``  | float | \-   | Probability of occupant presence at each hour during weekdays.               | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Saturday_1`` | float | \-   | Probability of occupant presence at each hour during Saturdays.              | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Sunday_1``   | float | \-   | Probability of occupant presence at each hour during Sundays.                | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Weekday_2``  | float | \-   | Probability of use of appliances and lighting at each hour during weekdays.  | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Saturday_2`` | float | \-   | Probability of use of appliances and lighting at each hour during Saturdays. | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Sunday_2``   | float | \-   | Probability of use of appliances and lighting at each hour during Sundays.   | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Weekday_3``  | float | \-   | Probability of use of domestic hot water at each hour during weekdays.       | (0.1...1)    | [2]_, [3]_ |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Saturday_3`` | float | \-   | Probability of use of domestic hot water at each hour during Saturdays.      | (0.1...1)    | [2]_, [3]_ |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Sunday_3``   | float | \-   | Probability of use of domestic hot water at each hour during Sundays.        | (0.1...1)    | [2]_, [3]_ |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Weekday_4``  | float | \-   | Probability of industrial processes occurring at each hour during weekdays.  | (0.1...1)    | [3]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Saturday_4`` | float | \-   | Probability of industrial processes occurring at each hour during Saturdays. | (0.1...1)    | [3]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Sunday_4``   | float | \-   | Probability of industrial processes occurring at each hour during Sundays.   | (0.1...1)    | [3]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Month``      | float | \-   | Probability of all distributions on a monthly basis.                         | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+
| ``Occ``        | int   | m²/p | Occupant density for each use type in square meters per person.              | (0.1...1)    | [1]_       |
+----------------+-------+------+------------------------------------------------------------------------------+--------------+------------+

References
~~~~~~~~~~

.. [1] Schweizerischer Ingenieur- und Architektenverein (SIA). (2006).
    Standard-Nutzungsbedingungen für die Energie- und Gebäudetechnik Merkbatt 2024. Zurich.
.. [2] Blatter M., Borel M., Simmler H., Paul H. (1993). Warmwasserbedarfszahlen und Verbrauchscharakteristik. Bern.
.. [3] Values assumed or without reference.
