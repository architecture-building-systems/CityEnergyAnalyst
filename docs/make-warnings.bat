REM @ECHO OFF

pushd %~dp0

REM Run Sphinx and break on first error / warning

sphinx-build -b html -j 4 -Q -W . _build

popd
