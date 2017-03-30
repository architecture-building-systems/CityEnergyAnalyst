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
           benchmark-graphs,weather-files,weather-path,
           locate,demand-graphs, scenario-plots,latitude,longitude,
           radiation,install-toolbox, heatmaps}
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

The sub-commands can be grouped into three groups: Main commands that work on a single scenario, main commands that work
on multiple scenarios and auxillary commands. Main commands that work on multiple scenarios have a ``--scenarios``
option for specifying the scenarios to work on - these commands ignore the ``-s`` global option for specifying the
scenario folder.

Main commands
.............

Main commands that work on a single scenario are:

- demand (calculate the demand load of a scenario)
- demand-helper (apply archetypes to a scenario)
- emissions (calculate emissions due to operation)
- embodied-energy (calculate embodied energy)
- mobility (calculate emissions due to mobility)
- demand-graphs (create graphs for demand output variables per building)
- radiation (create radiation data as input to the demand calculation)
- heatmaps (create heatmaps based on demand and emissions output)
- extract-reference-case (extracts a sample reference case that can be used to test-drive the CEA)

Main commands that work on multiple scenarios:

- benchmark-graphs (create graphs for the 2000 Watt society benchmark for multiple scenarios)
- scenario-plots (plots various scenarios against each other)

Auxillary commands
..................

- weather-files (list the weather names shipped with the CEA)
- weather-path (given a weather name {see above} return the path to the file)
- latitude (try to guess the latitude of a scenario based on it's building geometry shapefile)
- longitude (try to guess the longitude of a scenario based on it's building geometry shapefile)
- install-toolbox (install the ArcGIS interface)
- locate (gives access to the InputLocator class for finding paths)

Commands for developers
.......................

- test (runs a set of tests - requires access to the private repository *cea-reference-case*)

To run the ``cea test`` tool, you will need to provide authentication for the *cea-reference-case* repository. The
options ``--user`` and ``--token`` should be set to your GitHub username and a Personal Access Token. These will be
stored in your home folder in a file called ``cea_github.auth``. The first line is the username, the second contains the
token. See this page on how to create such a token: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
In the scopes section, select "repo (Full control of private repositories)" for the token.


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
