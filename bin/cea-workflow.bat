rem cea-workflow.bat
rem run a (complete) cea workflow for a given scenario

rem configure variables used for the simulation
if not defined CEA-SCENARIO (
    echo please set CEA-SCENARIO first
    exit /b 1
)

rem run each script, break on error

rem copy-default-databases
echo %date% %time% copy-default-databases begin >> %CEA-SCENARIO%\cea-workflow.log
cea copy-default-databases --scenario %CEA-SCENARIO%
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% copy-default-databases end >> %CEA-SCENARIO%\cea-workflow.log

rem data-helper
echo %date% %time% data-helper begin >> %CEA-SCENARIO%\cea-workflow.log
cea data-helper
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% data-helper end >> %CEA-SCENARIO%\cea-workflow.log

rem radiation-daysim
echo %date% %time% radiation-daysim begin >> %CEA-SCENARIO%\cea-workflow.log
rem cea radiation-daysim
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% radiation-daysim end >> %CEA-SCENARIO%\cea-workflow.log

rem demand
echo %date% %time% demand begin >> %CEA-SCENARIO%\cea-workflow.log
cea demand --multiprocessing on
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% demand end >> %CEA-SCENARIO%\cea-workflow.log

rem emissions
echo %date% %time% emissions begin >> %CEA-SCENARIO%\cea-workflow.log
cea emissions
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% emissions end >> %CEA-SCENARIO%\cea-workflow.log

rem network-layout
echo %date% %time% network-layout begin >> %CEA-SCENARIO%\cea-workflow.log
cea network-layout
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% network-layout end >> %CEA-SCENARIO%\cea-workflow.log

rem operation-costs
echo %date% %time% operation-costs begin >> %CEA-SCENARIO%\cea-workflow.log
cea operation-costs
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% operation-costs end >> %CEA-SCENARIO%\cea-workflow.log

rem photovoltaic
echo %date% %time% photovoltaic begin >> %CEA-SCENARIO%\cea-workflow.log
cea photovoltaic
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% photovoltaic end >> %CEA-SCENARIO%\cea-workflow.log

rem solar-collector
echo %date% %time% solar-collector FP begin >> %CEA-SCENARIO%\cea-workflow.log
cea solar-collector --type-scpanel FP
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% solar-collector FP end >> %CEA-SCENARIO%\cea-workflow.log

rem solar-collector
echo %date% %time% solar-collector ET begin >> %CEA-SCENARIO%\cea-workflow.log
cea solar-collector --type-scpanel ET
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% solar-collector ET end >> %CEA-SCENARIO%\cea-workflow.log

rem photovoltaic-thermal
echo %date% %time% photovoltaic-thermal begin >> %CEA-SCENARIO%\cea-workflow.log
cea photovoltaic-thermal
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% photovoltaic-thermal end >> %CEA-SCENARIO%\cea-workflow.log

rem sewage-potential
echo %date% %time% sewage-potential begin >> %CEA-SCENARIO%\cea-workflow.log
cea sewage-potential
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% sewage-potential end >> %CEA-SCENARIO%\cea-workflow.log

rem lake-potential
echo %date% %time% lake-potential begin >> %CEA-SCENARIO%\cea-workflow.log
cea lake-potential
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% lake-potential end >> %CEA-SCENARIO%\cea-workflow.log

rem thermal-network-matrix
echo %date% %time% thermal-network-matrix begin >> %CEA-SCENARIO%\cea-workflow.log
cea thermal-network-matrix
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% thermal-network-matrix end >> %CEA-SCENARIO%\cea-workflow.log

rem decentralized
echo %date% %time% decentralized begin >> %CEA-SCENARIO%\cea-workflow.log
cea decentralized
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% decentralized end >> %CEA-SCENARIO%\cea-workflow.log

rem optimization
echo %date% %time% optimization begin >> %CEA-SCENARIO%\cea-workflow.log
cea optimization --initialind 2 --ngen 2
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% optimization end >> %CEA-SCENARIO%\cea-workflow.log

rem plots
echo %date% %time% plots begin >> %CEA-SCENARIO%\cea-workflow.log
cea plots
if %errorlevel% neq 0 exit /b %errorlevel%
echo %date% %time% plots end >> %CEA-SCENARIO%\cea-workflow.log