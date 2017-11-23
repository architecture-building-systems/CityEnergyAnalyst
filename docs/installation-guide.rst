Installation guide
==================

This guide covers the main steps of installing the City Energy Analyst version |version| for research.
It also includes a guide to connect to our development environment and to the Euler cluster of ETH Zurich (only of ETH zurich affiliates).

Prerequisites
-------------

-  GitHub Desktop (or your favorite ``git``)
-  Anaconda distribution (64-bit) - other pythons can work, but this is really recommended
   - alternatively, Miniconda2 64-bit will also work!
-  PyCharm community edition - you can use your own favorite editor, but this is what we use
-  ArcGIS 10.5 - only if you would like to use ArcGIS visuals.
-  Git Large File Storage - only for working with the reference case repository (you need to be a core developer to
   have access to the private reference case repository)

Installation CEA research
-------------------------

To install the research version of CEA:

#. open Anaconda prompt (terminal console) from the start menu.
#. choose location where to store the repository: do ``cd Documents``
#. clone repository: do ``git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
#. in the Anaconda prompt navigate to the folder CityEnergyAnalyst wherever you cloned it. In this case do:
   ``cd Documents\CityEnergyAnalyst``
#. create a conda environment and activate it: do ``conda env create``, then do ``activate cea``
#. install cea: do ``pip install .``
#. install arcgis plug-in: do ``cea install-toolbox``

  - this also installs the user configuration file (``cea.config``, located in your home folder)
  - this also extracts the reference case (reference-case-open) to the temporary folder
    (``%TEMP%\reference-case-open\baseline``) for test-driving the CEA

#. edit the file ``%USERPROFILE%\cea.config`` (normally something like ``C:\Users\USERNAME\cea.config``) and
   set the ``default-scenario`` property of yours.

.. note:: We advise to follow the above guide precisely. Especially the ``conda env create`` command can trip up users
    with previous experience in Anaconda / Miniconda as it looks very similar to the ``conda create`` command often
    used to create new conda environments.
    In addition to creating an environment, ``conda env create`` reads in the ``environment.yml`` file which contains a
    list of packages (and versions) to install as well as a definition of the channels to check. If you
    need to create a conda environment for the CEA that has a specific name (the default is ``cea``) then use the
    ``name`` parameter: ``conda env create --name your-env-name-here``

Installation CEA development environment
----------------------------------------

To install the development environment of CEA, perform the steps above, except, instead of ``pip install .``:

#. do ``pip install -e .[dev]``
#. download and install Daysim: ``http://daysim.ning.com/page/download``

.. note:: The location to store the repository can be any - "Documents" is just an example.

.. note:: If after the installation you experience an error concerning geopandas or fiona, i.e.,
    ``ImportError: DLL load failed: The specified module could not be found.``
    Try copying ``C:\Users\your_name\Anaconda2\envs\cea\proj.dll`` OR ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\proj.dll`` to
    ``C:\Users\your_name\Anaconda2\envs\cea\Library\bin`` OR ``C:\Users\your_name\AppData\Local\conda\conda\envs\Library\bin`` and CEA should run.

Setting up PyCharm
..................

The developer team uses PyCharm Community edition as default. Here are
the instructions to get PyCharm up and running:

#. Access PyCharm and open project CityEnergyAnalyst

#. Open File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project
   Interpreter

#. Click on settings>addlocal and point to the location of your python
   installation in the environment ``cea``. It should be located in
   something like
   ``C:\Users\your_name\Anaconda2\envs\cea\python.exe`` or ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\python.exe``


#. Click apply changes.

#. Now add your conda environment ``C:\Users\your_name\Anaconda2\envs\cea``
   to your environment variable ``PATH``. The environment variable is located
   under Environment Variables in the tab Advanced in System Properties in the Control Panel.

#. Restart PyCharm if open.

To set the custom dictionary used in PyCharm, do:

#. Open File>Settings>Editor>Spelling

#. Open the Dictionaries tab

#. Add a new Custom Dictionaries Folder

#. Select the root source folder for CityEnergyAnalyst. It should be located
   in something like
   ``C:\Users\your_name\Documents\GitHub\CityEnergyAnalyst``.

#. Click "Apply".


Connecting to Arcpy
-------------------

the step ``cea install-toolbox`` (see step 4 in the basic installation steps above) attempts to connect the CEA with
the ArcGIS environment. You should not need to do anything else. If, however, you get error messages like
``ImportError: no module named arcpy`` you can check your home directory
for a file called ``cea_arcgis.pth`` containing these three lines::

    C:\Program Files (x86)\ArcGIS\Desktop10.5\bin64
    C:\Program Files (x86)\ArcGIS\Desktop10.5\arcpy
    C:\Program Files (x86)\ArcGIS\Desktop10.5\Scripts

Edit these folders to point to the appropriate ArcGIS folders as documented in the ArcGIS manuals.

Installation on the Euler cluster
---------------------------------

It is possible to install the CEA on the Euler_ cluster by following the following guide:
:doc:`installation-on-euler`.


.. _Euler: https://www.ethz.ch/services/en/it-services/catalogue/server-cluster/hpc.html
.. _Anaconda: https://www.continuum.io/downloads
.. _Miniconda: https://conda.io/miniconda.html
.. _geopandas: https://github.com/geopandas/geopandas
