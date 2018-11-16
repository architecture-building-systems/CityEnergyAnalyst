Known issues
============
CEA uses Github Issues to document new ideas for user interaction or technical `bugs <https://github.com/architecture-building-systems/CityEnergyAnalyst/labels/bug>`_.
Please read the :doc:`how-to-contribute` guide and review the `open issues <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues?utf8=%E2%9C%93&q=is%3Aopen+>`_
before posting. We appreciate your contribution!

The table below contains a number of common issues that may arise while Installing or using CEA:

.. csv-table:: Known Issues
    :header: "Issue #", "Regarding", "Description"
    :widths: 12, 20, 40

    "`1577 <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/1577>`_", "ArcGIS < 10.6", "Internet Explorer Script Error:
    An error has occurred in the script of this page. Do you want to continue running scripts on this page?"
    "Update", "ArcGIS", "During the ``cea install-toolbox`` you get this error::

        ImportError: no module named arcpy

    Check your home directory for a file called ``cea_arcgis.pth`` containing these three lines::

        C:\Program Files (x86)\ArcGIS\Desktop10.5\bin64
        C:\Program Files (x86)\ArcGIS\Desktop10.5\arcpy
        C:\Program Files (x86)\ArcGIS\Desktop10.5\Scripts

    Edit these folders to point to the appropriate ArcGIS folders as documented in the ArcGIS manuals."
    "Update", "Fiona/GDAL", "After the installation you experience an error::

        ImportError: DLL load failed: The specified module could not be found.

    Try copying::

        C:\Users\your_name\Anaconda2\envs\cea\proj.dll
        TO
        C:\Users\your_name\Anaconda2\envs\cea\Library\bin

    OR::

      C:\Users\your_name\AppData\Local\conda\conda\envs\cea\proj.dll
      TO
      C:\Users\your_name\Anaconda2\envs\cea\Library\bin"

    "Update", "daysim_main.py", "Error when running daysim_main.py::

        .wea weather file cannot be found

    In the subfiles inputlocator.py/tempfile.py, the environment variable is not correctly read if the username
    contains a space.
    If the original path for the TEMP environment variable is::

        C:\Users\Mister Tester\AppData\Local\Temp

    it is read as::

        C:\Users\MisterT~1\AppData\Local\Temp"

Report a new issue
------------------

For any problems please `post a new issue here <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues>`__.
We have a turn-over time of a couple of days.

