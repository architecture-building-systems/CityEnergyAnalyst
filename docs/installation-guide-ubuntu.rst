:orphan:

Installation guide for Ubuntu
=============================

Follow these instructions to install the CEA on a Linux system (feedback on these steps are welcome, they are based
on experiences writing a Dockerfile and there might be some updates for actually installing on a Desktop system)

Prerequisites
~~~~~~~~~~~~~

#. Anaconda2 or Miniconda2

  - ``curl -O https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh``
  - ``bash Miniconda2-latest-Linux-x86_64.sh`` (defaults are fine)

#. git

  - ``apt-get install git``

#. Download and install `Daysim <https://daysim.ning.com/page/download>`__.
  - ``git clone https://github.com/MITSustainableDesignLab/Daysim.git``
  - ``mkdir build``
  - ``cd build``
  - (if you don't have cmake installed, you can use ``apt-get install cmake`` to install it. Other packages that might
    be of interest are: ``apt-get install build-essential libgl1-mesa-dev freeglut3-dev`)
  - ``cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && make install``
  - copy the ``CMakeLists.txt`` file from the ``docker`` folder in the CityEnergyAnalyst
    repository (see below) to the Daysim repository and run
  - (from the ``build`` directory created above)
  - ``cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim``
  - ``make && mv ./bin/rtrace ./bin/rtrace_dc && cp ./bin/* $HOME/Daysim/bin``
  - Daysim is now installed in the folder ``~/Daysim/bin``

Installation
~~~~~~~~~~~~

This guide walks you through the steps of installing the CEA on Ubuntu 16. Start by opening a terminal and navigating
to a folder to use for the installation. In this guide, we assume you are using ``~/tmp`` and starting out in your
home directory (``~``):

- create a folder for working in: ``mkdir tmp``
- navigate to that folder: ``cd tmp``
- clone the CEA repository: ``git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
- navigate to the repository folder: ``cd CityEnergyAnalyst``
- create the conda environment: ``conda env create --file environment.ubuntu.yml``
- activate the conda environment: ``source activate cea``
- install the CEA to the conda environment: ``pip install -e .``
- test the CEA: ``cea test``

