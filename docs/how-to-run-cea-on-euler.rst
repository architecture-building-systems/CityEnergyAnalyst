:orphan:

How to run the CEA on Eurler
============================

Euler is the name of the High Performance Computing clusters that is open to members of ETHZ.
The CEA is installed on Euler as a Singularity container.


The main steps to run CEA on Euler are:

#. Accessing the clusters.
#. Build a CEA Singularity container.
#. Run a simulation.


Step 1: Accessing the clusters
------------------------------
Estimated time: 1 hr

The detailed steps are described in the `wiki <https://scicomp.ethz.ch/wiki/Getting_started_with_clusters>`_ of the Scientific Computing Service in ETHZ.

For Windows users, it is recomendded to download WinSCP and MobaXterm.
Please follow the steps in the wiki carefully, and consult the cluster support when Troubleshooting section (2.9) is not
enough to solve your problwm.


Step 2: Build a CEA Singularity container.
------------------------------------------
Estimated time: 20 mins

- Request a compute node with Singularity::
    bsub -n 1 -R singularity -R light -Is bash

- Load eth_proxy to connect to the internet from compute nodes::
    module load eth_proxy


- Pull the container image with Sigularity::
    cd $SCRATCH
    singularity pull docker://dockeruser/cea


- Check for `cea_latest.sif` in the scratch folder by typing

``
$ ls

``

- Run the container interactively as shell

``
$ singularity shell -B $HOME -B $SCRATCH cea_latest.sif
Singularity> source /venv/bin/activate
(venv) Singularity> cea
``


Step 3: Run a simulation.
-------------------------

#. Upload your CEA projects to ``\cluster\scratch\username``
#. Upload a ``workflow.yml`` to ``\cluster\scratch\username``
In ``workflow.yml``, point to the CEA project as well as the steps you wished to simulated.
Here is an example:
