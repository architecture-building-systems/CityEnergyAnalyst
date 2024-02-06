@SET MAMBA_ROOT_PREFIX="%~dp0dependencies\micromamba"
@CALL "%~dp0dependencies\micromamba.exe" shell hook -s cmd.exe

@REM run the command
@CALL %*