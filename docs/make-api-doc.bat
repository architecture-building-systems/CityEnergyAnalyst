@ECHO OFF

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
 ../cea/analysis/clustering*^
 ../cea/demand/metamodel*^
 ../cea/demand/calibration/bayesian_calibrator*^
 ../cea/demand/calibration/subset_calibrator*^
 ../cea/interfaces/dashboard*^
 ../cea/optimization/slave/test*^
 ../cea/resources/radiation_daysim/plot_points*^
 ../cea/technologies/cogeneration*^
 ../cea/technologies/thermal_network/network_layout*^
 ../cea/optimization/master/generation*^
 ../cea/tests/test_dbf*^
 ../cea/utilities/compile_pyd_files*


echo.
echo Sphinx has updated cea rst files - excluding some files and paths.
echo When documentation issue for these files are fixed, please update in the docs make.bat.
echo.