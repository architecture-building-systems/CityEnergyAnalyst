"""This is a really rough attempt at integrating all the documentation processes in one script"""

import os
import cea.config
import cea.scripts
import cea.inputlocator as locator
from subprocess import check_output


def get_meta_variables():
    metadata = cea.scripts.schemas()
    meta_variables = set()
    for locator_method in metadata:
        if not metadata[locator_method]['created_by']:
            script = metadata[locator_method]['file_path'].split('\\')[-1].split('.')[0]
        else:
            script = metadata[locator_method]['created_by'][0]
        for VAR in metadata[locator_method]['schema']:

            if VAR.find('srf') != -1:
                VAR = VAR.replace(VAR, 'srf0')
            if VAR.find('PIPE') != -1:
                VAR = VAR.replace(VAR, 'PIPE0')
            if VAR.find('NODE') != -1:
                VAR = VAR.replace(VAR, 'NODE0')
            if VAR.find('B0') != -1:
                VAR = VAR.replace(VAR, 'B001')
            if metadata[locator_method]['file_type'] == 'epw':
                VAR = 'EPW file variables'
            if metadata[locator_method]['file_type'] == 'xlsx' or metadata[locator_method]['file_type'] == 'xls':
                for var in metadata[locator_method]['schema'][VAR]:

                    file_name = metadata[locator_method]['file_path'].split('\\')[-1] + ':' + VAR
                    meta_variables.add((var, locator_method, script, file_name))
            else:

                file_name = metadata[locator_method]['file_path'].split('\\')[-1]
                meta_variables.add((VAR, locator_method, script, file_name))
    return meta_variables


def get_naming():
    # TODO incorporate into inputlocator method
    import pandas
    NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming.csv')
    naming = pandas.read_csv(NAMING_FILE_PATH)
    naming = naming.set_index(naming['VARIABLE'])
    return naming


def meta_naming_merge(output):
    import pandas
    # create dataframe from variables_gloss.csv without duplicates TODO delete the glossary reference after first run
    gloss_path = os.path.join(os.path.dirname(cea.config.__file__), '../docs/variables_gloss.csv')
    gloss = pandas.read_csv(gloss_path, delimiter=';')
    gloss['key'] = gloss['FILE'] + '!!!' + gloss['VARIABLE']
    gloss_vars = gloss.set_index(['VARIABLE'])
    gloss_vars = gloss_vars.loc[~gloss_vars.index.duplicated(keep='first')]
    gloss = gloss.set_index(['key'])

    naming = get_naming()
    META_VARIABLES = get_meta_variables()

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
            desc.append(naming.loc[var]['SHORT_DESCRIPTION'])
            color.append(naming.loc[var]['COLOR'])
            unit.append(naming.loc[var]['UNIT'])

            if key in list(gloss.index.values):
                dtype.append(gloss.loc[key]['DTYPE'])
                values.append(gloss.loc[key]['VALUES'])

            elif var in list(gloss_vars.index.values):
                dtype.append(gloss_vars.loc[var]['DTYPE'])
                values.append(gloss_vars.loc[var]['VALUES'])

            else:
                dtype.append('TODO')
                values.append('TODO')

        elif key in list(gloss.index.values):
            vars.append(var)
            desc.append(gloss.loc[key]['SHORT_DESCRIPTION'])
            dtype.append(gloss.loc[key]['DTYPE'])
            values.append(gloss.loc[key]['VALUES'])
            unit.append(gloss.loc[key]['UNIT'])
            color.append('black')

        elif var in list(gloss_vars.index.values):
            vars.append(var)
            desc.append(gloss_vars.loc[var]['SHORT_DESCRIPTION'])
            dtype.append(gloss_vars.loc[var]['DTYPE'])
            values.append(gloss_vars.loc[var]['VALUES'])
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

    for var in list(naming['VARIABLE']):
        for VAR, method, script, file_name in META_VARIABLES:
            if var == VAR:
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
    csv.to_csv(output, columns=['SCRIPT', 'LOCATOR_METHOD', 'FILE_NAME','VARIABLE', 'DESCRIPTION', 'UNIT', 'VALUES', 'TYPE', 'COLOR'], index=False, sep=';')

    exceptions = {
        'new_variables': newvar,
        'old_variables': oldvar
    }
    return exceptions


