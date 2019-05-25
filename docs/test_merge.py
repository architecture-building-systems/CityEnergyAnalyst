import os
import cea.config as config
import cea.inputlocator
import pandas
import yaml
import cea.doc

locator = cea.inputlocator.InputLocator(config.Configuration().scenario).scenario
output = os.path.join(os.path.dirname(cea.config.__file__), 'tests/variable_declaration.csv')

#TODO replace once naming merge has been completed
NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
naming = pandas.read_csv(NAMING_FILE_PATH)
naming = naming.set_index(naming['VARIABLE'])

metadata = cea.doc.get_meta()
META_VARIABLES = cea.doc.get_meta_variables()


input_locator_methods = set()
output_locator_methods = set()
glossdata = set()




for locator_method in metadata:
    if metadata[locator_method]['used_by'] == []:
        input_locator_methods.add((locator_method,'-'*len(locator_method)))
    else:
        output_locator_methods.add((locator_method,'-'*len(locator_method)))

for var in META_VARIABLES:
    if var in list(naming.index):
        glossdata.add(tuple(naming.loc[var]))

    # else:
    #
    # variable, description, unit, values, type, method



# # create dataframe from variables_gloss.csv without duplicates
# gloss_path = os.path.join(os.path.dirname(cea.config.__file__), '../docs/variables_gloss.csv')
# gloss = pandas.read_csv(gloss_path, delimiter = ';')
# gloss = gloss.set_index(gloss['VARIABLE'])
# gloss = gloss[~gloss.index.duplicated(keep='first')]
#
# # create dataframe from naming.csv
# NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming.csv')
# naming = pandas.read_csv(NAMING_FILE_PATH)
# naming = naming.set_index(naming['VARIABLE'])
#
# # create dataframe from trace_inputlocator.output.yml
# TRACE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'tests/trace_inputlocator.output.new.yml')
# with open(TRACE_PATH, 'r') as db:
#     TRACE = yaml.load(db)
#
# # set of unique variables in trace_inputlocator.output.yml
# TRACE_DATA = set()
# # dict containing variables mapped to scripts which wrote them
# SCRIPT = {}
# for index in TRACE:
#     if not TRACE[index]['created_by']:
#         scr = 'primary input: '+ str(TRACE[index]['file_path'].split('\\')[-1])
#     else:
#         scr = TRACE[index]['created_by'][0]
#     for VAR in TRACE[index]['schema']:
#         if VAR.find('srf') != -1:
#             VAR = VAR.replace(VAR,'srf0')
#         if VAR.find('PIPE') != -1:
#             VAR = VAR.replace(VAR,'PIPE0')
#         if VAR.find('NODE') != -1:
#             VAR = VAR.replace(VAR,'NODE0')
#         if VAR.find('B0') != -1:
#             VAR = VAR.replace(VAR,'B01')
#         if TRACE[index]['file_type'] == 'epw':
#             VAR = None
#         if TRACE[index]['file_type'] == 'xlsx' or TRACE[index]['file_type'] == 'xls':
#             for var in TRACE[index]['schema'][VAR]:
#                 TRACE_DATA.add(var)
#                 SCRIPT[var] = scr
#         else:
#             TRACE_DATA.add(VAR)
#             SCRIPT[VAR] = scr
#
#
# # cross reference all variables(in order of priority) with naming.csv, variables_gloss.csv for descriptions
# # cross reference all variables with variables_gloss.csv for TYPE and VALUES
# # if variable not found in either - TO DO labels
# csv = pandas.DataFrame(columns=['VARIABLE', 'SCRIPT', 'DESCRIPTION', 'UNIT', 'TYPE', 'VALUES', 'COLOR'])
# vars = []
# desc = []
# dtype = []
# values = []
# script = []
# color = []
# unit = []
# oldvar = []
# newvar = []
# for var in TRACE_DATA:
#     script.append(SCRIPT[var])
#     if var in list(naming['VARIABLE']):
#         vars.append(var)
#         desc.append(naming.loc[var]['SHORT_DESCRIPTION'])
#         color.append(naming.loc[var]['COLOR'])
#         unit.append(naming.loc[var]['UNIT'])
#         if var in list(gloss['VARIABLE']):
#             dtype.append(gloss.loc[var]['DTYPE'])
#             values.append(gloss.loc[var]['VALUES'])
#         if var not in list(gloss['VARIABLE']):
#             dtype.append('TODO')
#             values.append('TODO')
#
#     elif var in list(gloss['VARIABLE']):
#         vars.append(var)
#         desc.append(gloss.loc[var]['SHORT_DESCRIPTION'])
#         dtype.append(gloss.loc[var]['DTYPE'])
#         values.append(gloss.loc[var]['VALUES'])
#         unit.append(gloss.loc[var]['UNIT'])
#         color.append('black')
#
#     else:
#         vars.append(var)
#         desc.append('TODO')
#         dtype.append('TODO')
#         values.append('TODO')
#         color.append('black')
#         unit.append('TODO')
#         newvar.append(var)
#
# for var in list(naming['VARIABLE']):
#     if var not in TRACE_DATA:
#         oldvar.append(var)
#
#
# # assign to dataframe and write
# csv['VARIABLE'] = vars
# csv['DESCRIPTION'] = desc
# csv['TYPE'] = dtype
# csv['VALUES'] = values
# csv['SCRIPT'] = script
# csv['UNIT'] = unit
# csv['COLOR'] = color
# csv = csv.sort_values(by=['SCRIPT','VARIABLE','VALUES'])
# csv.to_csv(output,columns=['SCRIPT','VARIABLE','DESCRIPTION','UNIT','VALUES', 'TYPE','COLOR'], index=False)
#
# oldvar
# print newvar
#
