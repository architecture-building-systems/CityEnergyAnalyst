@SET MAMBA_ROOT_PREFIX=%~dp0dependencies\micromamba
@CALL "%~dp0dependencies\micromamba.exe" shell hook -s cmd.exe
@CALL "%~dp0dependencies\micromamba\condabin\mamba_hook.bat"

@REM run the command
@CALL %*
