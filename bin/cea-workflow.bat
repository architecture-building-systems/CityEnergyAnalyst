rem cea-workflow.bat
rem run a (complete) cea workflow for a given scenario

rem configure variables used for the simulation
set SCENARIO=c:\reference-case-WTP-reduced\WTP_MIX_m
set REGION=SIN
set WEATHER=Singapore-2016

rem run each script, break on error

rem copy-default-databases
echo %date% %time% copy-default-databases begin >> %SCENARIO%\cea-workflow.log
cea copy-default-databases --scenario %SCENARIO% --region %REGION%
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% copy-default-databases end >> %SCENARIO%\cea-workflow.log

rem data-helper
echo %date% %time% data-helper begin >> %SCENARIO%\cea-workflow.log
cea data-helper
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% data-helper end >> %SCENARIO%\cea-workflow.log

rem radiation-daysim
echo %date% %time% radiation-daysim begin >> %SCENARIO%\cea-workflow.log
cea radiation-daysim --weather %WEATHER%
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% radiation-daysim end >> %SCENARIO%\cea-workflow.log

rem demand
echo %date% %time% demand begin >> %SCENARIO%\cea-workflow.log
cea demand --multiprocessing on
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% demand end >> %SCENARIO%\cea-workflow.log

rem emissions
echo %date% %time% emissions begin >> %SCENARIO%\cea-workflow.log
cea emissions
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% emissions end >> %SCENARIO%\cea-workflow.log

rem network-layout
echo %date% %time% network-layout begin >> %SCENARIO%\cea-workflow.log
cea network-layout
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% network-layout end >> %SCENARIO%\cea-workflow.log

rem operation-costs
echo %date% %time% operation-costs begin >> %SCENARIO%\cea-workflow.log
cea operation-costs
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% operation-costs end >> %SCENARIO%\cea-workflow.log

rem photovoltaic
echo %date% %time% photovoltaic begin >> %SCENARIO%\cea-workflow.log
cea photovoltaic
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% photovoltaic end >> %SCENARIO%\cea-workflow.log

rem solar-collector
echo %date% %time% solar-collector FP begin >> %SCENARIO%\cea-workflow.log
cea solar-collector --type-scpanel FP
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% solar-collector FP end >> %SCENARIO%\cea-workflow.log

rem solar-collector
echo %date% %time% solar-collector ET begin >> %SCENARIO%\cea-workflow.log
cea solar-collector --type-scpanel ET
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% solar-collector ET end >> %SCENARIO%\cea-workflow.log

rem photovoltaic-thermal
echo %date% %time% photovoltaic-thermal begin >> %SCENARIO%\cea-workflow.log
cea photovoltaic-thermal
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% photovoltaic-thermal end >> %SCENARIO%\cea-workflow.log

rem sewage-potential
echo %date% %time% sewage-potential begin >> %SCENARIO%\cea-workflow.log
cea sewage-potential
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% sewage-potential end >> %SCENARIO%\cea-workflow.log

rem lake-potential
echo %date% %time% lake-potential begin >> %SCENARIO%\cea-workflow.log
cea lake-potential
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% lake-potential end >> %SCENARIO%\cea-workflow.log

rem thermal-network-matrix
echo %date% %time% thermal-network-matrix begin >> %SCENARIO%\cea-workflow.log
cea thermal-network-matrix
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% thermal-network-matrix end >> %SCENARIO%\cea-workflow.log

rem decentralized
echo %date% %time% decentralized begin >> %SCENARIO%\cea-workflow.log
cea decentralized
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% decentralized end >> %SCENARIO%\cea-workflow.log

rem optimization
echo %date% %time% optimization begin >> %SCENARIO%\cea-workflow.log
cea optimization --individualind 2 ngen 2
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% optimization end >> %SCENARIO%\cea-workflow.log

rem optimization
echo %date% %time% optimization begin >> %SCENARIO%\cea-workflow.log
cea optimization --individualind 5 ngen 5
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% optimization end >> %SCENARIO%\cea-workflow.log

rem plots
echo %date% %time% plots begin >> %SCENARIO%\cea-workflow.log
cea plots
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% plots end >> %SCENARIO%\cea-workflow.log