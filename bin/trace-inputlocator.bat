rem run the trace-inputlocator for as many tools as possible, collecting the data

cea-config copy-default-databases --scenario c:\reference-case-WTP-reduced\WTP_MIX_m\
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts copy-default-databases, data-helper
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts radiation-daysim, demand
if %errorlevel% neq 0 exit /b %errorlevel%

rem make sure to run the quicker version (type-scpanel=FP)
cea-config solar-collector --type-scpanel FP
if %errorlevel% neq 0 exit /b %errorlevel%

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

cea trace-inputlocator --scripts thermal-network-matrix
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts decentralized
if %errorlevel% neq 0 exit /b %errorlevel%

cea-config optimization --initialind 2 --ngen 2
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts optimization
if %errorlevel% neq 0 exit /b %errorlevel%

cea trace-inputlocator --scripts plots
if %errorlevel% neq 0 exit /b %errorlevel%

