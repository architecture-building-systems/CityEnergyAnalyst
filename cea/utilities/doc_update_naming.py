"""
doc_update_naming.py

Rebuilds all restructured text files for the api documentation
Returns a dict containing potentially outdated files and ones yet to be documented.

"""
import cea.config
import cea.scripts
import cea.inputlocator
import os
import pandas

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(output):
    locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)

    # create dataframe from variables_gloss.csv without duplicates TODO delete the glossary reference after first run
    gloss_path = os.path.join(os.path.dirname(cea.config.__file__), '../docs/variables_gloss.csv')
    gloss = pandas.read_csv(gloss_path, delimiter=';')
    gloss['key'] = gloss['FILE'] + '!!!' + gloss['VARIABLE']
    gloss_vars = gloss.set_index(['VARIABLE'])
    gloss_vars = gloss_vars.loc[~gloss_vars.index.duplicated(keep='first')]
    gloss = gloss.set_index(['key'])

    # geta all variable sets from the trace.inputlocator schema
    META_VARIABLES = cea.scripts.get_schema_variables()

    # TODO replace once naming merge has been completed

    naming = locator.get_naming()
    naming = pandas.read_csv(naming)
    naming = naming.set_index(naming['VARIABLE'])

    # naming = pandas.read_csv(locator.get_naming(), sep=',')
    # naming['key'] = naming['FILE_NAME'] + '!!!' + naming['VARIABLE']
    # naming = naming.set_index(['key'])
    # naming = naming.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])

    # NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
    # naming = pandas.read_csv(NAMING_FILE_PATH, sep=';')
    # naming['key'] = naming['FILE_NAME'] + '!!!' + naming['VARIABLE']
    # naming = naming.set_index(['key'])
    # naming = naming.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])


    # cross reference all variables(in order of priority) with naming.csv, variables_gloss.csv for descriptions
    # cross reference all variables with variables_gloss.csv for TYPE and VALUES
    # if variable not found in either - TO DO labels

    #TODO this could probably be done more easily
    csv = pandas.DataFrame()
    vars = []
    desc = []
    dtype = []
    values = []
    scripts = []
    color = []
    unit = []
    locator_method = []
    files = []
    oldvar = []
    newvar = []


    for var, method, script, file_name in META_VARIABLES:
        key = file_name + '!!!' + var
        scripts.append(script)
        locator_method.append(method)
        files.append(file_name)

        if var in list(naming['VARIABLE']):
            vars.append(var)
            desc.append(str(naming.loc[var]['SHORT_DESCRIPTION']))
            color.append(naming.loc[var]['COLOR'])
            unit.append(naming.loc[var]['UNIT'])

            if key in list(gloss.index.values):
                dtype.append(gloss.loc[key]['DTYPE'])
                values.append(str(gloss.loc[key]['VALUES']))

            elif var in list(gloss_vars.index.values):
                dtype.append(gloss_vars.loc[var]['DTYPE'])
                values.append(str(gloss_vars.loc[var]['VALUES']))

            else:
                dtype.append('TODO')
                values.append('TODO')

        elif key in list(gloss.index.values):
            vars.append(var)
            desc.append(str(gloss.loc[key]['SHORT_DESCRIPTION']))
            dtype.append(gloss.loc[key]['DTYPE'])
            values.append(str(gloss.loc[key]['VALUES']))
            unit.append(gloss.loc[key]['UNIT'])
            color.append('black')

        elif var in list(gloss_vars.index.values):
            vars.append(var)
            desc.append(str(gloss_vars.loc[var]['SHORT_DESCRIPTION']))
            dtype.append(gloss_vars.loc[var]['DTYPE'])
            values.append(str(gloss_vars.loc[var]['VALUES']))
            unit.append(gloss_vars.loc[var]['UNIT'])
            color.append('black')

        else:
            vars.append(var)
            desc.append('TODO')
            dtype.append('TODO')
            values.append('TODO')
            color.append('black')
            unit.append('TODO')
            newvar.append(var)

    # todo: make this more specific once glossary part removed
    schema_variables = []
    for VAR, method, script, file_name in META_VARIABLES:
        schema_variables.append(VAR)
    for var in list(naming['VARIABLE']):
        if var not in schema_variables:
                oldvar.append(var)

    # assign to dataframe and write
    csv['VARIABLE'] = vars
    csv['DESCRIPTION'] = desc
    csv['TYPE'] = dtype
    csv['VALUES'] = values
    csv['SCRIPT'] = scripts
    csv['UNIT'] = unit
    csv['COLOR'] = color
    csv['LOCATOR_METHOD'] = locator_method
    csv['FILE_NAME'] = files
    csv = csv.sort_values(by=['SCRIPT', 'LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE', 'VALUES'])
    csv.to_csv(output, columns=['SCRIPT', 'LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE', 'DESCRIPTION', 'UNIT', 'VALUES', 'TYPE', 'COLOR'], index=False, sep=',')

    exceptions = {
        'new_variables': newvar,
        'old_variables': oldvar
    }

    print 'The following variables have not been documented in naming.csv:'
    for var in exceptions['new_variables']:
        print var
    print '\n'
    print 'The following variables do not exist within the schema.yml and could be outdated:'
    for var in exceptions['old_variables']:
        print var

    print '\n~~~~~~~~ Merge complete ~~~~~~~~ '

    return exceptions



if __name__ == '__main__':
    # Todo replace with inputlocator method 'get_naming' once first run is complete
    main(os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv'))