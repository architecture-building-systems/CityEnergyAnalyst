:orphan:

Installation guide on Windows for developers
==============================================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a Windows system (tested with Windows 10) for developers

Prerequisites
~~~~~~~~~~~~~
* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and Install `Micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`__.

Installation
~~~~~~~~~~~~

#. Open GitHub Desktop from the start menu.
#. Clone the CEA repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Clone the CEA GUI repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
#. Install CEA backend:
    #. Open a Powershell console (you can search for it in your start menu)
    #. Type ``cd Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``micromamba env remove -n cea`` and press ENTER.
    #. Type ``micromamba env create -n cea -f conda-lock.yml`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``pip install -e .`` and press ENTER *(mind the dot '.'!)*.
#. Build the CEA dashboard:
    #. Type ``cd ..`` and press ENTER, then type ``cd CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn electron:build`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/win-unpacked/CityEnergyAnalyst-GUI.exe``

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The Miniforge Prompt console interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The pycharm interface: this interface provides access to all the source code of CEA.

The command line interface and dashboard interface are included during the installation of CEA.
Other interfaces require a few additional steps to get them up and running.

Running the CEA dashboard
_________________________

In order to launch the CEA dashboard, you will need to do the following **each time**:

#. Open the Miniforge Prompt console (you find it in your start menu)
#. Type ``mamba activate cea`` and press ENTER.
#. Type ``cea dashboard`` and press ENTER.
#. Wait for ``start socketio.run`` to appear (This might 3 min the first time)
#. Run the CEA dashboard located in (``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/win-unpacked/CityEnergyAnalyst-GUI.exe``).

Here you can find a series of `blog posts <https://cityenergyanalyst.com/blogs>`_ to help you get started!

Running CEA on Pycharm
______________________

In order to access and work on the source code of CEA from pycharm do:

#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__ OR your own favorite editor.
#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CityEnergyAnalyst).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``Conda Environment`` from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like
   ``C:\Users\your_name\mamba\envs\cea\python.exe`` or
   ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\python.exe``.
   Where 'your_name' represents your user name in windows.
#. Click apply changes.

.. attention:: We ended Support of Grashopper on 20.03.20. The legacy code can be found in our github repository/legacy
.. attention:: We ended Support of ArcGIS on 15.04.19. The legacy code can be found in our github repository/legacy

Updating dependencies
~~~~~~~~~~~~

