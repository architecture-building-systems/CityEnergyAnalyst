:orphan:

Installing the City Energy Analyst on the Euler cluster
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

Installing dependencies
-----------------------

The Euler cluster has most of the dependencies for the CEA pre-installed. You just need to load the right module with

::

    module load new gcc/4.8.2 python/2.7.14

You can add that to the file ``~/.bash_profile`` if you don't want to type it every time you log into Euler.

Install the CEA with the following command:

::

   pip install --user cityenergyanalyst

This will install the ``cea`` command to ``~/.local/bin``, so add that to your PATH variable with

::

   export PATH=~/.local/bin:$PATH

You can add that to the file ``~/.bash_profile`` if you don't want to type it every time you log into Euler.

Running the CEA
---------------

You need to run the CEA scripts with their command line interface (CLI). Be sure to learn how to use the job system
on Euler, as the login nodes are not intended for running simulations. See clusterwiki_.


