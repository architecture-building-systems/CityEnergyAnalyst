:orphan:

How to generate plots in CEA?
=============================

CEA includes a library to generate responsive plots. This tutorial presents how to use this library for the next
categories of plots:

- Solar_potential: Plots related to the solar isolation in buildings.


Step 1. Generate data
----------------------

The objective of this step is to make sure we have generated all raw data necessary to create the plots.
The next table presents a list of dependencies between scripts and plots in CEA. Make sure to have run each
script associated to the kind of plots you would like to generate.

===============  ==========================================
Category         Umlaut
===============  ==========================================
Solar_potential       Step 2. Analyze energy potentials

Solar_potential       Step 2. Analyze energy potentials

Solar_potential       Step 2. Analyze energy potentials
===============  ==========================================


Step 2. Configure CEA
----------------------

The objective of this step is to use the configuration editor to set up the configuration of the plots tool.

#. Open Pycharm and the project City Energy Analyst.
#. From the project tab on the left run the configuration editor of cea. The editor is stored in CityEnergyAnalyst>
   cea>interfaces>config_editor>config_editor.py.
#. This command should open a window with the configuration editor.
#. In the configuration editor, scroll down the menu on the left and click in "dashboard" tool.
#. On the right side proceed to give an input to the next variables:
    - project: give a name to the new project or case study.
    - scenario: give a name to the baseline scenario of the new project.
    - occupancy-type: Select from the list the occupancy types you will have in your buildings.
    - zone: write the path to the zone geometry file
    - terrain: write the path to the terrain file
    - output-path: location where to create the new project
#. Click save and close the configuration editor.

Step 3. Generate plots
----------------------

The objective of this step will be to create the folder structure of your project according to CEA requiremetns.
This tool will also add new input databases to your project.

#. Open Pycharm and the project City Energy Analyst.
#. From the the project tab on the left run the plots tool. The tool is stored
   in CityEnergyAnalyst>cea>plots>plots_main.py.
