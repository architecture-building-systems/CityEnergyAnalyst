Installation guide
==================

This guide covers the main steps of installing the City Energy Analyst version |version| for research.
It also includes a guide to connect to our development environment and to the Euler cluster of ETH Zurich (only of ETH zurich affiliates).

Prerequisites
-------------

-  GitHub Desktop (or your favorite ``git``)
-  Anaconda distribution (x86) - other pythons can work, but this is really recommended
-  PyCharm community edition - you can use your own favorite editor, but this is what we use
-  ArcGIS 10.4 - only if you would like to use ArcGIS visuals.
-  Git Large File Storage - only for working with the reference case repository (you need to be a core developer to
   have access to the private reference case repository)

Installation CEA research
-------------------------

To install the research version of CEA:

#. open Anaconda prompt (terminal console) from the start menu.
#. create a conda environment and activate it: do ``conda create -n cea python=2.7``, do ``activate cea``
#. install dependencies: do ``conda install -c conda-forge geopandas ephem``
#. install cea: do ``pip install cityenergyanalyst``
#. install arcgis plug-in: do ``cea install-toolbox``

Note: Creating a conda environment is an optional step, but probably a good habit to get into: This creates a python
environment separate from your other python environments - that way, version mismatches between packages don't bleed
into your other work. (you can use any name, when creating an environment - "cea" is just an example)

Installation CEA development environment
----------------------------------------

To install the development environment of CEA:

#. open Anaconda prompt (terminal console) from the start menu.
#. create a conda environment and activate it. do ``conda create -n cea python=2.7``, do ``activate cea``
#. choose location where to store the repository: do ``cd Documents``
#. clone repository: do ``git clone https://github.com/architecture-building-systems/CEAforArcGIS.git``
#. go to location where the repository was cloned: do ``cd CEAforArcGIS``
#. install dependencies: do ``conda install -c conda-forge geopandas ephem``
#. install dependencies: do ``conda install -c dlr-sc tbb freeimageplus gl2ps``
#. install dependencies: do ``conda install -c oce -c pythonocc pythonocc-core=0.17.3``
#. install cea development: do ``python setup.py install``
#. set-up path to repository: do ``python setup.py develop``
#. download and install Daysim: ``http://daysim.ning.com/page/download``


Note: Creating a conda environment is an optional step, but probably a good habit to get into: This creates a python
environment separate from your other python environments - that way, version mismatches between packages don't bleed
into your other work. (you can use any name, when creating an environment - "cea" is just an example)

Note: Location where to store the repository can be any -"Documents" is just an example.

Setting up PyCharm
..................

The developer team uses PyCharm Community edition as default. Here are
the instructions to get PyCharm up and running:

#. Access PyCharm and open project CEAforArcGIS

#. Open File>Settings>Project:CEAforArcGIS>Project Interpreter>Project
   Interpreter

#. Click on settings>addlocal and point to the location of your python
   installation in the environment ``cea``. It should be located in
   something like
   ``C:\Users\your_name\Anaconda2\envs\cea/python.exe``

#. Click apply changes.

#. Now add your conda environment ``C:\Users\your_name\Anaconda2\envs\cea``
to your environment variable ``PATH``. The environment variable is located
under Environment Variables in the tab Advanced in System Properties in the Control Panel.

#. Restart PyCharm if open.

To set the custom dictionary used in PyCharm, do:

#. Open File>Settings>Editor>Spelling

#. Open the Dictionaries tab

#. Add a new Custom Dictionaries Folder

#. Select the root source folder for CEAforArcGIS. It should be located
   in something like
   ``C:\Users\your_name\Documents\GitHub\CEAforArcGIS``.

#. Click "Apply".


Connecting to Arcpy
-------------------

the step ``cea install-toolbox`` (see step 4 in the basic installation steps above) attempts to connect the CEA with
the ArcGIS environment. You should not need to do anything else. If, however, you get error messages like
``ImportError: no module named arcpy`` you can check your home directory
for a file called ``cea_arcgis.pth`` containing these three lines::

    C:\Program Files (x86)\ArcGIS\Desktop10.4\bin
    C:\Program Files (x86)\ArcGIS\Desktop10.4\arcpy
    C:\Program Files (x86)\ArcGIS\Desktop10.4\Scripts

Edit these folders to point to the appropriate ArcGIS folders as documented in the ArcGIS manuals.

Installation on the Euler cluster
---------------------------------

It is possible to install the CEA on the Euler_ cluster by following the following guide:
:doc:`installation-on-euler`.


.. _Euler: https://www.ethz.ch/services/en/it-services/catalogue/server-cluster/hpc.html
.. _Anaconda: https://www.continuum.io/downloads
.. _Miniconda: https://conda.io/miniconda.html
.. _geopandas: https://github.com/geopandas/geopandas
