# Installation hints for CEA


This document contains some hints about installing the City Energy Analyst scripts on a user machine. This relates to the version used by the MIBS students for their mid-term review on 28.10.2015 (release: mibs-2015.10.28)

The CEA consists of the following files:

- `CityEnergyAnalyst.pyt` (contains the code to add the software as a toolbox to ArcGIS)
- `prototype/*` (the actual scripts and helper modules)
- `prototype/db/*` (data used for calculations)

These need to be copied to `%APPDATA%/ESRI/Decktop10.3/ArcToolbox/MyToolbox`. `%APPDATA%` is usually something like `C:\Users\jdoe\AppData\Roaming`. If the folder `MyToolbox` does not exist, you need to create it.

For ArcGIS to be able to import the `pandas` module, you need to install `pandas` with the correct version of `numpy`(since ArcGIS has its own python distribution and an old version of `numpy`).

This is the list of modules and their versions needed:

- pandas (0.13.0)
- numpy (1.7.1 - installed with ArcGIS 10.3)
- scipy (0.13.2)

To install pandas in the correct version I used the following approach:

- install the Anaconda distribution of python (I did not install it as the default python version)
- open an Anaconda Command Prompt (from the start menu) and type: `conda create -n esri103 python=2.7 numpy=1.7.1`
	- this will create an environment (in your user folder) called "esri103" that is tied to the numpy version 1.7.1.
	- that environment can be found in `C:\Users\jdoe\Anaconda\envs\esri103`
	- inside the subfolder `conda-meta` create a file called `pinned` (that is right, no extension) and set the contents to: 
	```numpy ==1.7.1```
   - run `activate esri103` in the Anaconda command prompt
   - then do `conda install pandas` to install `pandas` - make sure the correct version is being installed.
   - do `conda install xlwt` to install the `xlwt` package for writing excel files
   - do `conda install scipy`
- inside the folder `C:\Users\jdoe\Anaconda\envs\esri103` access the `Lib\site-packages` folder.
  - copy `numpy/core/libmmd.dll` to `scipy/optimize`
  - copy `numpy/core/libifcoremd.dll` to `scipy/optimize`  
  - copy `numpy/core/libiomp5md.dll`to `scipy/linalg`
  - these files are being copied, so that the `scipy.optimize` and `scipy.linalg` modules can be loaded from ArcGIS python.
- to add the `esri103` environment to ArcGIS python, navigate to `C:\Python27\ArcGIS10.3`(folder name may be different for versions of Windows > 7)
  - create a file `Lib/site-packages/esri103.pth`
  - edit the file to contain the following:
     ``` # .pth file for accessing pandas from ArcGIS 10.3
     C:\Users\jdoe\Anaconda\envs\esri103\Lib\site-packages```

If you would like to be able to access the `arcpy` module from the `esri103` Anaconda python environment, create a file called  `arcpy.pth` in `C:\Users\jdoe\Anaconda\envs\esri103\Lib\site-packages` with the following contents:
```txt
C:\Program Files (x86)\ArcGIS\Desktop10.3\bin
C:\Program Files (x86)\ArcGIS\Desktop10.3\arcpy
C:\Program Files (x86)\ArcGIS\Desktop10.3\Scripts
```
Make sure the paths are the same as on your system.
