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
-------------------

If you would like to be able to access the ``arcpy`` module from the
``esri104`` Anaconda python environment, create a file called
``arcpy.pth`` in
``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages`` with the
following contents:

.. code::

    C:\Program Files (x86)\ArcGIS\Desktop10.4\bin
    C:\Program Files (x86)\ArcGIS\Desktop10.4\arcpy
    C:\Program Files (x86)\ArcGIS\Desktop10.4\Scripts

Configure your python console
-----------------------------

Whatever console you like, you will need to configure it to call the
environment esri104 created in Anaconda.

The developing team uses Pycharm Community edition as default. Here are
the instructions for get pycharm up and running.

#. Access PyCharm and open project CEAforArcGIS

#. Open File>Settings>Project:CEAforArcGIS>Project Interpreter>Project
   Interpreter

#. Click on settings>addlocal and point to the location of your python
   installation in the environment esri104. It should be located in
   something like
   ``C:\Users\your_name\Anaconda2\envs\esri104/python.exe``

#. Click apply changes and your are done!

To set the custom dictionary used in PyCharm, do:

#. Open File>Settings>Editor>Spelling

#. Open the Dictionaries tab

#. Add a new Custom Dictionaries Folder

#. Select the root source folder for CEAforArcGIS. It should be located
   in something like
   ``C:\Users\your_name\Documents\GitHub\CEAforArcGIS``.

#. Click "Apply".

Installation of the development environment
-------------------------------------------

**Software to be Downloaded**

-  GitHub Desktop
-  Anaconda distribution (x86)
-  Pycharm community edition
-  VCredist SP1 (x86)
-  Git Large File Storage

Installation on the Euler cluster
---------------------------------

It is possible to install the CEA on the Euler_ cluster by following the following guide:
:doc:`installation-on-euler`.

.. _Euler: https://www.ethz.ch/services/en/it-services/catalogue/server-cluster/hpc.html

