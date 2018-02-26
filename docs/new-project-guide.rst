:orphan:

How to set up a new case study?
===============================

CEA holds a particular folder structure in order to do calls between scripts and tools.
This guide presents how to prepare this folder structure in an automated way for a new project or case study.

Step 1. Data Mining
--------------------

The objective of this step is to collect the minimum set of inputs needed for a new project. There are basically
two input files you need to collect to start with CEA.

#. Zone geometry file: A shapefile storing the geometry of buildings.
#. Terrain file: Digital elevation model of the terrain.

Optionally you can indicate two more files.

#. District geometry file: A shapefile storing the geometry of buildings and surroundings
#. Streets geometry file: A shapefile storing the geometry of buildings and surroundings

The first will be used to calculate shading in buildings towards the edge of the zone. The second will be used
to create an optimal district and cooling network.

.. note:: all prerequisites MUST comply with the naming and structure described in the tutorial
          of `Input databases of CEA <https://docs.google.com/presentation/d/14cgSAhNGnjTDLx_rco9mWU9FFLk0s50FBd_ud9AK7pU/edit#slide=id.g1d85a4d9be_0_0>`__.

Step 2. Configure CEA
----------------------

The objective of this step is to use the configuration editor to set up the input parameters of the create-new-project tool.

#. Open the configuration editor of CEA. This guide :doc:`config-file-guide` describes how to use it.
#. In the configuration editor, scroll down the menu on the left and click in "Create-new-project" tool.
#. On the right side proceed to give an input to the next variables:

    ===================  =========  ==========================================
    Variable             Unit       Description
    ===================  =========  ==========================================
    project              [-]        name of the new project to create

    scenario             [-]        name of the baseline scenario of the
                                    project.

    occupancy-type       [-]        list of occupancy types in your building stock

    zone                 [-]        path to shapefile with geometry of zone

    district             [-]        path to shapefile with geometry of district

    streets              [-]        path to shapefile with geometry of streets

    output-path          [-]        location to where to create the new project
    ===================  =========  ==========================================

#. Click save and close the configuration editor.

Step 3. Create folder structure
-------------------------------

The objective of this step will be to create the folder structure of your project according to CEA requiremetns.
This tool will also add new input databases to your project.

#. Open Pycharm and the project City Energy Analyst.
#. From the the project tab on the left run the create new project tool. The tool is stored
   in CityEnergyAnalyst>cea>utilties>create_new_project.py.

Step 4. Create input databases
------------------------------

The objective of this step will be to create the input databases of your project and add default values to them.
In the next step you will be free to edit or replace those databases according to the real or expected values
of your project. For more information of these databases take a look to `Input databases of CEA <https://docs.google.com/presentation/d/14cgSAhNGnjTDLx_rco9mWU9FFLk0s50FBd_ud9AK7pU/edit#slide=id.g1d85a4d9be_0_0>`__.

#. Open Pycharm and the project City Energy Analyst.
#. From the the project tab on the left run the data helper tool. The tool is stored
   in CityEnergyAnalyst>cea>demand>preprocessing>data_helper.py.

Step 5. Edit/Replace input databases
-------------------------------------

Finally, the new input databases can be edited or replace to agree with the inputs your project may have.
To edit these databases check the guide on `How to edit databases in CEA <https://docs.google.com/presentation/d/16LXsu0vbllRL-in_taABuiThJ2uMP9Q05m3ORdaQrvU/edit#slide=id.gc6f73a04f_0_0>`__.

