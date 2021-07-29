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

To build the docker image, navigate to the folder ``docker/`` in the CityEnergyAnalyst repository. Execute the
following command::

   > docker build -t dockeruser/cea:latest .. -f .

Notice the ``.`` at the end of the command - be sure to include it, as it tells ``docker`` where to find the
``Dockerfile``.

The docker image should show up in your local computer::

    > docker images
    REPOSITORY                      TAG       IMAGE ID       CREATED          SIZE
    cityenergyanalyst/cea           latest    9963cd876a48   19 minutes ago   3.06GB

To share the docker image, push the image to Dockerhub::

    > docker login
        username: dockeruser
        password:
    > docker push dockeruser/cea:latest



Running the image in a new container
------------------------------------

The command::

  > docker run cityenergyanalyst/cea cea test
  > docker container run -t -p 5050:5050 cea-server

Will start the CEA server and display it's output. You should see something like this::

   City Energy Analyst version 3.11.0
   Running `cea dashboard` with the following parameters:
   - general:debug = False
     (default: False)
   start socketio.run

There's quite a lot going on here and if this is seems daunting, I suggest reading up on some Docker tutorials - I don't
understand it well enough myself to feel confident enough to explain. But here are some observations:

- The ``-t`` argument connects the container to your terminal, so you can see the output. You can drop this argument,
  but then you'll not be able to see any error messages etc. of the backend.
- The ``-p 5050:5050`` argument connects the port 5050 on the host machine (your computer) to the port 5050 in the
  container (an instance of the cea-server docker image).
- If you browse to http://localhost:5050/api/ you will see a description of the api you can use. This is the same
  api used by the CityEnergyAnalyst-GUI project, so you can essentially do anything that can be done in the GUI
  programmatically using this api.
- The ENTRYPOINT of the image is set to ``source /venv/bin/activate && cea dashboard``. You can change that if you
  would like to play around in the container: ``docker container run -it --entrypoint /bin/bash`` will take you directly
  to the shell. The ``-it`` parameter sets up interactive and tty so you can actually _do_ something there. Note,
  in order to use any of the CEA functionality, you'll need to type ``source /venv/bin/activate``.