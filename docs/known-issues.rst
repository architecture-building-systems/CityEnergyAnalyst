Known issues
============

This is a small collection of known issues that may rise while Installing or using CEA.

Fiona or GDAL
--------------

Error while running CEA
    If after the installation you experience an error concerning geopandas or fiona, i.e.,
    ``ImportError: DLL load failed: The specified module could not be found.``
    Try copying ``C:\Users\your_name\Anaconda2\envs\cea\proj.dll`` OR
    ``C:\Users\your_name\AppData\Local\conda\conda\envs\cea\proj.dll`` to
    ``C:\Users\your_name\Anaconda2\envs\cea\Library\bin`` OR
    ``C:\Users\your_name\AppData\Local\conda\conda\envs\Library\bin`` and CEA should run.


ArcGIS
------

CEA toolbox is not displayed in ArcGIS
    The step ``cea install-toolbox`` (see step 4 in the basic installation steps above) attempts to connect the CEA with
    the ArcGIS environment. You should not need to do anything else. If, however, you get error messages like
    ``ImportError: no module named arcpy`` you can check your home directory
    for a file called ``cea_arcgis.pth`` containing these three lines::

        C:\Program Files (x86)\ArcGIS\Desktop10.5\bin64
        C:\Program Files (x86)\ArcGIS\Desktop10.5\arcpy
        C:\Program Files (x86)\ArcGIS\Desktop10.5\Scripts

    Edit these folders to point to the appropriate ArcGIS folders as documented in the ArcGIS manuals.

Report a new issue
------------------

For any problems please `post a new issue here <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues>`__.
We have a turn-over time of a couple of days.

