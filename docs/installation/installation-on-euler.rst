:orphan:

Installation guide for the Euler cluster
=======================================================

**Disclaimer**: for this to work, you must be an ETH Zurich affiliated
person and own a nethz-account.

EULER stands for *Erweiterbarer, Umweltfreundlicher, Leistungsfähiger
ETH-Rechner*. It is a high performance cluster available to users
affiliated to the ETH Zurich. See more information about the computing
cluster on the clusterwiki_.

.. _clusterwiki: https://scicomp.ethz.ch

This section describes the steps necessary to get the CEA running on the
Euler cluster.

Logging on to the Euler cluster
-------------------------------

Estimated time: 1 hr

You can login to the Euler cluster via the SSH protocol. If you use
Linux or Mac OS X, then you can directly use SSH from within a shell as
it is part of the operating system. If you are on Windows, you will need an ssh client. The CEA Console includes
the ``ssh`` command, otherwise, install a third-party application in order to use SSH
(`Putty <http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html>`__,
`Cygwin <https://www.cygwin.com/>`__, `Git for
Windows <https://git-scm.com/download/win>`__).

You can only log in to Euler from within the ETH network or when
connected via VPN.

Once in the terminal in Linux or Mac OS X or in a terminal of
thrid-party application of your choicse, do:

::

    ssh <your nethz-name>@euler.ethz.ch

After entering the above command in the shell, you will be asked for a
password. Enter your nethz password. You are then greeted with the Euler
welcome message.

Detailed steps are described in the `Euler wiki <https://scicomp.ethz.ch/wiki/Getting_started_with_clusters>`_ of the Scientific Computing Service in ETHZ.
For Windows users, it is recomendded to download WinSCP and MobaXterm.
Please follow the steps in the wiki carefully, and consult the cluster support when Troubleshooting section (2.9) is not
enough to solve your problwm.


Build a CEA Singularity container
---------------------------------

Estimated time: 20 mins

You need to build a Singularity container via a cea docker image.
The latest docker image of cea is published `here <https://hub.docker.com/u/cityenergyanalyst>`_.
Please login to Euler and conduct the following steps.

- Request a compute node with Singularity

::

    bsub -n 1 -R singularity -R light -Is bash

- Load eth_proxy to connect to the internet from compute nodes

::

    module load eth_proxy


- Pull the container image with Sigularity

::

    cd $SCRATCH
    singularity pull docker://cityenergyanalyst/cea


- Run the container interactively as shell

::

    $ singularity shell -B $HOME -B $SCRATCH cea_latest.sif
    Singularity> source /venv/bin/activate
    (venv) Singularity> cea test


Running the CEA
---------------

You need to run the CEA scripts with their command line interface (CLI). Be sure to learn how to use the job system
on Euler, as the login nodes are not intended for running simulations. See clusterwiki_.

- Upload your CEA projects to ``\cluster\scratch\username``.

- Upload a ``workflow.yml`` to ``\cluster\scratch\username``.

- Open ``workflow.yml``, point the project path to ``\cluster\scratch\username``.

- In the same ``workflow.yml``, specify the steps you wish to simulate. Please refer to this `blog post <https://cityenergyanalyst.com/blog/2020/1/14/cea-workflow-how-to-automate-simulations>`_ on how to edit ``workflow.yml``.

- Submit a batch job following this example command:

::

    bsub -n 1 -R singularity -R "rusage[mem=2048]" -W 1:00 "SINGULARITY_HOME=/projects singularity run -B $SCRATCH cea_latest.sif cea workflow --workflow /cluster/scratch/username/workflow.yml"


Other Commands
---------------

Before building a new singularity container, it is suggested to clean up the folder first.

- To remove a singularity container (e.g., a container named ``cea_latest.sif`` that is installed in ``$SCRATCH``)

::

    cd $SCRATCH
    rm cea_latest.sif


- To clean up cache files

::

    singularity cache clean

