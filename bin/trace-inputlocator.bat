rem run the trace-inputlocator for as many tools as possible, collecting the data

rem set up the case study
cea extract-reference-case --destination %temp% --case cooling
cea-config demand --scenario %temp%\reference-case-cooling\baseline --weather Singapore-Changi_1990_2010_TMY
mkdir %temp%\reference-case-cooling\baseline\outputs

rem data-helper
cea-config data-helper --region SG
cea trace-inputlocator --scripts data-helper
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts radiation-daysim, demand
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts emissions, operation-costs
if %errorlevel% neq 0 exit /b %errorlevel%

cea-config network-layout --network-type DC
cea trace-inputlocator --scripts network-layout
if %errorlevel% neq 0 exit /b %errorlevel%

rem make sure to run the quicker version (type-scpanel=FP)
cea-config solar-collector --type-scpanel FP
cea trace-inputlocator --scripts solar-collector
if %errorlevel% neq 0 exit /b %errorlevel%

cea-config solar-collector --type-scpanel ET
cea trace-inputlocator --scripts solar-collector
if %errorlevel% neq 0 exit /b %errorlevel%


cea trace-inputlocator --scripts photovoltaic, photovoltaic-thermal
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts sewage-potential, lake-potential
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts operation-costs
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts network-layout
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts thermal-network
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts decentralized
if %errorlevel% neq 0 exit /b %errorlevel%

cea-config optimization --initialind 2 --ngen 2 --halloffame 2 --random-seed 1234
cea trace-inputlocator --scripts optimization
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts multi-criteria-analysis
if %errorlevel% neq 0 exit /b %errorlevel%

