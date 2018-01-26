:orphan:

How to create a new project
===========================

CEA holds a particular folder structure in order to do calls between scripts and tools.
This guide presents how to prepare this folder structure in an automated way for a new project or case study.

Prerequisites
-------------

#. Zone geometry file: A shapefile storing the geometry of buildings.
#. Terrain file: Digital elevation model of the terrain.

.. note:: both prerequisites MUST comply with the naming and structure described in the tutorial
          of `Input databases of CEA <https://docs.google.com/presentation/d/14cgSAhNGnjTDLx_rco9mWU9FFLk0s50FBd_ud9AK7pU/edit#slide=id.g1d85a4d9be_0_0>`__.

set up configuration
--------------------

#. Open Pycharm and the project City Energy Analyst.
#. From the project tab on the left run the configuration editor of cea. The editor is stored in CityEnergyAnalyst>
   cea>interfaces>config_editor>config_editor.py.
#. This command should open a window with the configuration editor.
#. In the configuration editor, scroll down the menu on the left and click in "Create-new-project" tool.
#. On the right side proceed to give an input to the next variables:
    - project: give a name to the new project or case study.
    - scenario: give a name to the baseline scenario of the new project.
    - occupancy-type: Select from the list the occupancy types you will have in your buildings.
    - zone: write the path to the zone geometry file
    - terrain: write the path to the terrain file
    - output-path: location where to create the new project
#. Click save and close the configuration editor.

Running the create new project tool
-----------------------------------
#. Finally, go back to PyCharm. From the the project tab on the left run the create new project tool. The tool is stored
   in CityEnergyAnalyst>cea>utilties>create_new_project.py.
