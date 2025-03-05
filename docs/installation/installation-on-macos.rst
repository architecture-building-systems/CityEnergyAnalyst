Installation guide for macOS
==============================

.. include:: ../common/cea-interfaces.rst

Non-Developer version
~~~~~~~~~~

Step 1: Download and install CEA.
~~~~~~~~~~
#. `Download the latest version of CEA here`_.
#. Open the installer and drag the APP into Applications.

.. _`Download the latest version of CEA here`: https://www.cityenergyanalyst.com/#downloads

Step 2: Run CEA Dashboard.
~~~~~~~~~~

#. Locate the CEA application in the Applications folder or Launchpad and double click on it
#. Start using CEA Dashboard

Here you can find a series of tutorials at `CEA Learning Camp <https://www.cityenergyanalyst.com/learning-camp>`__ to help you get started!


Developer version
~~~~~~~~~~
Step 1: Download and install CEA.
~~~~~~~~~~

* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and Install `Micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`__.

a) Fresh installation
_________________________
#. Open GitHub Desktop from the start menu.
#. Clone the CEA repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Clone the CEA GUI repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
#. Install CEA backend:
    #. Open a Terminal console
    #. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``micromamba env create -n cea -f conda-lock.yml`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``pip install -e .`` and press ENTER *(mind the dot '.'!)*.
#. Build the CEA dashboard:
    #. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn electron:build`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/mac-*/CityEnergyAnalyst-GUI.app``

b) Update existing installation
_________________________
These steps would only work if your current installation is installed using the steps above.

#. Update CEA backend:
    #. Open a Terminal console
    #. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``git pull`` and press ENTER.
    #. Type ``micromamba env remove -n cea`` and press ENTER.
    #. Type ``micromamba env create -n cea -f conda-lock.yml`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``pip install -e .`` and press ENTER *(mind the dot '.'!)*.

#. Update the CEA Dashboard:
    #. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``git pull`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn electron:build`` and press ENTER.
    #. You will find the new CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/mac-*/CityEnergyAnalyst-GUI.app``


Step 3: Run CEA Dashboard.
~~~~~~~~~~

In order to launch the CEA dashboard, you will need to do the following **each time**:

#. Open the Terminal
#. Type ``micromamba activate cea`` and press ENTER.
#. Type ``cea dashboard`` and press ENTER.
#. Wait for ``start socketio.run`` to appear (This might 3 min the first time)
#. Navigate your Finer to this location (``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/mac-*/CityEnergyAnalyst-GUI.app``)
#. Double click on the CEA Icon (CityEnergyAnalyst-GUI.app)
#. Wait for the CEA Dashboard to launch

Here you can find a series of tutorials at `CEA Learning Camp <https://www.cityenergyanalyst.com/learning-camp>`__ to help you get started!


Step 4: Access CEA using the Pycharm Interface.
~~~~~~~~~~

In order to access and work on the source code of CEA from pycharm, do:

#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__ OR your own favorite editor.
#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CityEnergyAnalyst).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``Conda Environment`` from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like
   ``/Users/your_name/mamba/envs/cea/python.exe`` or
   ``/Users/your_name/AppData/Local/conda/conda/envs/cea/python.exe``
   where *your_name* represents your user name on your Mac.
#. Click apply changes.
