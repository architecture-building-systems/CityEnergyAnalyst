:orphan:

Installation guide for Windows (Manual) - not recommended
==============================================

.. attention:: Manual installation is NOT RECOMMENDED for any CEA interface on Windows.
All CEA users should try using the CEA Installer for Windows first.
Follow these instructions to install the CityEnergyAnalyst (CEA) on a Windows system (tested with Windows 10) manually.

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


