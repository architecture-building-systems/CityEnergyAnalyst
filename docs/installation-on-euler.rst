:orphan:

Installing the City Energy Analyst on the Euler cluster
=======================================================

**Disclaimer**: for this to work, you must be an ETH Zurich affiliated
person and own a nethz-account.

EULER stands for *Erweiterbarer, Umweltfreundlicher, Leistungsfähiger
ETH-Rechner*. It is a high performance cluster available to users
affiliated to the ETH Zurich. See more information about the computing
cluster on the
`clusterwiki <http://www.clusterwiki.ethz.ch/brutus/Getting_started_with_Euler>`__.

This section describes the steps necessary to get the CEA running on the
Euler cluster.

Logging on to the Euler cluster
-------------------------------

You can login to the Euler cluster via the SSH protocol. If you use
Linux or Mac OS X, then you can directly use SSH from within a shell as
it is part of the operating system, whereas if you run Windows, you need
to install a third-party application in order to use SSH
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

Add the following lines to the file ``~/.bash_profile``. From now on you
will require basic knowledge of linux commands. here is a
`guide <http://www.howtogeek.com/howto/42980/the-beginners-guide-to-nano-the-linux-command-line-text-editor/>`__.

Now do:

::

    nano .bash_profile

then write the next in the file:

::

    PATH=$PATH:$HOME/bin
    PATH=$PATH:$HOME/apps/bin
    export PATH
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/apps/lib
    export PYTHONPATH=$HOME/SALib:$HOME/python/lib64/python2.7/site-packages
    export GDAL_DATA=$HOME/apps/share/gdal
    module load python/2.7

Save the results by doing ^O (CTRL+O) and pressing ENTER. Exit of the
file by doing ^X (CTRL+X).

Exit Euler and log on again to run the ``.bash_profile``. From now on,
the python module will be loaded automatically. The above also sets up a
path for the system to find local dynamic libraries and python libraries
- we will use this for compiling the dependencies below.

Upgrade numpy from the system version (1.8.0) to the newest version
(1.11.2 as of writing):

::

    pip install --user --upgrade numpy

The ``--user`` part to ``pip install`` tells ``pip`` to use the
``$HOME/python`` folder to install packages to - this is required
because you don't have permission to install as root. We will be using
similar tactics when compiling.

Upgrade scipy (from 0.13.2 to 0.18.1):

::

    OPENBLAS=/cluster/apps/openblas/0.2.8_seq/x86_64/gcc_4.8.2/lib
    export OPENBLAS=$OPENBLAS
    pip install --user --upgrade scipy

The system will compile, printing lots of warnings, but eventually it
should print a success message. This will happen for other libraries
below as well and might be surprising for Windows users.

::

    pip install --user xlrd
    pip install --user ephem
    pip install --user simpleDBF
    pip install --user deap

I followed `this guide to install
``libgeos_c`` <http://trac.osgeo.org/geos/wiki/BuildingOnUnixWithAutotools>`__
which is required for ``geopandas``, but modified it to install to a
local library folder. Execute the following steps:

::

    mkdir apps
    mkdir tmp; cd tmp
    curl -O http://download.osgeo.org/geos/geos-3.5.0.tar.bz2
    tar xjf geos-3.5.0.tar.bz2
    cd geos-3.5.0
    ./configure --prefix=$HOME/apps
    make
    make check
    make install  # installs to ~/apps/lib...

Now we can install Shapely:

::

    pip install --user Shapely

Installing GDAL requires a bit more effort - similar to GEOS:

::

    cd ~/tmp
    curl -O http://download.osgeo.org/gdal/2.1.1/gdal-2.1.1.tar.gz
    tar xzf gdal-2.1.1.tar.gz
    cd gdal-2.1.1
    ./configure --prefix=$HOME/apps
    make
    make install

The remaining libraries install easily:

::

    pip install --user fiona
    pip install --user pyproj
    pip install --user geopandas

Installing SALib
~~~~~~~~~~~~~~~~

The SALib library that is used by the sensitivity analysis routines does
not install with ``pip install SALib`` because the version of setuptools
on the cluster is just too old. Instead do this:

::

    [user@euler06 ~]$ git clone https://github.com/SALib/SALib.git
    Initialized empty Git repository in /cluster/home/darthoma/SALib/.git/
    remote: Counting objects: 2769, done.
    Receiving objects: 100% (2769/2769), 2.56 MiB | 1.34 MiB/s, done.
    remote: Total 2769 (delta 0), reused 0 (delta 0), pack-reused 2769
    Resolving deltas: 100% (1748/1748), done.

The ``PYTHONPATH`` exported in the ``~/.bash_profile`` script above
already includes the SALib path. Otherwise, append ``$HOME/SALib`` to
your ``PYTHONPATH``.

Cloning the CEA from GitHub
---------------------------

Installing the CEA itself is as simple as cloning it from GitHub:

::

    git clone https://github.com/architecture-building-systems/CEAforArcGIS.git

Alternatively, you can also clone a branch of the cea with:

::

    git clone - b <my-branch>  https://github.com/architecture-building-systems/CEAforArcGIS.git

Running the CEA
---------------

Since ArcGIS is not installed on the cluster, you need to run the CEA
scripts with their command line interface (CLI).

Here is an example from my account (``darthoma`` - replace with your own
user name) using a reference case previously cloned to the home folder:

::

    cd $HOME/CEAforArcGIS/cea
    export WEATHER=/cluster/home/darthoma/CEAforArcGIS/cea/databases/weather/Zug.epw
    export SCENARIO=/cluster/home/darthoma/cea-reference-case/reference-case-zug/baseline
    python demand/demand_main.py --scenario $SCENARIO --weather $WEATHER


