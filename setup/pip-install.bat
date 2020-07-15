REM Use the packed conda environment to pip install arguments
REM (makes sure the environment is set up properly before doing so)

REM set up environment variables
SET PATH=%~dp0\Dependencies\Python;%~dp0\Dependencies\Python\Scripts;%PATH%
SET PATH=%~dp0\Dependencies\Python\Library\bin;%~dp0\Dependencies\Daysim;%PATH%
SET PYTHONHOME=%~dp0\Dependencies\Python
SET GDAL_DATA=%~dp0\Dependencies\Python\Library\share\gdal
SET PROJ_LIB=%~dp0\Dependencies\Python\Library\share
SET RAYPATH=%~dp0\Dependencies\Daysim

REM call pip...
CALL python -m pip install %*