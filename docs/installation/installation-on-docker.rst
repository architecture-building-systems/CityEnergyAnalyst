Installation guide for docker containers
==============================

Installation
~~~~~~~~~~~~~~~~~

If you would like using docker containers, follow these instructions to run CEA on a macOS system (tested with Mac OS Catalina).

#. Install Docker and run CEA:
	#. `You can find instructions on how to do that here <https://city-energy-analyst.readthedocs.io/en/latest/developer/run-cea-in-docker.html>`__.
	#. If you only plan to run CEA from the command line interface, you're done!
#. If you would like to use the CEA dashboard, you will need to download and build it manually:
	#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
	#. Download and Install `Micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`__.
	#. Download and install `Yarn <https://yarnpkg.com/getting-started/install>`__.
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
        #. You will find the CEA application in the folder ``/Users/your_name/Documents/GitHub/CityEnergyAnalyst-GUI/out/mac-*/CityEnergyAnalyst-GUI.app``
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

