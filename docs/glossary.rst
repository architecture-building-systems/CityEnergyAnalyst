Glossary
========
This glossary contains all the input and output variables used by CEA. These variables are stored in databases,
themed by the type of information they contain. There are three main types of database in CEA:

    - **Input**
        - Primary: These databases define the location and geometry of the district and buildings within.
        - Secondary: These databases are constructed using the default databases. They store assumed variables, such as zone architecture, indoor comfort and loads as well as the building system constraints and typology.

    - **Default**
        These databases act as libraries from which the secondary input databases are built.
        The databases are relevant to the specified location and assumed initial and operating conditions of the
        district.
        They consist of assumed archetypes, benchmarks and building system parameters as well as economic and lifecycle factors
        specific to the scenario.

    - **Output**
        The output databases store most of the variables calculated by the CEA modules, which are subsequently used to plot various
        relationships.

For ease of access, common plot variables are also listed with a brief description in addition to the databases, which only
contain raw data variables stored within them.

The various codes used to define the HVAC, power supply, and pipe types are also defined below, along with the assumed retrofit
and newly constructed thermal assumptions.

.. toctree::

   plots_ref
   databases
   codes_ref