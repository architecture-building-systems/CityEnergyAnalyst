Installation guide for Docker
==============================

Pre-requisites
~~~~~~~~~~~~~~~

* `Docker <https://docs.docker.com/get-docker/>`__
* Knowledge on how to run commands using Docker

Installation
~~~~~~~~~~~~~~~~~
#. Pull CEA docker image from GitHub:

	.. code-block:: bash

		docker pull ghcr.io/architecture-building-systems/cityenergyanalyst/cea

#. Start a CEA docker container using one of the supported interfaces:

	There are different ways in which you can interact with the CEA docker container.

	- **Command line interface**: Run CEA commands from your computer terminal
	- **Desktop App**: Open source desktop application developed by the CEA team. (https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI)

Command line interface
______________________

In order to run CEA from the command line, you will need to run the following command: 

.. code-block:: bash

	docker run --rm -v PATH_TO_PROJECT:/projects ghcr.io/architecture-building-systems/cityenergyanalyst/cea cea

``--rm`` :							ensures that the container is removed after the command is executed.

``-v PATH_TO_PROJECT:/projects`` :	mounts the folder containing your CEA projects on your local machine to the container.

That's it! `You can run the CEA command interface normally <developer/interfaces.html#the-command-line-interface>`__.

Desktop App
___________

In order to use the CEA docker container with the Desktop App, you will need to start the docker container **every time before** starting the Desktop App:

.. code-block:: 

	docker run --rm -t -p 5050:5050 -v PATH_TO_PROJECT:/projects ghcr.io/architecture-building-systems/cityenergyanalyst/cea

``--rm`` :							ensures that the container is removed after the command is executed.

``-t`` :							allocates a pseudo-TTY, which keeps the container running and provides terminal output.

``-p 5050:5050`` :					maps the container's port 5050 to the host's port 5050.

``-v PATH_TO_PROJECT:/projects`` :	mounts the folder containing your CEA projects on your local machine to the container.

.. note:: 

	You can now run the CEA Desktop App normally... well, mostly. You will need to pay attention to a few details, described below.

	Since you will not be running CEA directly on your computer *(the docker container would not be able to access your files unless you tell it to)*,
	you will need to mount the folder that contains your CEA projects to your Docker container.
	
	So if your project is located, for example, in the directory ``/Users/username/Documents/CEA_projects/my_project`` you will need to mount ``/Users/username/Documents/CEA_projects``
	and select ``/projects/my_project`` as your project in the Desktop App.

	Also, note that your jobs in the dashboard might be listed as "pending" even when they have finished. If you would like to check if your job has finished, you can check the terminal - it's still running in the background.

