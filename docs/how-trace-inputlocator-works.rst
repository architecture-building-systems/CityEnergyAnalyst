:orphan:

Metadata acquisition
====================

trace-inputlocator
------------------
The CEA contains a tool for the acquisition of metadata specific to each scenario, called via the command line interface
by `cea trace-inputlocator --scripts <script_name>`. As the name suggests, the trace-inputlocator module records which methods are
called from `inputlocator.py` during script execution. Having established which script calls which inputlocator method (and subsequently which file),
the schema for each file is then read. Stored as a yml file within the directory of the current scenario, the keys are as follows:

- 'locator_method':
    - 'description' : the doc string associated with the inputlocator method
    - 'created_by' : list of scripts which are responsible for writing the file (empty list if input file)
    - 'used_by' : list of scripts which read the file (empty list if no dependencies exist)
    - 'file_path' : the absolute path of the file
    - 'file_type' : the file extension (e.g. 'xls' or 'dbf')
    - 'schema' :
        - variable or sheet name (for xls files)
            - 'sample_data' : the last non-null entry of the file
            - 'types_found' : list of python types encountered when reading the file, including None types

Note! The first time metadata is generated, the order of the scripts is important as the 'created_by' list is updated each time a script is run. For example,
if trace-inputlocator is run for 'demand', without having run 'radiation_daysim' previously, the 'created_by' key will remain
erroneously empty for files written by 'radiation_daysim'. Once parent locator methods are accounted for, the script order should not
matter.

An example of the metadata for an 'input' inputlocator method::

 get_archetypes_system_controls:
    created_by: []
    description: " Returns the database of region-specific system control parameters.\
        \ These are copied\n        to the scenario if they are not yet present, based\
        \ on the configured region for the scenario.\n\n        :param region:\n \
        \       :return:\n        "
    file_path: c:\reference-case-open\WTP_CBD_h\databases/CH/archetypes\system_controls.xlsx
    file_type: xlsx
    schema:
        heating_cooling:
            cooling-season-end:
                sample_data: !!python/unicode '09-15'
                types_found: [date]
            cooling-season-start:
                sample_data: !!python/unicode '05-15'
                types_found: [date]
            has-cooling-season:
                sample_data: true
                types_found: [bool]
            has-heating-season:
                sample_data: true
                types_found: [bool]
            heating-season-end:
                sample_data: !!python/unicode '05-14'
                types_found: [date]
            heating-season-start:
                sample_data: !!python/unicode '09-16'
                types_found: [date]
    used_by: [demand]

An example of the metadata for an 'output' inputlocator method::

 get_building_supply:
    created_by: [data-helper]
    description: scenario/inputs/building-properties/building_supply.dbf
    file_path: c:\reference-case-open\WTP_CBD_h\inputs/building-properties\supply_systems.dbf
    file_type: dbf
    schema:
        Name:
            sample_data: B010
            types_found: [string]
        type_cs:
            sample_data: T3
            types_found: [string]
        type_dhw:
            sample_data: T4
            types_found: [string]
        type_el:
            sample_data: T6
            types_found: [string]
        type_hs:
            sample_data: T0
            types_found: [string]
    used_by: [demand, operation-costs, emissions]

CEA Schema
----------
The CEA keeps a copy of a generalized trace-inputlocator output named `cea/schema.yml` and can be accessed
via the `cea.scripts` method: `schema()`.

TODO: Update the schema.yml!
TODO: document the `get_schema_variables(schema)` method
TODO: code and document a `get_schema_dependencies(schema)` method
TODO: code and document a `get_schema_redundancies(schema)` method