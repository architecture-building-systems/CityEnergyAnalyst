User Interfaces
===============

The CEA code exposes multiple interfaces as an API:

-  CLI (Command Line Interface) - each module in the CEA implements a
   CLI for calling it from the command line.
-  ArcGIS - the CEA implements an ArcGIS Toolbox (in the folder
   ``cea/GUI``) to run the modules from within ArcScene 10.4
-  euler - a set of scripts for running the CEA sensitivity analysis on
   the ETH Euler cluster is provided in the folder ``euler`` and can be
   used as a starting point for running the analysis on similar clusters
   and / or linux machines.

The Command Line Interface
--------------------------

The most portable way to interact with the CEA is via the CLI. Type the following command in your shell to see the
list of commands available::

    > cea --help
    usage: cea [-h] [-s SCENARIO]
           {demand,demand-helper,emissions,embodied-energy,mobility,
           benchmark-graphs,weather-files,weather-path,locate,demand-graphs,
           scenario-plots,latitude,longitude,radiation,install-toolbox,
           heatmaps}
           ...

    positional arguments:
    {demand,demand-helper,emissions,embodied-energy,mobility,
    benchmark-graphs,weather-files,weather-path,locate,demand-graphs,
    scenario-plots,latitude,longitude,radiation,install-toolbox,heatmaps}

    optional arguments:
    -h, --help            show this help message and exit
    -s SCENARIO, --scenario SCENARIO
                          Path to the scenario folder

Most commands work on a scenario folder, provided with the global option ``-s`` and defaults to the current
directory - if you ``cd`` to the scenario folder, you can ommit the ``-s`` option.

Each sub-command (one of ``demand``, ``demand-helper`` etc.) may provide additional arguments that are required to
run that sub-command. For example, the ``embodied-energy`` sub-command has an (optional) option ``--year-to-calculate``

::

    > cea embodied-energy --help
    usage: cea embodied-energy [-h] [--year-to-calculate YEAR_TO_CALCULATE]

    optional arguments:
    -h, --help            show this help message and exit
    --year-to-calculate YEAR_TO_CALCULATE
                          Year to calculate for (default: 2017)

As you can see, you can get help on any sub-command by typing ``cea SUBCOMMAND --help``. This will list the expected
arguments as well as the default values used.

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
