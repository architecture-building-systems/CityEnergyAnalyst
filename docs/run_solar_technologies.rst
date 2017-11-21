Solar technologies
==================

The current CEA simulates three solar technologies: photovoltaic panels, photovoltaic thermal panels, and solar thermal
collectors. The simulation is performed by three scripts: ``photovoltaic.py``, ``photovoltaic_thermal.py``, and
``solar_collectors.py`` in ``cea/technologies/`` folder.

Following are the steps to run the solar technology scripts: (take ``photovoltaic.py`` as an example)

1. Prepare radiation files by running ``radiation_main.py``
2. Specify inputs:

   - ``min_radiation`` : A user input. Minimum radiation threshold to install solar panels, represented as % of the
     maximum solar radiation in the district.
   - ``type_PVpanel``: A list of panels in ``..databases/systems/supply_systems.xls`` **FIXME: this doesn't seem to be a list input, rather select one from the list??**
   - ``worst_hour``: Site specific input. First hour of sunrise on the solar solstice at the case study location.
   - ``misc_losses``: Default input. Losses from cabling, resistances etc..
   - ``pvonroof``: A user input. True if allow PV installed on roofs.
   - ``pvonwall``: A user input. True if allow PV installed on walls.
   - ``longitude``: Site specific input. Longitude of the case study location.
   - ``latitude``: Site specific input. Latitude of the case study location.
   - ``date_start``: Default input. From global variable.

3. Expected outputs:

   - A file ``Building_name_PV.csv`` is produced for each building, which is saved at
     ``SCENARIO/outputs/data/solar-radiation``. It includes the hourly electricity production from the PV panels.



References
----------

Schweizerischer Ingenieur- und Architektenverein (SIA). (2006). Standard-Nutzungsbedingungen für die Energie- und
Gebäudetechnik Merkbatt 2024. Zürich.