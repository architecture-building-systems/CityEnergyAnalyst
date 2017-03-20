Installation guide
==================

The version 1.5 of the City Energy Analyst is dependent on ArcGIS 10.4
for its visuals. As such it is restricted to Windows-based OS for now.

**Prerequisites**

-  OS: Windows 7 or higher
-  ArcGIS 10.4

**Software to be Downloaded**

-  GitHub Desktop
-  Anaconda distribution (x86)
-  Pycharm community edition
-  VCredist SP1 (x86)
-  Git Large File Storage

**Installation Procedure**

#. Install GitHub Desktop and clone the repository of CEAforArcGIS into
   ``C:/Users/your_name/Documents/GitHub``.
   Take a look at the following figure, once you click 'Clone or
   download' button present in this
   `link <https://github.com/architecture-building-systems/CEAforArcGIS>`__,
   you will have two options.

|image0|

| Select 'Open in Desktop' option, it opens in GitHub Desktop as shown
  in the following figure,
| where on the left side pane, CEAforArcGIS folder is synchronised into
  your desktop.

*Note:* You can also clone it to any location you prefer. This is just
the default for GitHub Projects.

|image1|

#. Download and install `Anaconda distribution
   (x86) <https://www.continuum.io/downloads>`__. Select
   Python 2.7 version (32-bit). The following screenshots will guide you
   through the process

*Note:* Since ArcGIS is a 32-bit program, you will need to install the
32-bit version of Pyhton.

|image2|

|image3|

|image4|

|image5|

|image6|

|image7|

|image8|

|image9|

|image10|

#. Open 'Anaconda prompt', it looks like the following figure.

|image11|

#. Create a new environment from Anaconda prompt. The environment will
   be in the address something like
   ``C:\Users\your_name\Anaconda2\envs\esri104``. To create this
   environment, type the following in
   Anaconda prompt

-  ``conda create -n esri104 python=2.7 numpy=1.9.2``

|image12|

|image13|

#. ``C:\Users\your_name\Anaconda2\envs\esri104`` has a subfolder named
   ``conda-meta``. Inside this
   subfolder, create a file named ``pinned`` (without any extension) and
   set the contents to
   ``numpy ==1.9.2``. This can be done using 'Notepad++' as shown below.

|image14|

#. Install the following libraries using Anaconda Prompt. Type the
   following commands in Anaconda
   Prompt. Do refer the figures in case of confusion

-  ``activate esri104``

|image15|

-  ``conda install pandas``

|image16|

|image17|

-  ``conda install xlwt``

|image18|

-  ``codna install xlrd``

|image19|

-  ``conda install ephem``

|image20|

-  ``conda install matplotlib``

|image21|

|image22|

-  ``conda install scipy``

|image23|

-  ``pip install simpleDBF``

|image24|

-  ``pip install deap``

|image25|

-  ``pip install doit==0.29.0``

|image26|

#. Install Geopandas by following the steps mentioned below

-  | Download the zip file from this
     `link <https://shared.ethz.ch/owncloud/s/w4R8QjdMv2aqMeh>`__.
   | Unzip the file and make sure the unzipped files are present in the
     'Downloads' folder

-  | Download and install `VCredist
     SP1 <http://www.microsoft.com/en-us/download/details.aspx?id=26368>`__.
   | Download the 'x86' version. If your system already has this
     installed, the following message will
   | be displayed. Select 'cancel' from the dialogue box

   |image27|

#. Run the Anaconda command prompt and type the following commands.

-  ``activate esri104``

-  ``cd %USERPROFILE%/Downloads``

-  ``pip install GDAL-2.0.3-cp27-cp27m-win32.whl``

   |image28|

-  | add the installed path
     ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages\osgeo``
   | to your windows system path. See
     `here <http://www.computerhope.com/issues/ch000549.htm>`__ or
   | `here <http://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/>`__
   | on how this can be done.

-  Restart the anaconda prompt

-  ``activate esri104``

-  ``cd %USERPROFILE%/Downloads``

-  ``pip install Fiona-1.7.0-cp27-cp27m-win32.whl``

   |image29|

-  ``pip install pyproj-1.9.5-cp27-none-win32.whl``

   |image30|

