REM Use the packed conda environment to install CEA to the version provided by the argument
CALL "%~dp0Dependencies\Python\Scripts\activate.bat"

python -m pip install --no-deps cityenergyanalyst==%1