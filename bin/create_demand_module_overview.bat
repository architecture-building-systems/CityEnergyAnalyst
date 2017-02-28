:: create_demand_module_overview.bat
::
:: Use the `create_function_graph.py` script to create an overview of the demand calculation tracing calls from
:: module to module
::
:: NOTE: This script expects GraphViz to be installed and accessible from your PATH environment variable.
:: You can install GraphViz from here: http://www.graphviz.org/Download_windows.php

:: ---
:: author: Daren Thomas
:: copyright: Copyright 2017, Architecture and Building Systems - ETH Zurich
:: credits: Daren Thomas
:: license: MIT
:: version:  0.1
:: maintainer: Daren Thomas
:: email: cea@arch.ethz.ch
:: status: Production
:: ---

REM generate the dot file by running the demand script on the nine cubes test case
REM (the dot file is placed in the ..\docs\demand folder under the name "demand-module-overview.gv")
REM %~dp0 resolves to the full path of the folder in which the batch script resides.
if not exist "%~dp0..\docs\demand" mkdir %~dp0..\docs\demand
call python create_function_graph.py --module-overview --output %~dp0..\docs\demand\demand-module-overview.gv

REM generate the .pdf file by running the `dot` program
REM (the resulting pdf is placed in the ..\docs\demand folder under the name "demand-module-overview.gv.pdf")
call dot -Tpdf -O %~dp0..\docs\demand\demand-module-overview.gv