-  ``pip install Shapely-1.5.16-cp27-cp27m-win32.whl``

   |image31|

-  ``pip install geopandas``

   |image32|

#. To test if everything is installed and working, key in
   ``gdalinfo --help`` in the Anaconda prompt.
   The output might include an error message about missing FileGDB.dll
   that can be ignored for now.

|image33|

#. Access the folder
   ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages`` and
   copy the next files so that the ``scipy.optimize`` and
   ``scipy.linalg`` modules can be loaded from ArcGIS python.

-  copy ``libmmd.dll`` from subfolder ``numpy/core`` to
   ``scipy/optimize``
-  copy ``libifcoremd.dll`` from subfolder ``numpy/core`` to
   ``scipy/optimize``
-  copy ``libiomp5md.dll`` from subfolder ``numpy/core``\ to
   ``scipy/linalg``

#. Add the ``esri104`` environment to ArcGIS python. For this, navigate
   to ``C:\Python27\ArcGIS10.4\Lib\site-packages`` (folder name may be
   different for versions of Windows > 7)

-  create a file ``esri104.pth``
-  edit the file to contain the following:
   ``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages``

#. Download and install `Git Large File
   Storage <https://git-lfs.github.com/>`__

Connecting to Arcpy
-------------------

If you would like to be able to access the ``arcpy`` module from the
``esri104`` Anaconda python environment, create a file called
``arcpy.pth`` in
``C:\Users\your_name\Anaconda2\envs\esri104\Lib\site-packages`` with the
following contents:

.. code::

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

Installation on the Euler cluster
---------------------------------

It is possible to install the CEA on the Euler_ cluster by following the following guide:
:doc:`installation-on-euler`.

.. _Euler: https://www.ethz.ch/services/en/it-services/catalogue/server-cluster/hpc.html

.. |image0| image:: assets/installation-guide/Capture1.PNG
.. |image1| image:: assets/installation-guide/Capture2.PNG
.. |image2| image:: assets/installation-guide/Capture3.PNG
.. |image3| image:: assets/installation-guide/Capture4.PNG
.. |image4| image:: assets/installation-guide/Capture5.PNG
.. |image5| image:: assets/installation-guide/Capture6.PNG
.. |image6| image:: assets/installation-guide/Capture7.PNG
.. |image7| image:: assets/installation-guide/Capture8.PNG
.. |image8| image:: assets/installation-guide/Capture9.PNG
.. |image9| image:: assets/installation-guide/Capture10.PNG
.. |image10| image:: assets/installation-guide/Capture11.PNG
.. |image11| image:: assets/installation-guide/Capture12.PNG
.. |image12| image:: assets/installation-guide/Capture14.PNG
.. |image13| image:: assets/installation-guide/Capture15.PNG
.. |image14| image:: assets/installation-guide/Capture16.PNG
.. |image15| image:: assets/installation-guide/Capture17.PNG
.. |image16| image:: assets/installation-guide/Capture19.PNG
.. |image17| image:: assets/installation-guide/Capture20.PNG
.. |image18| image:: assets/installation-guide/Capture21.PNG
.. |image19| image:: assets/installation-guide/Capture22.PNG
.. |image20| image:: assets/installation-guide/Capture23.PNG
.. |image21| image:: assets/installation-guide/Capture24.PNG
.. |image22| image:: assets/installation-guide/Capture25.PNG
.. |image23| image:: assets/installation-guide/Capture26.PNG
.. |image24| image:: assets/installation-guide/Capture27.PNG
.. |image25| image:: assets/installation-guide/Capture28.PNG
.. |image26| image:: assets/installation-guide/Capture29.PNG
.. |image27| image:: assets/installation-guide/Capture30.PNG
.. |image28| image:: assets/installation-guide/Capture31.PNG
.. |image29| image:: assets/installation-guide/Capture32.PNG
.. |image30| image:: assets/installation-guide/Capture33.PNG
.. |image31| image:: assets/installation-guide/Capture34.PNG
.. |image32| image:: assets/installation-guide/Capture35.PNG
.. |image33| image:: assets/installation-guide/Capture36.PNG

