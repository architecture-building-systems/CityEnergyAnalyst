Installation guide for Windows
==============================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a Windows system (tested with Windows 10).

1. `Download the latest version of CEA in here`_.
2. Open the installer and follow the instructions

.. _`Download the latest version of CEA in here`: https://cityenergyanalyst.com/tryit

.. note:: For installing the development version of CEA, tick the box "development version" during the installation.

.. note:: For previous releases check `here <https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/>`__.

.. note:: To install from the source check :doc:`here <installation/installation-on-windows-manual>`

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The pycharm interface: this interface provides access to all the source code of CEA.

The command line interface and dashboard interface are included during the installation of CEA.
Other interfaces require a few additional steps to get them up and running.

Pycharm
-------

In order to access and work on the source code of CEA from pycharm do:

#. Make sure to have installed the development version of CEA (see step 2 of the installation guide).
#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__
#. Open PyCharm from the start menu and open project CityEnergyAnalyst
   (default location is ``C:\Users\<you>\Documents\CityEnergyAnalyst\CityEnergyAnalyst``).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``System Interpreter`` from the left hand list and select existing environment.
#. Point to ``C:\Users\<you>\Documents\CityEnergyAnalyst\Dependencies\Python\python.exe``
#. Click apply changes.

.. attention:: We ended Support of Grashopper on 20.03.20. The legacy code can be found in our github repositry/legacy
.. attention:: We ended Support of ArcGIS on 15.04.19. The legacy code can be found in our github repository/legacy
