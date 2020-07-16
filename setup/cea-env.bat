REM Set up the environment for using the CEA - assumes the CEA is installed and this file is in the root
REM of the installation

REM set up environment variables
SET PATH=%~dp0Dependencies\Python;%~dp0Dependencies\Python\Scripts;%PATH%
SET PATH=%~dp0Dependencies\Python\Library\bin;%~dp0Dependencies\Daysim;%PATH%
SET PYTHONHOME=%~dp0Dependencies\Python
SET GDAL_DATA=%~dp0Dependencies\Python\Library\share\gdal
SET PROJ_LIB=%~dp0Dependencies\Python\Library\share\proj
SET RAYPATH=%~dp0Dependencies\Daysim