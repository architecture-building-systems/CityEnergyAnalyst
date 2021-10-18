Installation guide for Mac OS
==============================

Working with the CityEnergyAnalyst (CEA) on a Mac OS system is a little bit messier than on Windows and requires using the Terminal to launch CEA. But don't worry - it works!

There are two installation methods: either doing a full installation from the CEA source code, or running CEA in a virtual container. The former option gives you full access to CEA but is significantly more cumbersome to install as it involves running a lot of commands on Terminal. The latter option is much easier to install but working in Docker takes some getting used to. Both options are perfectly suited for users, but only the full installation is suitable for developers.

Choose the one that suits your needs!


1. Use the CEA source code from GitHub
---------------------------------------

If you would like to develop CEA, this will be your method. Follow these instructions to install the CityEnergyAnalyst (CEA) on a Mac system (tested with macOS Mojave 10.14.6) from the source

.. attention:: We advise to follow the above guide precisely:

        *   Be sure to **USE** ``conda env create`` **NOT** ``conda create`` familiar to experienced conda users.
            This command not only creates an environment, but also reads the ``environment.yml`` file, containing a
            list of packages (and versions) to install, as well as a definition of the channels to check.
        *   If you need to create a conda environment for the CEA that has a specific name (the default is ``cea``) then use the
            ``name`` parameter: ``conda env create --name your-env-name-here``


Prerequisites
~~~~~~~~~~~~~

* Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
* Download and install `Miniconda(64-bit) for Python 3.8 <https://conda.io/miniconda.html>`__.
* Download and install `Homebrew <https://brew.sh/>`__.
* Download and install `Xcode <https://developer.apple.com/xcode/>`__.

Installation of the code base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Excluding the above software, CEA installation requires approximately 13 GB of storage (depending on your existing
Python library) and  1 hour of your time.

#. Open GitHub Desktop from the start menu.
#. Clone the CEA repository:
	#. Press ``Cmd+Shift+O`` (clone repository) and select the URL tab.
	#. Paste the CEA GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst
	#. Click Clone, this will take ~ 5-10 minutes (Size 1.65 GB).
#. Clone the CEA GUI repository:
	#. Press ``Cmd+Shift+O`` (clone repository) and select the URL tab.
	#. Paste the CEA GUI GitHub address: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
	#. Click Clone, this will take ~ 5 minutes (Size 600MB).
#. Install CEA:
    #. Open a Terminal console (you can find it in your Mac's *Applications* folder).
    #. Type ``cd Documents/GitHub/CityEnergyAnalyst`` and press ENTER.
    #. Type ``conda env create --name cea --file environment.osx.yml`` and press ENTER.
    #. Grab a cup of tea and some toast, this will take ~45 minutes.
    #. Type ``conda activate cea`` and press ENTER.
    #. Type ``pip install --no-deps -e .`` and press ENTER *(mind the dot '.' included in this command!)*.
#. Build the CEA dashboard GUI:
    #. Type ``cd ..`` and press ENTER, then type ``cd cea-electron`` and press ENTER.
    #. Install Yarn by typing ``brew install yarn`` and press ENTER.
    #. Type ``yarn`` and press ENTER.
    #. Type ``yarn dist:dir`` and press ENTER.
    #. You will find the CEA application in the folder ``/Users/your_name/Documents/GitHub/cea-electron/dist/mac``

.. attention:: In order to run CEA on Mac, you will need to select the correct Daysim binaries:

        *   If you are running the *Building Solar radiation* tool  using the dashboard, make sure the parameter *daysim-bin-directory* (under *Advanced*) points to the correct Daysim binary folder (by default, this should be ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst/setup/Dependencies/Daysim/mac``).
        *   If you are using the command line interface or Pycharm, you will need to modify the same parameter (i.e., ``config.radiation.daysim_bin_directory``) in the config file (usually located in ``Users/your_name/cea.config``, where *your_name* ).

