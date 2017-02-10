User Interfaces
===============

The CEA code exposes multiple interfaces as an API:

-  CLI (Command Line Interface) - each module in the CEA implements a
   CLI for calling it from the command line.
-  ArcGIS - the CEA implements an ArcGIS Toolbox (in the folder
   ``cea/GUI``) to run the modules from within ArcScene 10.4
-  euler - a set of scripts for running the CEA sensitivity analysis on
   the ETH Euler cluster is provided in the folder ``euler`` and can be
   used as a starting point for running the analysis on similar clusters
   and / or linux machines.

Planned interfaces
------------------

The following interfaces are planned for the near future:

-  Rhino/Grasshopper - provide a set of components for running CEA
   modules inside Grasshopper
-  VisTrails - provide a set of VisTrails modules for running the CEA


Further ideas
-------------

Other possible interfaces include:

-  Kepler - a set of modules for the Kepler Scientific Workflow software
-  REST - a REST server for executing the CEA in the cloud
