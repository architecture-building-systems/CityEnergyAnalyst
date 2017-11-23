The Configuration File
======================

The City Energy Analyst uses a configuration file for storing user preferences. User preferences
are inputs to simulation runs like what weather file to use, what scenario to use and script-specific inputs.

When you first run the ``cea`` tool (e.g. with ``cea install-toolbox`` during the installation process), the default
configuration file is copied to your home folder.

On Windows systems, the home folder is usually something like ``C:\Users\YourUserName``, so the configuration file
would be stored in ``C:\Users\michelle\cea.config``, assuming that your username is ``michelle``.


Setting values in the configuration file
----------------------------------------

The most important values to set when working with the CEA are probably those under the ``[general]`` section,
specifically ``scenario``, ``weather`` and ``region``.

Open the ``cea.config`` file with a text editor (``notebook.exe`` will do just fine) and update the values.

.. note:: We expect to implement an editor for the configuration file soon.

The configuration file and the command line interface
-----------------------------------------------------

When you run the CEA from the command line (with the ``cea`` command), then the values to use as inputs to the scripts
are taken from the configuration file. You can override each value by adding it as a parameter to the ``cea`` command,
using the syntax ``--`` + ``parameter-name`` + `` `` + ``value``. Example::

    $ cea demand --scenario C:\scenario\baseline --weather Brussels

The configuration file and the ArcGIS interface
-----------------------------------------------

The values in the configuration file are used as the default values when you open up a cea tool in the ArcGIS interface.