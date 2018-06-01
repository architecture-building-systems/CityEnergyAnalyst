@ECHO OFF

echo.
echo Removing old rst files.
echo.

pushd modules
del cea*.rst
popd

echo Building new rst files.
echo.

sphinx-apidoc -f -M -T -o modules ../cea


echo.
echo Sphinx has updated cea rst files - excluding some files and paths.
echo When documentation issue for these files are fixed, please update in the docs make.bat.
echo.