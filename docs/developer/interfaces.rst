User Interfaces
===============

The CEA code exposes multiple interfaces as an API:

-  CLI (Command Line Interface) - each module in the CEA implements a
   CLI for calling it from the command line.
-  euler - a set of scripts for running the CEA sensitivity analysis on
   the ETH Euler cluster is provided in the folder ``scripts/euler`` and can be
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
        excel-to-dbf, extract-reference-case, install-toolbox,
        latitude, list-demand-graphs-fields, locate, longitude, mobility,
        operation-costs, photovoltaic, photovoltaic-thermal, read-config, read-config-section,
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