2. Use the CEA docker image
----------------------------

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
	    #. Type ``cd Documents/GitHub/cea-electron`` and press ENTER.
        #. Install Yarn by typing ``brew install yarn`` and press ENTER.
        #. Type ``yarn`` and press ENTER.
        #. Type ``yarn dist:dir`` and press ENTER.
        #. You will find the CEA application in the folder ``/Users/your_name/Documents/GitHub/cea-electron/dist/mac``

.. _`You can find instructions on how to do that here`: https://city-energy-analyst.readthedocs.io/en/latest/developer/run-cea-in-docker.html

.. attention:: In order to run CEA on Mac, you will need to select the correct Daysim binaries:

        *   If you are running the *Building Solar radiation* tool  using the dashboard, make sure the parameter *daysim-bin-directory* (under *Advanced*) points to the correct Daysim binary folder (by default, this should be ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst/setup/Dependencies/Daysim/mac`` where *your_name* represents your user name on your Mac).
        *   If you are using the command line interface or Pycharm, you will need to modify the same parameter (i.e., ``config.radiation.daysim_bin_directory``) in the config file (usually located in ``/Users/your_name/cea.config`` where *your_name* represents your user name on your Mac).

Interfaces
----------------------------

There are different ways in which you can interact with the code of CEA.

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.
#. The Pycharm interface: this interface provides access to all the source code of CEA.

Command line interface
~~~~~~~~~~
If you installed CEA from the source code, you can run the command line interface by on the Terminal by running the command ``conda activate cea``.

In order to run the command line interface in Docker, you will need to run the following command instead: ``docker run --name cea_container -v path_to_your_cea_projects:/projects dockeruser/cea cea workflow --workflow /projects/workflow.yml``

That's it! `You can run the CEA command interface normally`_.

.. _`You can run the CEA command interface normally`: https://city-energy-analyst.readthedocs.io/en/latest/developer/interfaces.html#the-command-line-interface


Dashboard
~~~~~~~~~~
In order to run the dashboard, you will need to do the following:

#. Open the Terminal (you can find it in your Mac's *Applications* folder) and run the following command depending on your installation type:
    #. If you installed from the source code: type ``conda activate cea`` and press ENTER, then type ``cea dashboard`` and press ENTER
    #. If you are using Docker: ``docker run -t -p 5050:5050 -v path_to_your_cea_projects:/projects dockeruser/cea``
#. Run the CEA dashboard application you created in the last step of the installation above.

If you installed from the source code, you can now run the CEA dashboard interface normally.

If you're running from Docker, you will need to pay attention to a few details. Since you will not be running CEA directly on your computer, you will need to select a project on your Docker container. So if your project is located, for example, in the directory ``/Users/username/Documents/CEA_projects/my_project`` you will need to select ``/projects/my_project`` as your project in the CEA Dashboard. Also, note that your jobs in the dashboard might be listed as "pending" even when they have finished. If you would like to check if your job has finished, you can check the Terminal - it's still running in the background.

Pycharm
~~~~~~~~~~
The Pycharm interface can be helpful if you would like to contribute to CEA, but it requires a few steps
to get it up and running. In order to access and work on the source code of CEA from pycharm do:

#. Download and install `Pycharm Community edition (64-bit) <https://www.jetbrains.com/pycharm/download/#section=windows>`__ OR your own favorite editor.
#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CityEnergyAnalyst).
#. Open ``File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter``.
#. Click on the settings button (it looks like a wheel) next to the current interpreter path, and click Add.
#. Click ``Conda Environment`` from the left hand list and select existing environment.
#. Point to the location of your conda environment. It should look something like
   ``Users/your_name/Miniconda2/envs/cea/python.exe`` or
   ``Users/your_name/AppData/Local/conda/conda/envs/cea/python.exe``
   where *your_name* represents your user name on your Mac.
#. Click apply changes.
