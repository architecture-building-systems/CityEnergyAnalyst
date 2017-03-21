Installation guide
==================

The version |version| of the City Energy Analyst is dependent on ArcGIS 10.4
for its visuals. As such it is restricted to Windows-based OS's for some features.

Prerequisites
-------------

-  OS: Windows 7 or higher
-  ArcGIS 10.4 (for some features)


Installation Procedure
----------------------

Installation on Windows is easiest using Anaconda as the CEA requires ``geopandas`` which is tricky to install.

Open the Anaconda prompt and create a new conda environment::

    (C:\Users\darthoma\Anaconda2) C:\Users\darthoma>conda create -n cea python=2.7

You should see similar output to the following::

    Fetching package metadata .........
    Solving package specifications: ..........

    Package plan for installation in environment C:\Users\darthoma\Anaconda2\envs\cea:

    The following NEW packages will be INSTALLED:

        pip:            9.0.1-py27_1
        python:         2.7.13-0
        setuptools:     27.2.0-py27_1
        vs2008_runtime: 9.00.30729.5054-0
        wheel:          0.29.0-py27_0

    Proceed ([y]/n)? y

    Linking packages ...
    [      COMPLETE      ]|##################################################| 100%
    #
    # To activate this environment, use:
    # > activate cea
    #
    # To deactivate this environment, use:
    # > deactivate cea
    #
    # * for power-users using bash, you must source
    #


    (C:\Users\darthoma\Anaconda2) C:\Users\darthoma>

Next, install geopandas::

    (C:\Users\darthoma\Anaconda2) C:\Users\darthoma>activate cea

    (cea) C:\Users\darthoma>conda install -c conda-forge geopandas

This will trigger a lot of installation and might require confirmation. When all is done, installation of the CEA is
as easy as::

    (cea) C:\Users\darthoma>pip install cityenergyanalyst


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

Installation of the development environment
-------------------------------------------

**Software to be Downloaded**

-  GitHub Desktop
-  Anaconda distribution (x86)
-  Pycharm community edition
-  VCredist SP1 (x86)
-  Git Large File Storage

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

