echo.
echo Removing old rst files.
echo.

pushd modules
del cea*.rst
popd

echo Building new rst files.
echo.

sphinx-apidoc -f -M -T -o modules ../cea ../cea/databases* ../cea/analysis/clustering*
echo.
echo Sphinx has updated cea rst files - excluding databases and analysis clustering.
echo When analysis clustering documentation issues are fixed please update in the docs make.bat.
echo.