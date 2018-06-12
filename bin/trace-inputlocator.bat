rem run the trace-inputlocator for as many tools as possible, collecting the data

rem first delete the config file (force default config)
del %userprofile%\cea.config

rem new reference-case in C:\reference-case-open\baseline
cea extract-reference-case

