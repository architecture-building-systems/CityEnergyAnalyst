:orphan:

The main workflow of CEA
=========================

In this tutorial we will be running all scripts of CEA with the exemplary case study included along the installation.
The workflow we will be pursuing is described in the next figure:

|CEA workflow|


Step 1. Set up a case study and one scenario
---------------------------------------------

The first step consists on setting up a new case study or project for CEA to work in.
For this example we will be using the case study delivered with CEA. CEA holds a particular folder structure
in order to do calls between scripts and tools. So we recommend to keep it like that. To get the example case study
ready we will do the following steps:

#. Open Pycharm and the project City Energy Analyst.
#. From the project tab on the left copy and unzip the example case study to C:/. The file with the case study
   is stored in CityEnergyAnalyst>cea>examples>config_editor>reference-case-open.zip

In order to use a new case study of your own. Please follow the guide :doc:`new-project-guide`.

Step 2. Energy potentials
----------------------------

After setting up the case study, we will calculate the energy potentials of the case study. For this we will
run the next tools:

#. radiation
#. solar collector
#. photovoltaic
#. pVT
#. sewage
#. Visualize results in :doc:`dashboard`.

Step 3. Energy demand
----------------------

After calculating the energy potentials of the case study, we calculate the energy demand of the case study. For this we
will run the next tool:

#. Demand:
#. Visualize results in :doc:`dashboard`.

Step 4. Life Cycle Analysis
----------------------------

After calculating the energy demand of the case study and energy potentials of site, we proceed to do a life cycle
analysis of the area. For this we will run the next tools:

Calculate the emissions and primary energy needed due to the construction,
operation and dismantling of buildings in the area.

#. ``cea emissions``
#. ``cea embodied-energy``
#. ``cea operation-costs``
#. Visualize results in :doc:`dashboard`.

Step 5. Optimization
---------------------

After steps 1 and 3 we can have an idea of what is the environmental and economic impact of the case study at the
moment. This step entails the study of options to optimize the energy supply systems of the area.  For this we
will run the next tool:

#. thermal network
#. optimization
#. Visualize results in :doc:`dashboard`.


Step 6. Benchmarking
---------------------

In case you have more than one scenario inside the case study, this step calculates
targets of performance according to the 2000-Watt Society approach. The approach also
calculates the LCA of vehicles in the area.

#.``cea mobility``
#. ``cea benchmark``
#. Visualize results in :doc:`dashboard`.


.. =====================================================================================================================
.. figures and charts (GraphViz stuff)
.. =====================================================================================================================

.. |CEA workflow| digraph:: cea_workflow

    rankdir=LR;
    compound=true;
    node [shape=box];

    subgraph cluster0 {
        gather_data [shape=oval, style=dashed, label="gather data"];
        data_helper [style="dashed", label="cea data-helper"];
        label="Set up a case study";
    }
    subgraph cluster1 {
        radiation [label="cea radiation"];
        label="Resource potential";
    }
    subgraph cluster2 {
        demand [label="cea demand"];
        label="Demand estimation";
    }
    subgraph cluster3 {
        analysis_operation [label="cea emissions"];
        analysis_embodied [label="cea embodied-energy"];
        label="Life Cycle Analysis";
    }
    subgraph cluster4 {
        mobility [label="cea mobility"];
        benchmark_graphs [label="cea benchmark-graphs"];
        label="Benchmarking";
    }
    subgraph cluster5 {
        heatmaps [label="cea heatmaps"];
        benchmark_graphs [label="cea benchmark-graphs"];
        demand_graphs [label="cea demand-graphs"];
        scenario_plots [label="cea scenario-plots"];
        label="Visualization";
    }

    data_helper -> radiation [ltail=cluster0, lhead=cluster1];
    radiation -> demand [ltail=cluster1, lhead=cluster2];
    demand -> analysis_embodied [ltail=cluster2, lhead=cluster3];
    analysis_embodied -> mobility  [ltail=cluster3, lhead=cluster4];
    mobility -> heatmaps  [ltail=cluster4, lhead=cluster