def docs_template_gen(documentation_dir, function):
    from jinja2 import Template
    if function == 'viz':
        print 'sorry, viz method is not working ... yet'
        # template_path = os.path.join(documentation_dir, '\\templates\\viz_template.rst')
        # template = Template(open(template_path, 'r').read())
        # vizfiles = []
        # for script in sorted(all_scripts):
        #     viz_file = os.path.join(metafile, (script.name + '.gv'))
        #     if os.path.isfile(viz_file):
        #         with open(viz_file) as viz:
        #             digraph = viz.read()
        #             underline = '-' * len(script.name)
        #         contents = [[script.name, underline, digraph]]
        #         vizfiles.extend(contents)
        # output = template.render(vizfiles=vizfiles)
        # with open('script-input-outputs.rst', 'w') as vizzz:
        #     vizzz.write(output)

    if function == 'gloss':
        import pandas
        # TODO replace once naming merge has been completed
        NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
        naming = pandas.read_csv(NAMING_FILE_PATH, sep=';')
        naming['key'] = naming['FILE_NAME'] + '!!!' + naming['VARIABLE']
        naming = naming.set_index(['key'])
        naming = naming.sort_values(by=['LOCATOR_METHOD', 'FILE_NAME', 'VARIABLE'])

        metadata = cea.scripts.schemas()
        META_VARIABLES = get_meta_variables()

        input_locator_methods = set()
        output_locator_methods = set()
        glossary_data = set()

        for locator_method in metadata:
            if metadata[locator_method]['created_by'] == []:
                input_locator_methods.add((locator_method, '-' * len(locator_method)))
            else:
                output_locator_methods.add((locator_method, '-' * len(locator_method)))

        for var, locator_method, script, file_name in META_VARIABLES:
            key = file_name + '!!!' + var
            if key in list(naming.index):
                glossary_data.add(tuple(naming.loc[key]))

        # glossary_data = sorted(glossary_data)

        template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
        template = Template(open(template_path, 'r').read())
        output = template.render(headers=input_locator_methods, tuples=glossary_data)
        with open('input_files.rst', 'w') as gloss:
            gloss.write(output)

        template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
        template = Template(open(template_path, 'r').read())
        output = template.render(headers=output_locator_methods, tuples=glossary_data)
        with open('output_files.rst', 'w') as gloss:
            gloss.write(output)

    else:
        print ('The mode you have selected is not valid, please select either <viz> or <gloss>')


def main(config):
    docmode = config.doc.mode

    # easy access to paths, can be incorporated into inputlocator methods later
    originalpath = os.path.curdir
    docspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\docs'))
    ceapath = os.path.join(docspath, '..\\')
    sphinxbuild = os.path.join(docspath, '_build\\html\\index.html')

    # record docs relevant files from git diff
    os.chdir(ceapath)
    gitdiff = check_output('git diff --name-only', shell=True).split('\n')
    preview_docs = set()
    for altered_file in gitdiff:
        if altered_file.split('/')[0] == 'cea' or altered_file.split('/')[0] == 'docs':
            if altered_file.split('.')[-1] == 'py' or altered_file.split('.')[-1] == 'rst':
                preview_docs.add(altered_file)

    # change dir to cea/docs
    os.chdir(docspath)

    if docmode not in config.doc.choices:
        print '%s is not a recognised documentation mode' %docmode

    elif docmode == 'merge':
        output = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming_new.csv')
        exceptions = meta_naming_merge(output)

    elif docmode == 'gloss':
        docs_template_gen(docspath, 'gloss')

    elif docmode == 'viz':
        ## reconstruct trace_data through the metadata and employ viz in one method
        docs_template_gen(docspath, 'viz')
        print 'viz method is not working ... yet'

    elif docmode == 'api':
        os.system('make-api-doc')

    elif docmode == 'clean':
        os.system('make clean')

    elif docmode == 'html':

        # # make the api.rst files fresh for modified modules
        # if os.path.isfile(os.path.join(docspath,'modules\\cea.rst')):
        #     for preview in sorted(preview_docs):
        #         if preview.split('/')[0] == 'cea' and preview.split('.')[-1]=='py':
        #             apipath = os.path.join('..\\', preview).rsplit('.',1)[0]
        #             os.system('sphinx-apidoc -f -M -T -o modules '+apipath)

        # run sphinx build
        os.system('make html')

        # # open preview of modified api.rst or docs.rst html renders
        # if os.path.isfile(sphinxbuild):
        #     os.chdir(os.path.dirname(sphinxbuild))
        #     for preview in sorted(preview_docs):
        #         if preview.split('/')[0]=='cea':
        #             os.chdir(os.path.join(os.path.dirname(sphinxbuild),'modules'))
        #             print os.curdir
        #             preview = preview.rsplit('.',1)[0]
        #             os.startfile(str(preview.replace('/','.')+'.html'))
        #         # elif preview.split('/')[0]=='docs':

    os.chdir(originalpath)



if __name__ == '__main__':
    main(cea.config.Configuration())


