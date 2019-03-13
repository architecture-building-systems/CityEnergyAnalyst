import os
import cea.config as config
import cea.inputlocator
import pandas

locator = cea.inputlocator.InputLocator(config.Configuration().scenario)
fields = ['VARIABLE','DTYPE','UNIT','DESCRIPTION','VALUES']
# VAR_PATH = os.path.join(os.path.dirname(cea.config.__file__), r'docs/variables_gloss.csv')
gloss_path = r'C:\Users\Jack\Documents\GitHub\CityEnergyAnalyst\docs\variables_gloss.csv'
VAR = pandas.read_csv(gloss_path, usecols = fields, delimiter = ';')
VAR = VAR.set_index(VAR['VARIABLE'])
VAR = VAR[~VAR.index.duplicated(keep='first')]


    # CATEGORY,VARIABLE,UNIT,SHORT_DESCRIPTION,COLOR,TYP_VAL,
fields = ['VARIABLE','UNIT','SHORT_DESCRIPTION']
NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming.csv')
naming = pandas.read_csv(NAMING_FILE_PATH, usecols=fields)
variables = naming.set_index(naming['VARIABLE'])

for index in VAR.index:
    if index in list(variables.index):
        print 'yes'
    else:
        print index



