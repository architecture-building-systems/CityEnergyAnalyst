ECHO OFF

echo.
echo Removing old rst files.
echo.

pushd modules
del cea*.rst
popd

echo Building new rst files.
echo.

sphinx-apidoc -f -M -T -o modules ../cea^
 ../cea/databases*^
 ../cea/demand/metamodel*^
 ../cea/interfaces/dashboard*^
 ../cea/resources/radiation_daysim/plot_points*^
 ../cea/technologies/thermal_network/network_layout*^
 ../cea/optimization/master/generation*^
 ../cea/tests/test_dbf*^
 ../cea/utilities/compile_pyd_files*^



echo.
echo Sphinx has updated cea rst files - excluding some files and paths.
echo When documentation issues for these modules are fixed, please delete the exceptions in the docs make-api-doc.bat.
echo.