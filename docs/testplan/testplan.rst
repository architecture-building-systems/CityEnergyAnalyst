Testplan for the CityEnergyAnalyst
==================================

This document outlines the steps necessary for testing a full version of the CEA.

Testing the CEA can be broken down into these activites:

- testing the installer on each supported platform
- testing each of the scripts, according to testing template
- checking the documentation
  - ist the information correct?
  - grammar / spelling issues?
  - formatting?

Ideally, the testing activity can be distributed among the CEA developers. Ideally, as much as possible of the testing
can be automated - especially running parameter studies and checking output.

Testing template
----------------

The testing template document (``test_template.rst``) should be should be copied to a subfolder of ``docs/testplan`` for
each release and script. ``docs/testplan/v2.8/test_demand.rst`` would contain the filled out version of the
``test_template.rst`` document for the ``demand`` script.

List of scripts to test
-----------------------

Format: ``- script-name (script-author, script-tester)``

- benchmark-graphs 
- compile
- config-editor
- create-new-project
- data-helper
- dbf-to-excel
- demand
- embodied-energy
- emissions
- excel-to-dbf
- excel-to-shapefile
- extract-reference-case
- heatmaps
- install-grasshopper
- install-toolbox
- list-demand-graphs-fields
- mobility
- operation-costs
- photovoltaic
- photovoltaic-thermal
- radiation
- radiation-daysim
- retrofit-potential
- scenario-plots,
- sensitivity-demand-analyze
- sensitivity-demand-samples,
- sensitivity-demand-simulate
- shapefile-to-excel
- solar-collector
- test