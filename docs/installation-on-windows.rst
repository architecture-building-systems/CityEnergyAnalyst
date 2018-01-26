:orphan:

Installation guide for Windows
==============================

Follow these instructions to install the CEA on a Windows system (tested with Windows 10)

Prerequisites
~~~~~~~~~~~~~

#. Download and install `Github Desktop (64-bit) <https://desktop.github.com/>`__.
#. Download and install `Anaconda (64-bit) for python 2.7 <https://www.anaconda.com/download/>`__.
   OR `Miniconda(64-bit) for python 2.7 <https://conda.io/miniconda.html>`__.
#. Download and install `Pycharm Community edition (64-bit) <https://www.anaconda.com/download/>`__.
   OR your own favorite editor.
#. Download and install `Daysim <https://daysim.ning.com/page/download>`__.
#. Download and install  ArcGIS 10.5 - only if you would like to use ArcGIS visuals.

Installation
~~~~~~~~~~~~

#. Open Anaconda prompt (terminal console) from the start menu.
#. Type ``cd Documents`` and press ENTER.
#. Type ``git clone https://github.com/architecture-building-systems/CityEnergyAnalyst.git`` and press ENTER.
#. Type ``cd Documents\CityEnergyAnalyst`` and press ENTER.
#. Type ``conda env create`` and press ENTER.and ``activate cea``
#. Type ``activate cea`` and press ENTER.
#. Type ``pip install -e .[dev]`` and press ENTER (mind the dot '.' included in this comand!).
#. Type ``cea install-toolbox`` and press ENTER.

Configure of Pycharm
~~~~~~~~~~~~~~~~~~~~

#. Open PyCharm from the start menu and open project CityEnergyAnalyst (stored where you downloaded CEA (/Documents).
#. Open File>Settings>Project:CityEnergyAnalyst>Project Interpreter>Project Interpreter.
#. Click on the settings button (it looks like a wheel), and click in Addlocal.
#. Point to the location of your conda environment. It should look something like
   ``C:\Users\your_name\Anaconda2\envs\cea\python.exe`` or
   ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\python.exe``.
   Where 'your_name' represents your user name in windows.
#. Click apply changes.
#. Now add your conda environment ``C:\Users\your_name\Anaconda2\envs\cea``
   to your environment variable ``PATH``. The environment variable is located
   under Environment Variables in the tab Advanced in System Properties in the Control Panel.
#. Restart PyCharm if open.

.. note:: We advise to follow the above guide precisely. Especially the ``conda env create`` command can trip up users
    with previous experience in Anaconda / Miniconda as it looks very similar to the ``conda create`` command often
    used to create new conda environments.
    In addition to creating an environment, ``conda env create`` reads in the ``environment.yml`` file which contains a
    list of packages (and versions) to install as well as a definition of the channels to check. If you
    need to create a conda environment for the CEA that has a specific name (the default is ``cea``) then use the
    ``name`` parameter: ``conda env create --name your-env-name-here``
