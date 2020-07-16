REM Use the packed conda environment to run a command (e.g. during installation)
REM (makes sure the environment is set up properly before doing so)

CALL %~dp0cea-env.bat

REM run the command
CALL %*