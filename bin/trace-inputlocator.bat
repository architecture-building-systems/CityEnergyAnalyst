rem run the trace-inputlocator for as many tools as possible, collecting the data

rem first delete the config file (force default config)
del %userprofile%\cea.config

rem new reference-case in C:\reference-case-open\baseline
cea extract-reference-case

cea trace-inputlocator --scripts copy-default-databases, data-helper, radiation-daysim, demand

rem run the two variants of the solar-collector
cea-config solar-collector --type-scpanel ET
cea trace-inputlocator solar-collector
cea-config solar-collector --type-scpanel FP
cea trace-inputlocator solar-collector

cea trace-inputlocator photovoltaic photovoltaic-thermal
cea trace-inputlocator sewage-potential lake-potential