# City Energy Analyst for ArcGIS Desktop 10.4

This file describes the installation of the City Energy Analyst (CEA) as performed by the installer 
`Setup_CityEnergyAnalyst10.4.exe`.

The city energy analyst (CEA) is an urban simulation engine created to assess multiple energy efficiency strategies 
in urban areas. The CEA offers tools for the analysis of the carbon, financial and environmental benefits of the next 
strategies in an urban area.

- **Building retrofits:** Appliances and lighting, building envelope, HVAC systems (incl. Control strategies)
- **Integration of local energy sources:** renewable and waste-to-heat energy sources.
- **Infrastructure retrofits:** decentralized and centralized thermal micro-grids and conversion technologies.
- **Modifications to urban form:** new zoning, changes in occupancy and building typology.

You can find more information about the CEA here: https://github.com/architecture-building-systems/CityEnergyAnalyst

## Files installed

The installer made the following changes to your computer:
 
- Installation directory: (typically `C:\Program Files (x86)\CityEnergyAnalyst`)
  - `README.md` - this file
  - `LICENSE.md` - copy of the license file mentioned below
  - `site-packages` - contains python library dependencies
- `C:\Python27\ArcGIS10.4\Lib\site-packages`
  - `cealib.pth` - tells ArcGIS's python where to find the python library dependencies (**NOTE**: in certain cases this
  does not work, e.g. ArcGIS's python is in a different directory. You will need to manually copy this file to the 
  appropriate directory or add it's parent folder to your `%PYTHONPATH%` environment variable)
- ArcGIS Toolboxes folder (typically `%APPDATA%\ESRI\Desktop10.4\ArcToolbox\My Toolboxes`)
  - `cea` - contains the CEA code
  - `City Energy Analyst.pyt` - contains a description of the toolbox for ArcGIS Desktop
  - `City Energy Analyst.*.pyt.xml` - these files are created by ArcGIS, one per tool provided by the CEA
  
**NOTE**: This installer does not install Python, just copies a set of library dependencies and sets up the version of 
Python most likely used by ArcGIS to recognize these libraries. If your setup is more complicated, you might need
to install manually. Check the online documentation for a manual installation guide here:
https://architecture-building-systems.gitbooks.io/cea-toolbox-for-arcgis-manual/content/
 
## License

This software is under the MIT License. See here for more information: 
https://github.com/architecture-building-systems/CityEnergyAnalyst/blob/master/LICENSE.md

### Dependencies

The installer also installs library dependencies, all open source, that might have differing licenses. This is a list
of library dependencies shipped with the installer:

- colorama=0.3.7=py27_0 (BSD License)
- decorator=4.0.10=py27_0 (BSD License)
- enum34=1.1.6=py27_0 (GNU GPL)
- ephem=3.7.5.3=py27_0 (GNU LGPL)
- funcsigs=1.0.2=py27_0 (Apache Software License)
- ipython=5.1.0=py27_0 (BSD License)
- ipython_genutils=0.1.0=py27_0 (BSD License)
- jpeg=8d=vc9_0 (Python Software Foundation License)
- llvmlite=0.9.0=py27_0 (BSD License)
- markdown=2.6.6=py27_0 (BSD License)
- matplotlib=1.4.3=np19py27_3 (BSD License)
- nose=1.3.7=py27_1 (GNU LGPL)
- numba=0.24.0=np19py27_0 (BSD License)
- numpy=1.9.2=py27_2 (BSD License)
- openssl=1.0.2h=vc9_0 (Apache Software License)
- pandas=0.17.0=np19py27_0 (BSD License)
- path.py=8.2.1=py27_0 (MIT License)
- pathlib2=2.1.0=py27_0 (MIT License)
- pickleshare=0.7.4=py27_0 (MIT License)
- pip=8.1.2=py27_0 (MIT License)
- prompt_toolkit=1.0.8=py27_0 (BSD License)
- pygments=2.1.3=py27_0 (BSD License)
- pyparsing=2.1.4=py27_0 (MIT License)
- pyqt=4.11.4=py27_7 (GNU GPL)
- python-dateutil=2.5.3=py27_0 (BSD License)
- pytz=2016.6.1=py27_0 (MIT License)
- scikit-learn=0.16.1=np19py27_0 (new BSD)
- scipy=0.16.0=np19py27_0 (BSD)
- setuptools=25.1.6=py27_0 (MIT License)
- simplegeneric=0.8.1=py27_1 (ZPL 2.1 - Zope Public License)
- singledispatch=3.4.0.3=py27_0 (MIT License)
- six=1.10.0=py27_0 (MIT License)
- sqlalchemy=1.0.13=py27_0 (MIT License)
- traitlets=4.3.1=py27_0 (BSD License)
- wcwidth=0.1.7=py27_0 (MIT License)
- wheel=0.29.0=py27_0 (MIT License)
- win_unicode_console=0.5=py27_0 (MIT License)
- xlrd=1.0.0=py27_0 (BSD License)
- xlwt=1.1.2=py27_0 (BSD License)
- deap==1.0.2 (GNU LGPL)
- descartes==1.0.2 (BSD License)
- doit==0.29.0 (MIT License)
- fiona==1.7.0 (BSD License)
- gdal==2.0.3 (MIT License)
- geopandas==0.2.1 (BSD License)
- httplib2==0.9.2 (MIT License)
- plotly==1.12.9 (MIT License)
- pyproj==1.9.5 (OSI Approved)
- requests==2.11.1 (Apache Software License)
- salib==0.7.1 (MIT License)
- shapely==1.5.16 (BSD License)
- simpledbf==0.2.6 (BSD License)


  
