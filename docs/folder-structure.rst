:orphan:

Folder Structure of the CEA repository
--------------------------------------

The repository of cea, which can be opened from Pycharm contains the next set of folders:

- cea

  - analysis
  - databases
  - demand
  - geometry
  - optimization
  - plots
  - resources
  - technologies
  - utilities
  - examples
  - tests

- docs
- bin
- euler
- setup
- tests

cea
~~~

Contains the source code (human readable) of the different modules of CEA.
This is the core of CEA and is divided in the next sub-folder structure:

cea/analysis
~~~~~~~~~~~~

Contains scripts to analyze the results of all simulations in CEA.

cea/databases
~~~~~~~~~~~~~

Contains default data of weather, technology, occupancy, costs etc.,

cea/demand
~~~~~~~~~~

Contains scripts to calculate the demand of energy in buildings

cea/geometry
~~~~~~~~~~~~

Contains scripts to manipulate and read building geometry.

cea/optimization
~~~~~~~~~~~~~~~~

Contains scripts aiming to optimize the energy system of a district.

cea/plots
~~~~~~~~~

Contains scripts to plot information.

cea/resources
~~~~~~~~~~~~~

Contains scripts to analyze the potential of energy sources.

cea/technologies
~~~~~~~~~~~~~~~~

Contains scripts for the simulation of different technologies.

cea/utilities
~~~~~~~~~~~~~

Contains functions needed by any other script frequently.

cea/examples
~~~~~~~~~~~~

Contains an open source case study to test the cea.

cea/tests
~~~~~~~~~

Contains unitest data and scripts necessary ot run our automatic code checker in Github.

docs
~~~~

Contains the developers manual of the CEA.

euler
~~~~~

Contains source code needed to connect to the cluster of 50K cores called Euler at ETH Zurich
(Only researchers at ETH Zurich can use this).
