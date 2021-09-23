Installation guide for Mac OS
==============================

Working with the CityEnergyAnalyst (CEA) on a Mac OS system is a little bit messier than on Windows and requires using the Terminal to launch CEA. But don't worry - it works! 
Follow these instructions to run CEA on a Mac OS system (tested with Mac OS Catalina).

1. In order to access the full CEA functionality, you will need to run CEA in Docker. `You can find instructions on how to do that here`_. If you only plan to run CEA from the command line interface, you're done!
2. If you would like to use the CEA dashboard, you will need to download and build it manually. `You can do so by following the instructions in this repository`_.

.. _`You can find instructions on how to do that here`: https://city-energy-analyst.readthedocs.io/en/latest/developer/run-cea-in-docker.html
.. _`You can do so by following the instructions in this repository`: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI

Interfaces
~~~~~~~~~~

There are different ways in which you can interact with the code of CEA.

#. The command line interface: This is the command line to all the commands of CEA from your computer terminal
#. The dashboard: This a web-based interface to CEA, open source and developed by the CEA team.

In order to run the command line interface in Docker, you will need to open the Terminal (you can find it in your Mac's `Applications`) and run the following command:
`> docker run --name cea_container -v path_to_your_cea_projects:/projects dockeruser/cea cea workflow --workflow /projects/workflow.yml`
That's it! `You can run the CEA command interface normally`_.
.. _ `You can run the CEA command interface normally`: https://city-energy-analyst.readthedocs.io/en/latest/developer/interfaces.html#the-command-line-interface

In order to run the dashboard, you will need to do the following:
#. Open the Terminal (you can find it in your Mac's `Applications`) and run the following command: `docker run -t -p 5050:5050 -v path_to_your_cea_projects:/projects dockeruser/cea`
#. Open a new tab on Terminal and type `cd Documents\GitHub\CityEnergyAnalyst-GUI`
#. Run the command `yarn`
#. The CEA dashboard should open.

You can run the CEA dashboard interface normally... well, mostly. Note that you will not be running CEA directly on your computer, so you will need to select a project on your Docker container. So if your project is located, for example, in the directory `/Users/username/Documents/CEA_projects/my_project` you will need to select `projects/my_project` as your project in the CEA Dashboard. 

Once your project is open, you can run the CEA dashboard normally. Note that your jobs in the dashboard might be listed as "pending" even when they have finished. If you would like to check if your job has finished, you can check the Terminal - it's still running in the background.
