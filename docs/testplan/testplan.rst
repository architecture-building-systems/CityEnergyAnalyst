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

.. note:: which scripts do we need to test first for the executive course?

Format: ``- script-name (script-author, script-tester)``

- demand (JF, ?)
- data-helper (JF, ?)
- emissions (JF, ?)
- embodied-energy (JF, ?)
- mobility (MM, ?)
- benchmark-graphs = (MM, ?)
- list-demand-graphs-fields (DT??, ?)
- scenario-plots (DT??, ?)
- radiation (JF, ?) NOTE: do we still need this? Or remove it entirely?
- photovoltaic (JF, ?)
- solar-collector (JF/SH, ?)
- photovoltaic-thermal (JF/SH, ?)
- radiation-daysim (PN/KW, ?)
- install-toolbox (DT, ?)
- install-grasshopper (DT, ?)
- heatmaps (JF, ?)
- operation-costs (JF, ?)
- retrofit-potential (JF/GH, ?)
- test (DT, ?)
- extract-reference-case (DT, ?)
- compile = (DT, ?) NOTE: do we still need this? Or remove it entirely?
- excel-to-dbf (DT, ?)
- dbf-to-excel (DT, ?)
- shapefile-to-excel (DT, ?)
- excel-to-shapefile (DT, ?)
- sensitivity-demand-samples (JF, ?)
- sensitivity-demand-simulate (JF, ?)
- sensitivity-demand-analyze (JF, ?)
- config-editor (DT, ?)
- create-new-project (JF, ?)


Other stuff to test
-------------------

- UBG (SZ, ?)
- Check tutorials

  - are the screenshots up-to-date?
  - spelling / grammar? (get a native speaker to check this... also: grammarly)

- data-mining of the outputs

  - statistically plausible?
  - ipython notebooks (see folder `notebooks`, create such notebooks with code for testing)