Glossary
========
Input Databases
------------------------


Default Databases
------------------------
Default databases are fomatted using .xlsx.


supply_systems
^^^^^^^^^^^^^^

Description: catalogs pipe schedule.

.. list-table:: Database Contents
   :widths: auto
   :header-rows: 1

   * - Nomenclature
     - Description
     - Unit
   * - Description
     - Describes the nominal diameter
     - DN# (string)
   * - Diameter_max
     - Describes max pipe diameter
     - (float)
   * - Diameter_min
     - Describes min pipe diameter
     - (float)
   * - Unit
     - Describe measuring unit
     - (string)
   * - Investment
     - Describes investment cost
     - (float)
   * - Currency
     - Defines cost denomination
     - USD-2015 (string)


archetypes_schedules
^^^^^^^^^^^^^^^^^^^^^^

Description: catalogs probibility in hour steps (0-24) and occupency density.

.. list-table:: Database Contents
   :widths: auto
   :header-rows: 1

   * - Nomenclature
     - Description
     - Unit
   * - Use of lighting and appliances
     - Probibility in hour steps
     - (float)
   * - Domestic hot water consumption
     - Probibility in hour steps
     - (float)
   * - Monthly use
     - Probibility in hour steps
     - (float)
   * - Daily processes
     - Probibility in hour steps
     - (float)
   * - Investment
     - Probibility in hour steps
     - (float)
   * - Occupation Density
     - Defines static density
     - Persons/m2 (float)


LCA_buildings
^^^^^^^^^^^^^^^^
Description: Defines the model's Embodied_Energy and Embodied_Emissions in distinct .xlsx pages.

.. list-table:: Embodied_Energy Database Contents
   :widths: auto
   :header-rows: 1

   * - Nomenclature
     - Description
     - Unit
   * - building_use
     - Defines intended building function (OFFICE...)
     - (string)
   * - year_start 
     - Categorises 
     - (string)
   * - year_end 
     -
     - (string)
   * - standard 
     -
     -
   * - Wall_ext_ag
     - Embodied energy 
     -
   * - 
     -
     -
   * - 
     -
     -
   * - 
     -
     -
   * - 
     -
     -
   * - 
     -
     -

Blank 

Title
^^^^^^^^^^^^^^^^^^^^^^^^

Description:

.. list-table:: Database Contents
   :widths: auto
   :header-rows: 1

   * - Nomenclature
     - Description
     - Unit
   * - 
     -
     -
   * - 
     -
     -
   * - 
     -
     -
   * - 
     -
     -