rem script used to test the cea by the jenkins
rem creates a conda environment (deleting the old one first)

rem removing conda environment creation temporarily
rem call conda env remove -y -q --name ceatestall
rem call conda env create -q --name ceatestall

rem call activate ceatestall
call activate cea

pip.exe install -e .

rem where cea

cea test --reference-cases open --tasks all --verbosity 1
if %errorlevel% neq 0 exit /b %errorlevel%

call deactivate


