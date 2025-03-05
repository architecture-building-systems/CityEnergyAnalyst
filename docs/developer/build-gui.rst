Windows
-------
#. Clone the CEA GUI repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
#. Build the CEA dashboard:

    #. Type ``cd ..`` and press ENTER, then type ``cd CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn electron:build`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/win-unpacked/CityEnergyAnalyst-GUI.exe``

#. Build the CEA dashboard:
    #. Type ``cd ~/Documents/GitHub/CityEnergyAnalyst-GUI`` and press ENTER.
    #. Type ``micromamba activate cea`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn electron:build`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/mac-*/CityEnergyAnalyst-GUI.app``


macOS
-----
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
