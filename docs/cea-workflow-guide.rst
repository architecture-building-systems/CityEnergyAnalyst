:orphan:

How to run simulations in CEA
=============================

In this tutorial we will be running all scripts of CEA with the exemplary case study included along the installation




Resource potential
~~~~~~~~~~~~~~~~~~

Once a case study is created the solar radiation incident in every surface is calculated.
- run ``cea radiation``

Demand estimation
~~~~~~~~~~~~~~~~~

Calculate the demand of energy services for every building in the area.
- run ``cea demand``

Life Cycle Analysis
~~~~~~~~~~~~~~~~~~~

Calculate the emissions and primary energy needed due to the construction,
operation and dismantling of buildings in the area.

- run ``cea emissions``
- run ``cea embodied-energy``

Benchmarking
~~~~~~~~~~~~

In case you have more than one scenario inside the case study, this step calculates
targets of performance according to the 2000-Watt Society approach. The approach also
calculates the LCA of vehicles in the area.

- run ``cea mobility``
- run ``cea benchmark``

Visualization
~~~~~~~~~~~~~

There are different ways to visualize and plot all the raw data described until now.
You can either map it using ArcGIS (we expect you to know how through our user's manual),
or run the different scripts we included for this.

- for heatmaps of demand or LCA run ``cea heatmaps`` - currently, you will need ArcGIS for this.
- for plots of demand run ``cea demand-graphs``
- for plots of benchmarking run ``cea scenario plots``


|CEA workflow|


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