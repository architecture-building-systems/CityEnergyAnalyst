Running the CEA in Docker
=========================

  Docker is an open-source project for automating the deployment of applications as portable, self-sufficient containers
  that can run on the cloud or on-premises. (Source_)

.. _Source: https://docs.microsoft.com/en-us/dotnet/architecture/microservices/container-docker-introduction/docker-defined

The CEA can be run in docker. The main steps are:

- install Docker on your computer (out of scope of this document)
- build the image
- run the image

Note, that "CEA" in this context refers to the backend (server, cli) part of the CEA and not the GUI.

Building the image
------------------

Set server host to ``0.0.0.0``. You can do it by editing ``default.config`` in the ``cea`` folder. In the ``[server]``
section, change the default address from ``127.0.0.1`` to ``0.0.0.0``.

To build the docker image, navigate to CityEnergyAnalyst repository where the ``Dockerfile`` is located. Execute the
following command::

    > docker build -t dockeruser/cea:latest .

Notice the ``.`` at the end of the command - be sure to include it, as it tells ``docker`` where to find the
``Dockerfile``.

The docker image should show up in your local computer::

    > docker images
    REPOSITORY                      TAG       IMAGE ID       CREATED          SIZE
    dockeruser/cea                  latest    9963cd876a48   19 minutes ago   3.06GB

To share the docker image, push the image to Dockerhub::

    > docker login
        username: dockeruser
        password:
    > docker push dockeruser/cea:latest


Pull docker image
-----------------

If you wish to use the latest cea image without building it on your own, you can pull it from our `dockerhub <https://hub.docker.com/repository/docker/cityenergyanalyst/cea>`__.

To pull a docker image from Dockerhub::

    > docker pull dockeruser/cea


Running the image in a new container
------------------------------------

1. To test the docker image::

    > docker run --rm dockeruser/cea cea test

   * The ``--rm`` flag removes the container after it finishes running. This is useful when running the ``cea test``
command so that the container does not persist after it exits after running the tests.

2. To run the docker container via shell (as the CEA Console)::

    > docker run -it -v /home/cea_projects:/projects dockeruser/cea /bin/bash
    root@df9d4b16e5c0:> source /venv/bin/activate
    (venv) root@df9d4b16e5c0:> cea --help

   * The ``-it`` flag sets up interactive and tty so you can actually _do_ something there. Note, in order to use any of the CEA functionality, you'll need to type ``source /venv/bin/activate``.
   * The `-v /home/cea_projects:/projects` binds the folder ``/home/cea_projects`` in host to the folder ``/projects`` inside the container. Files saved in ``/home/cea_projects`` will be shared with the container.

3. To run ``cea workflow``. First make sure the project folder and ``workflow.yml`` are in the correct path, in the example is ``/home/cea_projects``.::

    > docker run --name cea_container -v /home/cea_projects:/projects dockeruser/cea cea workflow --workflow /projects/workflow.yml

4. To connect the GUI, CEA Dashboard, to a container ::

    > docker run -t -p 5050:5050 dockeruser/cea

  This command will start the CEA server and display it's output. You should see something like this::

    City Energy Analyst version 3.24.0
    Running `cea dashboard` with the following parameters:
    - general:debug = False
      (default: False)
    start socketio.run

  There's quite a lot going on here and if this is seems daunting, I suggest reading up on some Docker tutorials - I don't
  understand it well enough myself to feel confident enough to explain. But here are some observations:
   * The ``-t`` flag connects the container to your terminal, so you can see the output. You can drop this argument, but then you'll not be able to see any error messages etc. of the backend.
   * The ``-p 5050:5050`` flag connects the port 5050 on the host machine (your computer) to the port 5050 in the container (an instance of the cea-server docker image).
   * If you browse to http://localhost:5050/api/ you will see a description of the api you can use. This is the same api used by the CityEnergyAnalyst-GUI project, so you can essentially do anything that can be done in the GUI programmatically using this api.
