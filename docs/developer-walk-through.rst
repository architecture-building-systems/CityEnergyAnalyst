Developer Walk-through
======================

.. toctree::
   :maxdepth: 2
   :caption: Contents

   how-to-add-a-new-script-to-the-cea
   configuration-file-details


Architecture
------------

The architecture of the CEA is still a bit in flux, but some main
components have already been developed and will be explained in this
chapter. The following figure shows a high-level view of the main
components of the CEA:

|CEA architecture objects|

Demand calculation
~~~~~~~~~~~~~~~~~~

At the core of the CEA is the demand calculation. The demand calculation
retrieves inputs from the scenario folder and stores outputs back to the
scenario folder. A preprocessing step can be used to add archetype data
to a scenario as a first guess of certain parameters.

The demand calculation uses a special variable called ``tsd`` to store
information about the timestep data during the calculation of thermal
loads for each building. The data structure used is a simple python
dictionary of NumPy arrays. Each of these arrays has the length 8760, to
total number of hours of the year. The keys of the ``tsd`` dictionary
are the names of the state variables of the simulation.

The demand calculation also uses a variable ``bpr`` to store building
properties of a single building.

InputLocator
~~~~~~~~~~~~

The ``cea.inputlocator.InputLocator`` class encapsulates the code for
creating paths for input and output to the archetypes and the contents
of the scenario (input and output files). An instance of this class is
found in most of the code and is always named ``locator``, unless
multiple ``InputLocator`` objects are used, e.g. for comparing
scenarios.

Each method of the ``locator`` starts with ``get_*`` and returns a
string containing the full path to the resource requested. These
``get_*`` methods should be the only way to obtain file- and folder
names in the CEA - files and folders should especially not be
concatenated with strings and backslashes (``\``). Instead, new paths
should be introduced as methods of the ``InputLocator`` class.

One of the main benefits of doing this is that it makes documentation of
what files are read / written by what module of the CEA easier. The
``funcionlogger`` module can be used to trace these calls for generating
documentation.

The private method ``_ensure_folder(*paths)`` is used to join path
components and at the same time ensure that the folders are present in
the scenario folder, creating them with ``os.makedirs`` if necessary.

**NOTE**: The list of ``get_*`` methods is getting very long. We might
end up creating a namespace hierarchy for grouping related paths
together.

Analysis and Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Separate modules exist for analyzing different aspects of a scenario.
Some of the analysis modules operate only on the input data (LCA for
embedded emissions, mobility) and others operate on the output of the
demand module (LCA for emissions due to operation). These modules are
grouped in the folder ``cea/analysis``.

The folder ``cea/plots`` contains modules for plotting outputs of the
calculations.

"Higher order" modules
~~~~~~~~~~~~~~~~~~~~~~

Some of the modules in the CEA use the demand calculation to calculate
variants of a scenario. This includes the sensitivity analysis, the
calibration and the network optimization code. All these modules call
the demand calculation as part of their process.

.. |CEA architecture objects| digraph:: cea_objects

    node [shape=box, fontname="Helvetica"];

    demand [label="Demand calculation", style="filled"];
    sensitivity [label="Sensitivity Analysis"];
    calibration [label="Transient Bayesian Calibration"];
    optimization [label="Network Optimization"];
    analysis [label="Mobility / Life Cycle Analysis"];
    plots [label="Data Visualization"];

    {
        node [style="dashed"];
        rank=same;
        bpr [label="bpr (BuildingPropertiesRow)"];
        tsd [label="tsd (timestep data)"];
        locator [label="locator (InputLocator)", style="filled"];
    }

    db [label="db (Archetypes)", shape="folder"];
    scenario [label="Case Study (scenario)", shape="folder"];

    locator -> bpr;
    locator -> scenario [label="  read / write"];
    locator -> db [label="  write"];

    {rank=same; demand; analysis; plots; }
    {rank=same; db; scenario; }

    demand -> locator;
    demand -> tsd;
    demand -> bpr;
    analysis -> locator;
    plots -> locator;
    sensitivity -> demand;
    calibration -> demand;
    optimization -> demand;

    db -> scenario [label="  preprocessing  "];

