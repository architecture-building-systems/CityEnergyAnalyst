REM Use the packed conda environment to pip install arguments
CALL "%~dp0cea-env.bat"

REM call pip...
CALL "%~dp0Dependencies\Python\python.exe" -m pip install %*