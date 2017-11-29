User Interfaces
===============

The CEA code exposes multiple interfaces as an API:

-  CLI (Command Line Interface) - each module in the CEA implements a
   CLI for calling it from the command line.
-  ArcGIS - the CEA implements an ArcGIS Toolbox (in the folder
   ``cea/GUI``) to run the modules from within ArcScene 10.4 / 10.5
-  Grasshopper - the CEA implements a Rhino/Grasshopper component for running the CEA scripts
-  euler - a set of scripts for running the CEA sensitivity analysis on
   the ETH Euler cluster is provided in the folder ``euler`` and can be
   used as a starting point for running the analysis on similar clusters
   and / or linux machines.

The Command Line Interface
--------------------------

The most portable way to interact with the CEA is via the CLI. Type the following command in your shell to see the
list of commands available::

    > cea --help
    usage: cea SCRIPT [OPTIONS]
           to run a specific script
    usage: cea --help SCRIPT
           to get additional help specific to a script

    SCRIPT can be one of: benchmark-graphs, compile, data-helper,
        dbf-to-excel, demand, demand-graphs, embodied-energy, emissions,
        excel-to-dbf, extract-reference-case, heatmaps, install-toolbox,
        latitude, list-demand-graphs-fields, locate, longitude, mobility,
        operation-costs, photovoltaic, photovoltaic-thermal, radiation,
        radiation-daysim, read-config, read-config-section,
        retrofit-potential, scenario-plots, sensitivity-demand-analyze,
        sensitivity-demand-samples, sensitivity-demand-simulate,
        solar-collector, test, weather-files, weather-path, write-config

All scripts use the configuration file as the default source of parameters. See the :ref:`configuration-file-details`
for information on the configuration file.

The parameters in the configuration file relevant to a script can be overridden. To see which parameters are used by
a certain script, use the syntax ``cea --help SCRIPT``::

    > cea --help data-helper

    building properties algorithm

    OPTIONS for data-helper:
    --scenario: C:/reference-case-open/baseline
        Path to the scenario to run
    --archetypes: ['comfort', 'architecture', 'HVAC', 'internal-loads']
        List of archetypes to process

This displays some documentation on the script as well as a list of parameters, their default values and a description
of the parameter. Using this information, the ``data-helper`` script can be run like this::

    > cea data-helper --scenario C:/reference-case-open/scenario1 --archetypes HVAC

.. note:: All options are optional and have default values as defined in the configuration file!

ArcGIS interface
----------------

Use the following command to install the interface for ArcScene 10.4 / 10.5::

    > cea install-toolbox

Start ArcScene and check ``Toolboxes/My Toolboxes`` in the Catalog: You should see a toolbox called
"City Energy Analyst.pyt" with all the interfaces.

Rhino / Grasshopper interface
-----------------------------

Use the following command to install the interface for Rhino 5.0 / Grasshopper::

    > cea install-grasshopper

This will install a Grasshopper component in the "CEA" section of the Grasshopper tool menu that can be used to
execute CEA scripts. It works similar to the ``cea`` CLI command described above: Input the name of the script to
run (e.g. "demand") and an (optional) list of parameters. The list of valid parameters to use is the same as for the
CLI interface. When specifying parameters for the "args" input to the component, use this syntax::

    scenario = {general:scenario}/../scenario1
    weather = Zug

.. note:: You can use references to parameters in the configuration file using the ``{SECTION:PARAMETER}`` syntax as
    in the above example.

Planned interfaces
------------------

The following interfaces are planned for the near future:

-  Rhino/Grasshopper - provide a set of components for running CEA
   modules inside Grasshopper
-  VisTrails - provide a set of VisTrails modules for running the CEA


Further ideas
-------------

Other possible interfaces include:

-  Kepler - a set of modules for the Kepler Scientific Workflow software
-  REST - a REST server for executing the CEA in the cloud
