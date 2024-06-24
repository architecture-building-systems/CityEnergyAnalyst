Installation guide for Windows
==============================

Step 1: Determine the interface that you want to interact with CEA.
~~~~~~~~~~

There mainly 3 ways or interfaces.

#. CEA Dashboard: This a graphical user interface to CEA, open source and developed by the CEA Team using web-based technology.
#. CEA Command Line: This is the command line to all the commands of CEA from your computer terminal.
#. The Pycharm Interface: this interface provides access to all the source code of CEA.

Install CEA Developer Version if you intend to use the Pycharm Interface. CEA Developer Version also includes CEA Dashboard and CEA Command Line


Step 2: Download and install CEA.
~~~~~~~~~~
Follow these instructions to install CEA on a Windows system (tested with Windows 10).

#. `Download the latest version of CEA in here`_.
#. Open the installer and follow the instructions
#. For installing CEA Developer Version, tick the box "Developer Version" during the installation.

.. _`Download the latest version of CEA in here`: https://www.cityenergyanalyst.com/#downloads

.. note:: For previous releases check `here <https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/>`__.
.. note:: (not recommended) Alternatively, you can install CEA from the source check :doc:`installation-on-windows-manual`


Step 3: Run CEA Dashboard.
~~~~~~~~~~

#. Locate the CEA icon (usually on desktop) and double click on it
#. Start using CEA Dashboard

Here you can find a series of tutorials at `CEA Learning Camp <https://www.cityenergyanalyst.com/learning-camp>`__ to help you get started!


Step 4 (Developer Version): Access CEA using the Pycharm Interface.
~~~~~~~~~~

In order to access and work on the source code of CEA from pycharm, do:

#. Make sure to have installed CEA Developer Version (see step 2 of the installation guide).
#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__
#. Open PyCharm from the start menu and open project CityEnergyAnalyst
   (default location is ``C:\Users\<you>\Documents\CityEnergyAnalyst\CityEnergyAnalyst``).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``System Interpreter`` from the left hand list and select existing environment.
#. Point to ``C:\Users\<you>\Documents\CityEnergyAnalyst\Dependencies\Python\python.exe``
#. Click apply changes.


.. attention:: We ended Support of Grasshopper on 20.03.20. The legacy code can be found in our github repository/legacy.
As of 24.06.2024, you may export and load your Grasshopper geometries into CEA using a provisional link explained
in this `CEA Lesson <https://www.cityenergyanalyst.com/learning-camp/cea-s-01-from-grasshopper-to-cea-dashboard>`__.

.. attention:: We ended Support of ArcGIS on 15.04.19. The legacy code can be found in our github repository/legacy
