:orphan:

Installation guide for Ubuntu
=============================

Follow these instructions to install the CEA on a Linux system (tested with Ubuntu 16.04 LTS)

Prerequisites
~~~~~~~~~~~~~

#. Anaconda2 or Miniconda2

  - ``curl -O https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh``
  - ``bash Miniconda2-latest-Linux-x86_64.sh`` (defaults are fine)

#. git

  - ``apt-get install git``

#. Download and install `Daysim <https://daysim.ning.com/page/download>`__.

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
- add this to your environment: ``export MKL_THREADING_LAYER=GNU``

  - either type that out every time before you start using the CEA or add it to your ``~/.bashrc``

- test the CEA: ``cea test``

