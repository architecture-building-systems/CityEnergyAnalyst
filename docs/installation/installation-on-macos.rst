Installation guide for Mac OS
==============================

There are two installation methods on a Mac system (tested with macOS Mojave 10.14.6).

#. `(1) From the Source`_: If you would like to develop CEA, this will be your method.
#. `(2) As a Docker image`_: If you are not interested on developing CEA, this will be your method.

Choose the one that suits your needs!

(1) From the Source
-------------------

Prerequisites
~~~~~~~~~~~~~
* Download and install `Homebrew <https://brew.sh/>`__. Upon finishing installing Homebrew, pay attention to the message reverted. You may also have to execute ``brew install node``.
* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and Install `Micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`__. Upon finishing installing Micromamba, pay attention to the message reverted.

Installation
~~~~~~~~~~~~
.. note:: (*Experimental*) We have a script that can automate the process below. Just open a Terminal console and enter ``/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/master/install/mac_installation.sh)"`` Continue on the next section to find out how to interact with CEA.
#. Open GitHub Desktop from the start menu.
#. Clone the CEA repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst
#. Clone the CEA GUI repository with the following URL: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
#. Install CEA backend:
    #. Open a Terminal console
    #. Type ``cd Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``CONDA_SUBDIR=osx-64 mamba env create -f environment.yml`` and press ENTER.
    #. Type ``mamba activate cea`` and press ENTER.
    #. Type ``pip install -e .`` and press ENTER *(mind the dot '.'!)*.
#. Build the CEA dashboard:
    #. Type ``cd ..`` and press ENTER, then type ``cd CityEnergyAnalyst-GUI`` and press ENTER.
    #. Install Yarn by typing ``brew install yarn`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn package`` and press ENTER.
    #. You will find the CEA dashboard in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-*``

.. attention:: In order to run CEA on Mac, you will need to select the correct Daysim binaries:

        *   If you are running the *Building Solar radiation* tool using the dashboard, make sure the parameter *daysim-bin-directory* (under *Advanced*) points to the correct Daysim binary folder (by default, this should be ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst/setup/Dependencies/Daysim/mac``).
        *   If you are using the command line interface or Pycharm, you will need to modify the same parameter (i.e., ``config.radiation.daysim_bin_directory``) in the config file (usually located in ``/Users/your_name/cea.config``, where *your_name* represents your user name on your Mac).

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The Terminal console interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The pycharm interface: this interface provides access to all the source code of CEA.

The command line interface and dashboard interface are included during the installation of CEA.
Other interfaces require a few additional steps to get them up and running.

Running the CEA dashboard
_________________________

In order to launch the CEA dashboard, you will need to do the following **each time**:

#. Open the Terminal
#. Type ``mamba activate cea`` and press ENTER.
#. Type ``cea dashboard`` and press ENTER.
#. Wait for ``start socketio.run`` to appear (This might 3 min the first time)
#. Navigate your Finer to this location (``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-*``)
#. Double click on the CEA Icon (CityEnergyAnalyst-GUI.app)
#. Wait for the CEA Dashboard to launch



Here you can find a series of `blog posts <https://cityenergyanalyst.com/blogs>`_ to help you get started!

Running CEA on Pycharm
______________________

The Pycharm interface can be helpful if you would like to contribute to CEA, but it requires a few steps
to get it up and running. In order to access and work on the source code of CEA from pycharm do:

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

(2) As a Docker Image
----------------------

If you would like using docker containers, follow these instructions to run CEA on a Mac OS system (tested with Mac OS Catalina).
This method is suitable for users, but not developers. For developers, please refer to the second method below.

#. Install Docker and run CEA:
	#. `You can find instructions on how to do that here <https://city-energy-analyst.readthedocs.io/en/latest/developer/run-cea-in-docker.html>`__.
	#. If you only plan to run CEA from the command line interface, you're done!
#. If you would like to use the CEA dashboard, you will need to download and build it manually:
	#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
	#. Download and install `Miniconda(64-bit) for Python 3.8 <https://conda.io/miniconda.html>`__.
	#. Download and install `Homebrew <https://brew.sh/>`__.
	#. Clone the CEA GUI repository:
		#. Press ``Cmd+Shift+O`` (clone repository) and select the URL tab.
		#. Paste the CEA GUI GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
		#. Click Clone, this will take ~ 5 minutes (Size 600MB).
	#. Build the CEA dashboard GUI:
	    #. Open a Terminal console (you can find it in your Mac's *Applications* folder).
	    #. Type ``cd Documents/GitHub/CityEnergyAnalyst-GUI`` and press ENTER.
        #. Install Yarn by typing ``brew install yarn`` and press ENTER.
        #. Type ``yarn`` and press ENTER.
        #. Type ``yarn package`` and press ENTER.
        #. You will find the CEA application in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-*``
#. Running CEA:
    * You can run CEA a couple of different ways (see `Docker Interfaces`_ below).
    * If you are familiar with running CEA on a Windows computer, **please note that there are a few additional steps when running the dashboard on a Mac!**

.. _`You can find instructions on how to do that here`: https://city-energy-analyst.readthedocs.io/en/latest/developer/run-cea-in-docker.html


Docker Interfaces
~~~~~~~~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The Pycharm interface: this interface provides access to all the source code of CEA.

Command line interface
______________________

In order to run the command line interface in Docker, you will need to run the following command instead: ``docker run --name cea_container -v path_to_your_cea_projects:/projects dockeruser/cea cea workflow --workflow /projects/workflow.yml``

That's it! `You can run the CEA command interface normally`_.

.. _`You can run the CEA command interface normally`: https://city-energy-analyst.readthedocs.io/en/latest/developer/interfaces.html#the-command-line-interface


Dashboard
_________

In order to run the dashboard, you will need to do the following **each time you want to start the dashboard**:

#. Open the Terminal (you can find it in your Mac's *Applications* folder) and run the following command depending on your installation type:
#. Type ``docker run -t -p 5050:5050 -v path_to_your_cea_projects:/projects dockeruser/cea``.
#. Run the CEA dashboard application you created in the last step of the installation above.

You can now run the CEA dashboard normally... well, mostly. You will need to pay attention to a few details, described below.

Since you will not be running CEA directly on your computer, you will need to select a project on your Docker container. So if your project is located, for example, in the directory ``/Users/username/Documents/CEA_projects/my_project`` you will need to select ``/projects/my_project`` as your project in the CEA Dashboard.

Also, note that your jobs in the dashboard might be listed as "pending" even when they have finished. If you would like to check if your job has finished, you can check the Terminal - it's still running in the background.

