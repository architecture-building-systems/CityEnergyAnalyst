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
__version__ = "2.14"
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
    schema_variables = cea.scripts.get_schema_variables()

    # TODO replace once naming merge has been completed

    naming = locator.get_naming()
    naming = pandas.read_csv(naming)
    naming = naming.set_index(naming['VARIABLE'])

    # naming = pandas.read_csv(locator.get_naming(), sep=',')
    # naming['key'] = naming['FILE_NAME'] + '!!!' + naming['VARIABLE']
    # naming = naming.set_index(['key'])
    # naming = naming.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])

    # cross reference all variables(in order of priority) with naming.csv, variables_gloss.csv for descriptions
    # cross reference all variables with variables_gloss.csv for TYPE and VALUES
    # if variable not found in either - TO DO labels

    #TODO this could probably be done better
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
    old_variables = []
    new_variables = []

    for variable, method, script, file_name in schema_variables:
        key = file_name + '!!!' + variable
        scripts.append(script)
        locator_method.append(method)
        files.append(file_name)

        if variable in list(naming['VARIABLE']):
            vars.append(variable)
            desc.append(str(naming.loc[variable]['SHORT_DESCRIPTION']))
            color.append(naming.loc[variable]['COLOR'])
            unit.append(naming.loc[variable]['UNIT'])

            if key in list(gloss.index.values):
                dtype.append(gloss.loc[key]['DTYPE'])
                values.append(str(gloss.loc[key]['VALUES']))

            elif variable in list(gloss_vars.index.values):
                dtype.append(gloss_vars.loc[variable]['DTYPE'])
                values.append(str(gloss_vars.loc[variable]['VALUES']))

            else:
                dtype.append('TODO')
                values.append('TODO')

        elif key in list(gloss.index.values):
            vars.append(variable)
            desc.append(str(gloss.loc[key]['SHORT_DESCRIPTION']))
            dtype.append(gloss.loc[key]['DTYPE'])
            values.append(str(gloss.loc[key]['VALUES']))
            unit.append(gloss.loc[key]['UNIT'])
            color.append('black')

        elif variable in list(gloss_vars.index.values):
            vars.append(variable)
            desc.append(str(gloss_vars.loc[variable]['SHORT_DESCRIPTION']))
            dtype.append(gloss_vars.loc[variable]['DTYPE'])
            values.append(str(gloss_vars.loc[variable]['VALUES']))
            unit.append(gloss_vars.loc[variable]['UNIT'])
            color.append('black')

        else:
            vars.append(variable)
            desc.append('TODO')
            dtype.append('TODO')
            values.append('TODO')
            color.append('black')
            unit.append('TODO')
            new_variables.append(variable)

    # todo: make this more specific once glossary part removed
    list_of_variables = []
    for variable, method, script, file_name in schema_variables:
        list_of_variables.append(variable)

    # keep a record of the variables which are in naming.csv but not in
    # the schema.yml (i.e. potentially outdated variables)
    for variable in list(naming['VARIABLE']):
        if variable not in list_of_variables:
                old_variables.append(variable)

    exceptions = {
        'new_variables': new_variables,
        'old_variables': old_variables
    }

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



    print 'The following variables have not been documented in naming.csv:'
    for variable in exceptions['new_variables']:
        print variable
    print '\n'
    print 'The following variables do not exist within the schema.yml and could be outdated:'
    for variable in exceptions['old_variables']:
        print variable

    print '\n~~~~~~~~ Merge complete ~~~~~~~~ \n'

    return exceptions



if __name__ == '__main__':
    # Todo replace with inputlocator method 'get_naming' once first run is complete
    main(os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv'))