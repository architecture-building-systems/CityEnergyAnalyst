:orphan:

Installation guide for macOS
============================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a macOS system (tested with Mojave 10.14.5) from the source

Prerequisites
~~~~~~~~~~~~~

* Download and install Git (64-bit).
* Download and install Github Desktop (64-bit).
* Download and install Miniconda(64-bit) for Python 2.7.
* Download and install CMake.
* Install DAYSIM version >= 4.0: Open Terminal and run the following commands

  - ``git clone https://github.com/MITSustainableDesignLab/Daysim.git``
  - ``mkdir build && cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && make install``
  - ``cp ./CMakeLists.txt /Daysim/CMakeLists.txt``
  - ``cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && mv ./bin/rtrace ./bin/rtrace_dc && cp ./bin/* /root/Daysim/bin``
  - ``export PATH="path_to_cea_env:path_to_daysim_bin:$PATH"`` where ‘path_to_cea_env‘ is the path to the CEA conda environment (it should look something like ``\Users\your_name\Miniconda2\envs\cea\bin`` where ‘your_name‘ represents your user name on your Mac) and ‘path_to_daysim_bin‘ is the path to the Daysim bin folder (it should look something like ``\Users\your_name\Daysim\bin``).

Installation of the code base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Excluding the above software, CEA installation requires approximately 13 GB of storage (depending on your existing Python library) and 1 hour of your time.

#. Open GitHub Desktop from the start menu.
#. Press Command+Shift+O (clone repository) and select the URL tab.
#. Paste the CEA GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Click Clone, this will take ~ 5 -10 minutes (Size 900MB).
#. Open Anaconda prompt (terminal console) from the start menu.
#. Type ``cd Documents\GitHub\CityEnergyAnalyst`` and press ENTER.
#. Type ``conda env create`` and press ENTER.
#. Type ``conda activate cea`` and press ENTER.
#. Type ``pip install -e .[dev]`` and press ENTER (mind the dot ‘.’ included in this command!).

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA. As of now, the CEA dashboard does not work on macOS, however the following interfaces are included:

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal.
#. The PyCharm interface: this interface provides access to all the source code of CEA.

While the command line interface is included during the installation of CEA, the PyCharm interface requires a few steps to get up and running.

PyCharm
-------

In order to access and work on the source code of CEA from PyCharm do:

#. Download and install PyCharm Community edition (64-bit) OR your own favorite editor.
#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CityEnergyAnalyst).
#. Open ``Preferences>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add Local.
#. Click Conda Environment from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like 
   ``\Users\your_name\Miniconda2\envs\cea\bin\python``
   where ‘your_name’ represents your user name on your Mac.
#. Click apply changes.

