:orphan:

Installation guide for Windows
==============================

Follow these instructions to install the CEA on a Windows system (tested with Windows 10)

Prerequisites
~~~~~~~~~~~~~


* Download and install `Git (64-bit) <https://git-scm.com/download/win>`__.
* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and install `Anaconda (64-bit) for python 2.7 <https://www.anaconda.com/download/>`__.
   OR `Miniconda(64-bit) for python 2.7 <https://conda.io/miniconda.html>`__.

   .. note:: **UNCHECK** the *"Register Anaconda as my default Python 2.7"* option as ArcGIS integration
      will not work otherwise.

* Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__.
   OR your own favorite editor.
* Download and install `Daysim <https://daysim.ning.com/page/download>`__.
* Download and install `ArcGIS Desktop 10.5 or 10.6 <https://desktop.arcgis.com/en/arcmap/latest/get-started/installation-guide/introduction.htm>`_ (requires a licence).
    * An `Esri account <https://www.arcgis.com/home/signin.html>`_ must be created to buy and download ArcGIS Desktop, located in *Products: All Products*.
    * ETH affiliates are advised to access ArcGIS via the ETH IT Shop.
* Download and install the `ArcGIS Desktop Background Geoprocessing (64 Bit) <https://desktop.arcgis.com/en/arcmap/latest/analyze/executing-tools/64bit-background.htm>`_.

    .. note:: ArcGIS (with Background Geoprocessing) is required to run the thermal network layout script.
        Otherwise, ArcGIS is only used for visualisation purposes.

Installation
~~~~~~~~~~~~

#. Open GitHub Desktop from the start menu.
#. Press Ctrl+Shift+O (clone repository) and select the URL tab.
#. Paste the CEA GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Click Clone.
#. Open Anaconda prompt (terminal console) from the start menu.
#. Type ``cd Documents\GitHub\CityEnergyAnalyst`` and press ENTER.
#. Type ``conda env create`` and press ENTER.
#. Type ``activate cea`` and press ENTER.
#. Type ``pip install -e .[dev]`` and press ENTER (mind the dot '.' included in this comand!).
#. Grab a cup of tea and some toast, this will take about 45 minutes.
#. Type ``cea install-toolbox`` and press ENTER.


Configuration of Pycharm
~~~~~~~~~~~~~~~~~~~~~~~~

#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CEA (/Documents).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``Conda Environment`` from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like
   ``C:\Users\your_name\Anaconda2\envs\cea\python.exe`` or
   ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\python.exe``.
   Where 'your_name' represents your user name in windows.
#. Click apply changes.

.. note:: We advise to follow the above guide precisely. Especially the ``conda env create`` command can trip up users
    with previous experience in Anaconda / Miniconda as it looks very similar to the ``conda create`` command often
    used to create new conda environments.
    In addition to creating an environment, ``conda env create`` reads in the ``environment.yml`` file which contains a
    list of packages (and versions) to install as well as a definition of the channels to check. If you
    need to create a conda environment for the CEA that has a specific name (the default is ``cea``) then use the
    ``name`` parameter: ``conda env create --name your-env-name-here``
