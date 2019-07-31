:orphan:

Installation guide for macOS
============================

Follow these instructions to install the CityEnergyAnalyst (CEA) on a macOS system (tested with Mojave 10.14.5) from the source

Prerequisites
~~~~~~~~~~~~~

* Download and install `Git`_ (64-bit).
* Download and install `GitHub Desktop`_ (64-bit).

  * (this is not strictly necessary, but we find it easier for novice git users)

* Download and install `Miniconda`_ (64-bit) for Python 2.7.

  * (the Mac OS X 64-bit `.pkg installer`_ is probably the easiest way to install Miniconda on your Mac)

* Download and install `CMake`_.

  * (CMake is required for compiling DAYSIM)
  * (this guide assumes you installed CMake to ``/Applications/CMake`` or have it in your PATH)

* Install DAYSIM version >= 4.0: Open Terminal and run the following commands

  - ``git clone https://github.com/MITSustainableDesignLab/Daysim.git``
  - ``mkdir build && cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && make install``
  - ``cp ./CMakeLists.txt /Daysim/CMakeLists.txt``
  - ``cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && mv ./bin/rtrace ./bin/rtrace_dc && cp ./bin/* /root/Daysim/bin``
  - ``export PATH="path_to_cea_env:path_to_daysim_bin:$PATH"`` where ‘path_to_cea_env‘ is the path to the CEA conda environment (it should look something like ``\Users\your_name\Miniconda2\envs\cea\bin`` where ‘your_name‘ represents your user name on your Mac) and ‘path_to_daysim_bin‘ is the path to the Daysim bin folder (it should look something like ``\Users\your_name\Daysim\bin``).

.. _`Git`: https://www.atlassian.com/git/tutorials/install-git
.. _`GitHub Desktop`: https://desktop.github.com/
.. _`Miniconda`: https://docs.conda.io/en/latest/miniconda.html
.. _`.pkg installer`: https://repo.anaconda.com/miniconda/Miniconda2-latest-MacOSX-x86_64.pkg
.. _`CMake`: https://cmake.org/download/

Installation of the code base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Excluding the above software, CEA installation requires approximately 13 GB of storage (depending on your existing Python library) and 1 hour of your time.

#. Open "GitHub Desktop".
#. Press Command+Shift+O (clone repository) and select the URL tab.
#. Paste the CEA GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Click Clone, this will take ~ 5-10 minutes (Size 900MB). (this guide assumes you cloned to the default
  folder ``~/Documents/GitHub/CityEnergyAnalyst``).
#. Open the Terminal app.
#. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
#. Type ``conda env create -f environment.osx.yml`` and press ENTER.
#. Type ``conda activate cea`` and press ENTER.
#. Type ``pip install -e .`` and press ENTER (mind the dot ‘.’ included in this command!).
#. IMPORTANT: Due to how Mac OS X works, the version of python installed by conda will not work with matplotlib and
   other libraries that require access to the graphics system. You need to edit the ``cea`` script - run ``which cea``
   to find the exact path, it was ``/miniconda2/envs/cea/bin/cea`` on my system after installing using the above steps.
   The first line (``#!/miniconda2/envs/cea/bin/python``) needs to be changed to ``#!/usr/bin/env pythonw``).
#. (optional) Type ``cea test`` to run a basic test of the functionality

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

