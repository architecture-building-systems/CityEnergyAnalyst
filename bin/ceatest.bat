rem script used to test the cea by the jenkins
rem creates a conda environment (deleting the old one first)

call conda env remove -y -q --name ceatest
call conda env create -q --name ceatest

call activate ceatest

pip.exe install .

rem where cea

cea test --reference-cases open --tasks all --verbosity 1
if %errorlevel% neq 0 exit /b %errorlevel%

call deactivate
