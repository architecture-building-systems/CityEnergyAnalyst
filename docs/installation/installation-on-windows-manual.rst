:orphan:

Installation guide for Windows for developers
==============================================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a Windows system (tested with Windows 10) for developers

Prerequisites
~~~~~~~~~~~~~
* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and Install `Mamba <https://mamba.readthedocs.io/en/latest/installation.html>`__.
* Download and Install `Yarn <https://github.com/yarnpkg/yarn/releases/download/v1.22.4/yarn-1.22.4.msi>`__.

Installation
~~~~~~~~~~~~

#. Open GitHub Desktop from the start menu.
#. Clone the CEA repository: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Clone the CEA GUI repository: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
#. Install CEA backend:
    #. Open a Terminal console
    #. Type ``cd Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``CONDA_SUBDIR=osx-64 mamba env create -f environment.yml`` and press ENTER.
    #. Type ``mamba activate cea`` and press ENTER.
    #. Type ``pip install -e .`` and press ENTER *(mind the dot '.'!)*.
#. Build the CEA dashboard:
    #. Type ``cd ..`` and press ENTER, then type ``cd CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn package`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-*``

Running the CEA dashboard
_________________________

In order to launch the CEA dashboard, you will need to do the following **each time**:

#. Open the Terminal
#. Type ``conda activate cea`` and press ENTER.
#. Type ``cea dashboard`` and press ENTER.
#. Wait for ``start socketio.run`` to appear (This might 3 min the first time)
#. Run the CEA dashboard located in (``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-*``).

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

