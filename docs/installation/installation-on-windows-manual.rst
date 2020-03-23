:orphan:

Installation guide for Windows (from the source)
=================================================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a Windows system (tested with Windows 10) from the source

.. attention:: We advise to follow the above guide precisely:

        *   Be sure to **USE** ``conda env create`` **NOT** ``conda create`` familiar to experienced conda users.
            This command not only creates an environment, but also reads the ``environment.yml`` file, containing a
            list of packages (and versions) to install, as well as a definition of the channels to check.
        *   If you need to create a conda environment for the CEA that has a specific name (the default is ``cea``) then use the
            ``name`` parameter: ``conda env create --name your-env-name-here``


Prerequisites
~~~~~~~~~~~~~

* Download and install `Git (64-bit) <https://git-scm.com/download/win>`__.
* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and install `DAYSIM version >= 4.0 <https://daysim.ning.com/page/download>`__.
* Download and install `Miniconda(64-bit) for Python 2.7 <https://conda.io/miniconda.html>`__.
   .. note:: UNCHECK the "Register Anaconda as my default Python 2.7" option as ArcGIS integration
      will not work otherwise.

Installation of the code base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Excluding the above software, CEA installation requires approximately 13 GB of storage (depending on your existing
Python library) and  1 hour of your time.

#. Open GitHub Desktop from the start menu.
#. Press Ctrl+Shift+O (clone repository) and select the URL tab.
#. Paste the CEA GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Click Clone, this will take ~ 5 -10 minutes (Size 900MB).
#. Open Anaconda prompt (terminal console) from the start menu.
#. Type ``cd Documents\GitHub\CityEnergyAnalyst`` and press ENTER.
#. Type ``conda env create`` and press ENTER.
#. Grab a cup of tea and some toast, this will take ~ 45 minutes.
#. Type ``activate cea`` and press ENTER.
#. Type ``pip install -e .[dev]`` and press ENTER (mind the dot '.' included in this command!).

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The pycharm interface: this interface provides access to all the source code of CEA.

While the command line interface, and dashboard interface are included during the installation of CEA, the rest of the interfaces
require a few steps to get them up and running.

Pycharm
-------

In order to access and work on the source code of CEA from pycharm do:

#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__ OR your own favorite editor.
#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CityEnergyAnalyst).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``Conda Environment`` from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like
   ``C:\Users\your_name\Miniconda2\envs\cea\python.exe`` or
   ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\python.exe``.
   Where 'your_name' represents your user name in windows.
#. Click apply changes.

.. attention:: We ended Support of Grashopper on 20.03.20. The legacy code can be found in our github repositry/legacy
.. attention:: We ended Support of ArcGIS on 15.04.19. The legacy code can be found in our github repository/legacy

