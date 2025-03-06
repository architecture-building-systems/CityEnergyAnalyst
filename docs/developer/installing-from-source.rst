Install CEA from source
=======================

This is recommended for advanced users and developers who want to contribute to the codebase.

The steps below will describe how to setup an environment for CEA by installing the required dependencies in a conda environment.

.. note:: Due to the complex dependencies of CEA, we currently do not support installing using ``pip`` directly from PyPI.

Prerequisites
-------------
* `Git <https://git-scm.com/downloads>`__
    Required to clone the CEA source code from GitHub. 
    You can use `Github Desktop <https://desktop.github.com/>`__ if you are not comfortable with the command line.
* `Conda <https://docs.conda.io/projects/conda/en/stable/>`__
   We recommend using `Micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`__.
   It supports parallel downloading of package files using multi-threading and it natively supports `conda-lock <https://github.com/conda/conda-lock/>`__ to skip the solving of dependencies *(it saves a lot of time!)*.
   
   .. attention:: Currently using Micromamba v2 is not supported due to a `bug in micromamba <https://github.com/mamba-org/mamba/issues/3711>`__. Please use **v1.5.10** instead.
    
   .. attention:: If you are planning to use CEA in **PyCharm**, we recommend using the other ones listed below, since micromamba environments are not natively supported by **PyCharm**.

   However, you can use any other conda package manager that you might already have
   (e.g. `Anaconda <https://www.anaconda.com/docs/getting-started/anaconda/install>`__, `Miniconda <https://www.anaconda.com/docs/getting-started/miniconda/install>`__ or `Miniforge <https://github.com/conda-forge/miniforge>`__),
   we will install conda-lock in the following steps.


Installation
------------
#. Clone the CEA repository with the URL: https://github.com/architecture-building-systems/CityEnergyAnalyst

    Using the command line:

    .. code-block:: bash

        git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git
    
    This will create a directory called ``CityEnergyAnalyst`` in your current directory.

#. Install ``conda-lock`` to manage the dependencies of CEA:

    **Skip this step if you are using micromamba or already have conda-lock installed.**

    Using the command line:

    .. code-block:: bash
        
        conda install --channel=conda-forge --name=base conda-lock


#. Create CEA conda environment:

    We will be creating a conda environment called ``cea`` for the purpose of installing CEA.
    
    Using the ``conda-lock.yml`` file found in the root directory of the CEA repository,
    the environment will be created without having to solve for the dependencies.

    Using the command line (micromamba):

    .. code-block:: bash
        
        micromamba create --name cea --file ./CityEnergyAnalyst/conda-lock.yml
    
    Using the command line (Conda):

    .. code-block:: bash
        
        conda lock install --name cea --file ./CityEnergyAnalyst/conda-lock.yml
    
    .. note:: 
        If you are using Windows, the path separator would be ``\`` instead of ``/`` 

        e.g. ``.\CityEnergyAnalyst\conda-lock.yml`` instead of ``./CityEnergyAnalyst/conda-lock.yml``
    
#. Install CEA in the ``cea`` environment:

    Activate the newly created environment and install CEA in the environment in editable mode (i.e. using the ``-e`` flag)
    using the path of the cloned repository.

    Using the command line (micromamba):

    .. code-block:: bash
        
        micromamba activate cea
        pip install -e ./CityEnergyAnalyst
    
    Using the command line (Conda):

    .. code-block:: bash
        
        conda activate cea
        pip install -e ./CityEnergyAnalyst

Now you should have a working installation of CEA!

You should be able to run the following command to see the help message:

.. note:: Remember to activate the ``cea`` environment before running any cea commands.

.. code-block:: bash

    cea --help

    usage: cea SCRIPT [OPTIONS]
       to run a specific script
    usage: cea --help SCRIPT
        to get additional help specific to a script

To use it in Pycharm, see :doc:`pycharm-interface`.
