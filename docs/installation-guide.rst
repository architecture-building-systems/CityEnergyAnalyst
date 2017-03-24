Installation guide
==================

The version |version| of the City Energy Analyst is dependent on ArcGIS 10.4
for its visuals. As such it is restricted to Windows-based OS's for some features.


Installation on Windows
-----------------------

Installing the CEA on Windows is easiest with Anaconda_ (or Miniconda_) as the CEA depends on the geopandas_ module.

.. _Anaconda: https://www.continuum.io/downloads
.. _Miniconda: https://conda.io/miniconda.html
.. _geopandas: https://github.com/geopandas/geopandas

Installation follows the following basic steps:

#. create a conda environment and activate it (optional)
#. ``conda install -c conda-forge geopandas``
#. ``pip install cityenergyanalyst``
#. ``cea install-toolbox`` (installs the CEA as an ArcGIS 10.4 toolbox)


Creating a conda environment
............................

Creating a conda environment is an optional step, but probably a good habit to get into: This creates a python
environment separate from your other python environments - that way, version mismatches between packages don't bleed
into your other work. Follow these steps to create a new conda environment for the CEA:

#. ``conda create -n cea python=2.7`` (you can use any name, when creating an environment - "cea" is just an example)
#. ``activate cea`` (do this before any cea-related work on the commandline)
#. work with CEA, python is now set up to use your conda environment
#. ``deactivate cea`` (you can also just close the shell)


Connecting to Arcpy
...................

The command ``cea install-toolbox`` attempts to connect the CEA with the ArcGIS environment. You should not need to
do anything else.

If, however, you get error messages like ``ImportError: no module named arcpy`` you can check your home directory
for a file called ``cea_arcgis.pth`` containing these three lines::

    C:\Program Files (x86)\ArcGIS\Desktop10.4\bin
    C:\Program Files (x86)\ArcGIS\Desktop10.4\arcpy
    C:\Program Files (x86)\ArcGIS\Desktop10.4\Scripts

Edit these folders to point to the appropriate ArcGIS folders as documented in the ArcGIS manuals.

Installation of the development environment
-------------------------------------------

When installing the City Energy Analyst for development, clone the repository to your computer and run::

    python setup.py develop

This will install the ``cea`` tool to your path and set it up to use the version in the repository. Note, you will need
to follow the guide above to create a conda environment and install geopandas.

Recommended software
....................

-  GitHub Desktop (or your favorite ``git``)
-  Anaconda distribution (x86) - other pythons can work, but this is really recommended
-  PyCharm community edition - you can use your own favorite editor, but this is what we use
-  Git Large File Storage - only for working with the reference case repository (you need to be a core developer to
   have access to the private reference case repository)

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

#. Click apply changes and your are done!

To set the custom dictionary used in PyCharm, do:

#. Open File>Settings>Editor>Spelling

#. Open the Dictionaries tab

#. Add a new Custom Dictionaries Folder

#. Select the root source folder for CEAforArcGIS. It should be located
   in something like
   ``C:\Users\your_name\Documents\GitHub\CEAforArcGIS``.

#. Click "Apply".

Installation on the Euler cluster
---------------------------------

It is possible to install the CEA on the Euler_ cluster by following the following guide:
:doc:`installation-on-euler`.

.. _Euler: https://www.ethz.ch/services/en/it-services/catalogue/server-cluster/hpc.html

