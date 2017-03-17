Getting started
===============

The City Energy Analyst V1.0b is stored in a public repository in Github
under the name of
`CEAforArcGIS <https://github.com/architecture-building-systems/CEAforArcGIS>`__.

|Folder Structure|

The repository is divided in the next folder structure:

cea
~~~~
It stores the source code (human readable) of the different modules of CEA.
This is the core of CEA and is divided in the next sub-folder structure:

GUI: It stores scripts to connect CEA to the graphical user interface of ArcGIS.
analysis: It stores scripts to analyze the results of all simulations in CEA.
databases: It stores default data of weather, technology, occupancy, costs etc.,
demand: It stores scripts to calculate the demand of energy in buildings
geometry: It stores scripts to manipulate and read building geometry.
optimization: It stores scripts aiming to optimize the energy system of a district.
plots: It stores script to plot information.
resources: It stores scripts to analyze the potential of energy sources.
technologies: It stores scripts for the simulation of different technologies.
utilities: It stores functions needed by any other script frequently.

docs
~~~~
It Stores the developers manual of the CEA.

examples
~~~~~~~~
It stores an open source case study to test the cea.

bin
~~~~
It stores the compiled code (non-human readable stuff) of the different modules of the CEA.

euler
~~~~~
stores source code (human readable) needed to connect to the cluster of 50K cores called Euler at ETH Zurich
(Only researchers at ETH Zurich can use this).

setup
~~~~~
It stores data needed to install cea.

tests
~~~~~
It stores unitest data and scripts necessary ot run our automatic code checker in Github.

|CEA workflow|

The main workflow of CEA is:

Set-up a case study
~~~~~~~~~~~~~~~~~~~

If you want to run a case study different from those available in 'examples' folder.
This step entails preparing a case study to have:

1. the same folder structure as one of our case studies in the 'examples' folder.
2. the exact number, names and attributes tables of the input shapefiles.
3. the exact name and content of the digital elevation model of the terrain.

The CEA users manual includes a great deal of hints to both gather and format these data for CEA
using ArcGIS or any other geographical information system.

Resource potential
~~~~~~~~~~~~~~~~~~

Once a case study is created the solar radiation incident in every surface is calculated.
- run 'cea.resources.radiation.py'

Demand estimation
~~~~~~~~~~~~~~~~~

Once done, calculate the demand of energy services for every building in the area.
- run 'cea.demand.demand_main.py'

Life Cycle Analysis
~~~~~~~~~~~~~~~~~~~

Once done, calculate the emissions and primary energy needed due to the construction,
operation and dismantling of buildings in the area.
- run 'cea.analysis.operation.py'
- run 'cea.analysis.embodied.py'

Benchmarking
~~~~~~~~~~~~

In case you have more than one scenario inside the case study. this step calculates
targets of performance according to the 2000-Watt Society approach. The apporach also
calculates the LCA of vehicles in the area.

- run 'cea.analysis.mobility.py'
- run 'cea.analysis.benchamark.py'

Visualization
~~~~~~~~~~~~~

There are different ways to visualize and plot all the raw data described until now.
you can either Map it using ArcGIS (we expect you to know how through our users manual).
or run the different scripts we included for this.
- for heatmaps of demand or LCA run 'cea.plots.heatmaps.py' - you still will need ArcGIS for this (we are working in anther way now).
- for plots of demand           run 'cea.plots.graphs_demand.py'
- for plots of benchamrking     run 'cea.plots.scenario_plots.py'


.. |CEA workflow| digraph:: cea_workflow

    rankdir=LR;
    compound=true;
    node [shape=box];

    subgraph cluster0 {
        gather_data [shape=oval, style=dashed, label="gather data"];
        radiation [label="Radiation"];
        preprocessing [style="dashed", label="Data helper"];
        label="Preprocessing";
    }
    subgraph cluster1 {
        demand [label="Demand"];
        label="Demand Calculation";
    }
    subgraph cluster2 {
        analysis_operation [label="Emissions Operation"];
        analysis_embodied [label="Embodied Energy"];
        analysis_mobility [label="Emissions Mobility"];
        label="Analysis";
    }
    subgraph cluster3 {
        benchmark_graphs [label="Benchmark graphs"];
        demand_graphs [label="Demand graphs"];
        heatmaps [label="Heatmaps"];
        scenario_plots [label="Scenario plots"];
        label="Visualization";
    }

    radiation -> demand [ltail=cluster0, lhead=cluster1];
    demand -> analysis_embodied [ltail=cluster1, lhead=cluster2];
    analysis_embodied -> demand_graphs  [ltail=cluster2, lhead=cluster3];

