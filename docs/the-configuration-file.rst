Cascading Configuration Files
=============================

The City Energy Analyst uses a system of cascading configuration files for storing user preferences. User preferences
are inputs to simulation runs that are not well captured by the other input files.

The order of the cascade
------------------------

The configuration files are searched in this order:

1. the scenario (``scenario.config``)
2. the project (directory containing the scenario folder ``project.config``)
3. the user's home folder (``cea.config``)
4. the cea default valeus (``default.config``)

With configuration files higher up in the list overwriting values defined in the files lower down in the list.

The effective configuration file
--------------------------------

The effective configuration file stores the configuration used in the last run of the CEA and is mainly used for
documenting the configuration settings as part of the inputs to a calculation. You can also re-create a specific run
by using the global ``--config FILE`` option to the ``cea`` command to process this file.

Variable interopolation and special variables
---------------------------------------------

- CEA.DB
- CEA.SCENARIO

List of configuration settings
------------------------------

.. code-block:: none

    scenario=\%(TEMP)s/reference-case-open/baseline
    multiprocessing=on


    [demand]
    weather=
    heating_season_start:
    heating_season_end:
    cooling_season_start:
    cooling_season_end:

    [radiation]
    longitude=
    latitude=