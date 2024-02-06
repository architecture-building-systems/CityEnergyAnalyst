@SET MAMBA_ROOT_PREFIX="%~dp0\dependencies\micromamba"
@CALL "%~dp0\dependencies\micromamba.exe shell hook -s cmd.exe"

@REM run the command
@CALL %*