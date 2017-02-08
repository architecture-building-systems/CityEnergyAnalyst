Installation guide
==================

The version 1.5 of the City Energy Analyst is dependent on ArcGIS 10.4
for its visuals. As such it is restricted to Windows-based OS for now.

Follow the next four phases to fully install the CEA for contributions.

-  `install the core <#install-the-cea's-core>`__
-  `install dependencies <#install-dependencies>`__
-  `connect to arcpy <#connect-to-arcpy>`__
-  `configure python console <#configure-your-python-console>`__

Install the CEA's core
----------------------

Clone the repository CEAforArcGIS into:
``C:/Users/your_name/Documents/GitHub``.

*NOTE:* you can also clone it to any location you prefer. This is just
the default for GitHub projects.

Install dependencies
--------------------

#. Download and install `Anaconda distribution
   x86 <https://www.continuum.io/download>`__ (use the Python 2.7
   version)

*NOTE:* Since ArcGIS is a 32-bit program, you will need to install the
x86 (32-bit) version of Python.

#. Create a new environment from the Anaconda command prompt. The
   environment will be in something like
   ``C:\Users\your_name\Anaconda2\envs\esri104``

-  do ``conda create -n esri104 python=2.7 numpy=1.9.2``

#. Inside the sub-folder ``conda-meta`` create a file called ``pinned``
   (that is right, no extension) and set the contents to:
   ``numpy ==1.9.2``

*NOTE:* an editor such as ``Notepad++`` is able to do that.

#. Install the next libraries in the anaconda command prompt:

-  do ``activate esri104``
-  do ``conda install pandas``
-  do ``conda install xlwt``
-  do ``conda install xlrd``
-  do ``conda install ephem``
-  do ``conda install matplotlib``
-  do ``conda install scipy``
-  do ``pip install simpleDBF``
-  do ``pip install deap``
-  do ``pip install doit``

#. Install
   Geopandas(\ `http:\\/\\/geopandas.org <http://geopandas.org>`__):

-  download the following files from
   `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`__

   -  `GDAL-2.0.3-cp27-cp27m-win32.whl <http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal>`__
   -  `Fiona-1.7.0-cp27-cp27m-win32.whl <http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona>`__
   -  `pyproj-1.9.5-cp27-none-win32.whl <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyproj>`__
   -  `Shapely-1.5.16-cp27-cp27m-win32.whl <http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely>`__

-  download and install `VCredist
   SP1 <http://www.microsoft.com/en-us/download/details.aspx?id=26368>`__
   (x86)

-  run the anaconda command prompt again:

   -  do ``activate esri104``
   -  do ``cd %USERPROFILE%/Downloads``
   -  do ``pip install GDAL-2.0.3-cp27-cp27m-win32.whl``
   -  add the installed path
      ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages\osgeo``
      to your windows system path. See
      `here <http://www.computerhope.com/issues/ch000549.htm>`__ or
      `here <http://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/>`__
      how this can be done.
   -  close the Anaconda Command prompt and start it again
   -  do ``activate esri104``
   -  do ``cd %USERPROFILE%/Downloads``
   -  do ``pip install Fiona-1.7.0-cp27-cp27m-win32.whl``
   -  do ``pip install pyproj-1.9.5-cp27-none-win32.whl``
   -  do ``pip install Shapely-1.5.16-cp27-cp27m-win32.whl``
   -  do ``pip install geopandas``

-  To test if everything is working do ``gdalinfo --help``

   -  *NOTE:* The output might include an error message about missing
      FileGDB dlls that can be ignored for now.

#. Access the folder
   ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages`` and
   copy the next files so that the ``scipy.optimize`` and
   ``scipy.linalg`` modules can be loaded from ArcGIS python.

-  copy ``numpy/core/libmmd.dll`` to ``scipy/optimize``
-  copy ``numpy/core/libifcoremd.dll`` to ``scipy/optimize``
-  copy ``numpy/core/libiomp5md.dll``\ to ``scipy/linalg``

#. Add the ``esri104`` environment to ArcGIS python. For this, navigate
   to ``C:\Python27\ArcGIS10.4\Lib\site-packages`` (folder name may be
   different for versions of Windows > 7)

-  create a file ``esri104.pth``
-  edit the file to contain the following:
   ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages``

#. Download and install `Git Large File
   Storage <https://git-lfs.github.com/>`__

Connect to Arcpy
----------------

If you would like to be able to access the ``arcpy`` module from the
``esri104`` Anaconda python environment, create a file called
``arcpy.pth`` in
``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages`` with the
following contents:

.. code:: txt

    C:\Program Files (x86)\ArcGIS\Desktop10.4\bin
    C:\Program Files (x86)\ArcGIS\Desktop10.4\arcpy
    C:\Program Files (x86)\ArcGIS\Desktop10.4\Scripts

Configure your python console
-----------------------------

Whatever console you like, you will need to configure it to call the
environment esri104 created in Anaconda.

The developing team uses Pycharm Community edition as default. Here are
the instructions for get pycharm up and running.

#. Access PyCharm and open project CEAforArcGIS
#. Open File>Settings>Project:CEAforArcGIS>Project Interpreter>Project
   Interpreter
#. Click on settings>addlocal and point to the location of your python
   installation in the environment esri104. It should be located in
   something like
   ``C:\Users\your_name\Anaconda2\envs\esri104/python.exe``
#. Click apply changes and your are done!

To set the custom dictionary used in PyCharm, do:

#. Open File>Settings>Editor>Spelling
#. Open the Dictionaries tab
#. Add a new Custom Dictionaries Folder
#. Select the root source folder for CEAforArcGIS. It should be located
   in something like
   ``C:\Users\your_name\Documents\GitHub\CEAforArcGIS``.
#. Click "Apply".
