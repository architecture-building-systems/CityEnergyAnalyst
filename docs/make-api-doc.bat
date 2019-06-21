ECHO OFF

sphinx-apidoc -f -M -T -o modules ../cea^
 ../cea/databases*^
 ../cea/optimization/master/generation*^

echo.
echo Sphinx has updated cea rst files.