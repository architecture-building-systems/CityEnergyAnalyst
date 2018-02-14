:orphan:

How to generate plots in CEA?
=============================

CEA includes a library to generate responsive plots. This tutorial presents how to use this library for the next
categories of plots:

    =======================  ==========================================
    Category of plots        Description
    =======================  ==========================================
    solar_potential          Plots related to the solar isolation in
                             buildings in a certain scenario

    technology_potentials    Plots related to the energy potential of
                             solar technologies in buildings in a
                             certain scenario

    energy_demand            Plots related to the energy demand of
                             buildings in a certain scenario

    optimization             Plots related to the optimization of the
                             energy system in a certain scenario

    life_cycle               Plots related to the life cycle assessment
                             of buildings in a certain scenario. This
                             includes diagrams about emissions, primary
                             energy consumption and operation costs

    scenarios_comparisons    Plots related to the comparison of energy
                             consumption, emissions and costs of
                             multiple scenarios
    =======================  ==========================================


Step 1. Generate data
----------------------

The objective of this step is to make sure we have generated all raw data necessary to create the plots.
Make sure to have run each script associated to the kind of plots you would like to generate.

Step 2. Configure CEA
----------------------

The objective of this step is to use the configuration editor to set up the configuration of the plots tool.

#. Open the configuration editor of CEA. This guide :doc:`config-file-guide` describes how to use it.
#. In the configuration editor, scroll down the menu on the left and click in "dashboard" tool.
#. On the right side proceed to give an input to the next variables:


    ===================  =========  ==================================================
    Variable             Unit       Description
    ===================  =========  ==================================================
    scenarios              [-]       list of scenarios to consider while plotting
                                     (Only applicable for scenarios_comparisons plots)


    buildings              [-]       list of buildings to consider while plotting

    categories             [-]       list of categories of plots to execute

    generations            [-]       list of generations to plot
                                     (Only applicable for optimization plots)

    individual             [-]       list of inidividuals in last generation
                                     to plot (Only applicable for optimization
                                     plots)
    ===================  =========  ==================================================

#. Click save and close the configuration editor.

Step 3. Generate plots
----------------------

The objective of this step will be to create the folder structure of your project according to CEA requiremetns.
This tool will also add new input databases to your project.

#. Open Pycharm and the project City Energy Analyst.
#. From the the project tab on the left run the plots tool. The tool is stored
   in CityEnergyAnalyst>cea>plots>plots_main.py.
