:orphan:

Installation guide for Ubuntu
=============================

Follow these instructions to install the CEA on a Linux system (tested on Ubuntu 18.04.2 LTS with minimal installation
configuration)

Prerequisites
~~~~~~~~~~~~~

#. Anaconda2 or Miniconda2

  - ``mkdir tmp``
  - ``cd tmp``
    - all further prerequisiste installation assumes you're in the folder ``~/tmp``
  - ``curl -O https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh``
    - if curl is not installed, try ``sudo apt-get install curl``
  - ``bash Miniconda2-latest-Linux-x86_64.sh`` (defaults are fine)

#. git

  - ``sudo apt-get update``
    - (updates the list of packages known to apt-get)
  - ``sudo apt-get install git``

#. Download and install `Daysim <https://daysim.ning.com/page/download>`__.

  - ``git clone https://github.com/MITSustainableDesignLab/Daysim.git``
  - ``mkdir build``
  - ``cd build``
  - if you don't have cmake installed, you can use ``sudo apt-get install cmake`` to install it.

    - Other packages that are missing in minimal setup of Ubuntu and need to be installedwith apt-get are:

      - ``sudo apt-get install build-essential`` (for error "No CMAKE_CXX_Compiler could be found.")
      - ``sudo apt-get install libgl1-mesa-dev`` (for error "Could NOT find OpenGL")
      - ``sudo apt-get install freeglut3-dev`` (for error "GL/glu.h: No such file or directory" while running ``make`` below)

  - ``cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim``
  - ``make``
  - ``make install``
  - open the file ``~/tmp/Daysim/CMakeLists.txt`` in your favorite text editor (the one that comes with Ubuntu is fine)

    - add a line just below the line "project (daysim VERSION 5.2.0)": ``add_definitions(-DDAYSIM)``
    - save and return to terminal

  - ``cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim``
  - ``make``
  - ``mv ./bin/rtrace ./bin/rtrace_dc``
  - ``cp ./bin/* $HOME/Daysim/bin``
  - Daysim is now installed in the folder ``~/Daysim/bin``

Installation
~~~~~~~~~~~~

This guide walks you through the steps of installing the CEA on Ubuntu 16. Start by opening a terminal and navigating
to a folder to use for the installation. In this guide, we assume you are installing projects in your
home directory (``~``), but any other folder could do:

- navigate to the project folder: ``cd ~``
- clone the CEA repository: ``git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
- navigate to the repository folder: ``cd CityEnergyAnalyst``
- create the conda environment: ``conda env create --file environment.ubuntu.yml``
- activate the conda environment: ``conda activate cea``
- install the CEA to the conda environment: ``pip install -e .``
- test the CEA: ``cea test``

