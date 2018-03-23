:orphan:

Installation guide for Ubuntu
=============================

Follow these instructions to install the CEA on a Linux system (tested with Ubuntu 16.04 LTS)

Prerequisites
~~~~~~~~~~~~~

#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
#. Download and install `Anaconda (64-bit) for python 2.7 <https://www.anaconda.com/download/>`__.
   OR `Miniconda(64-bit) for python 2.7 <https://conda.io/miniconda.html>`__.
#. Download and install `Pycharm Community edition (64-bit) <https://www.anaconda.com/download/>`__.
   OR your own favorite editor.
#. Download and install `Daysim <https://daysim.ning.com/page/download>`__.

Installation
~~~~~~~~~~~~

This guide walks you through the steps of installing the CEA on Ubuntu 16. Start by opening a terminal and navigating
to a folder to use for the installation. In this guide, we assume you are using ``~/tmp`` and starting out in your
home directory (``~``):

- create a folder for working in: ``mkdir tmp``
- navigate to that folder: ``cd tmp``
- download the installation script: ``curl -O https://repo.continuum.io/archive/Anaconda2-5.0.1-Linux-x86_64.sh``

  - *NOTE*: The actual link will change as new versions of Anaconda2 are released. You can find the newest link here:
    https://www.anaconda.com/download/#linux

- run the installation script: ``bash Anaconda2-5.0.1-Linux-x86_64.sh``

  - *NOTE*: make sure to replace with the version you actually downloaded
  - follow instructions (hint, you can use the space key to view the license one page at a time)
  - use the default settings unless you know what you're doing
  - except for  the question: "Do you wish the installer to prepend the Anaconda2 install location to PATH in your /home/user/.bashrc ? [yes|no]"

    - this is probably a good idea to agree to.
    - then, either start a new terminal as suggested or do ``source ~/.bashrc``

- clone the CEA repository: ``git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
- navigate to that folder: ``cd CityEnergyAnalyst``
- *FIXME*: this step needs to be removed when merging to master: ``git checkout 951-chisqprob-is-deprecated``
- create the conda environment: ``conda env create --file environment.ubuntu.yml``
- activate the conda environment: ``source activate cea``
- install the CEA to the conda environment: ``pip install -e .[dev]``
- add this to your environment: ``export MKL_THREADING_LAYER=GNU``

  - either type that out every time before you start using the CEA or add it to your ``~/.bashrc``

- test the CEA: ``cea test``

