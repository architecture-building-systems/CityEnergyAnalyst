"""This is a really rough attempt at integrating all the documentation processes in one script"""

import os
import cea.config
import cea.scripts
import cea.inputlocator as locator
from subprocess import check_output

all_scripts = cea.scripts.list_scripts()

def get_meta():
    # TODO incorporate into inputlocator method
    import yaml
    metapath = os.path.join(os.path.dirname(cea.config.__file__), 'schemas.yml')
    with open(metapath, 'r') as db:
        metadata = yaml.load(db)
    return metadata


def get_meta_variables():
    # TODO incorporate into inputlocator method
    import yaml
    metapath = os.path.join(os.path.dirname(cea.config.__file__), 'schemas.yml')
    with open(metapath, 'r') as db:
        metadata = yaml.load(db)
    meta_variables = set()
    for locator_method in metadata:
        if not metadata[locator_method]['created_by']:
            script = metadata[locator_method]['file_path'].split('\\')[-1]
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
                VAR = VAR.replace(VAR, 'B01')
            if metadata[locator_method]['file_type'] == 'epw':
                VAR = None
            if metadata[locator_method]['file_type'] == 'xlsx' or metadata[locator_method]['file_type'] == 'xls':
                for var in metadata[locator_method]['schema'][VAR]:
                    meta_variables.add((var, locator_method, 'input:'+script+':'+str(VAR)))
            else:
                meta_variables.add((VAR, locator_method, script))
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
    gloss = gloss.set_index(gloss['VARIABLE'])
    gloss = gloss[~gloss.index.duplicated(keep='first')]

    naming = get_naming()
    metadata = get_meta()
    META_VARIABLES = get_meta_variables()
    # dict containing variables mapped to scripts which wrote them
    # SCRIPT = {}
    #
    # for locator_method in metadata:
    #     if not metadata[locator_method]['created_by']:
    #         scr = metadata[locator_method]['file_path'].split('\\')[-1]
    #     else:
    #         scr = metadata[locator_method]['created_by'][0]
    #     for VAR in metadata[locator_method]['schema']:
    #         if VAR.find('srf') != -1:
    #             VAR = VAR.replace(VAR, 'srf0')
    #         if VAR.find('PIPE') != -1:
    #             VAR = VAR.replace(VAR, 'PIPE0')
    #         if VAR.find('NODE') != -1:
    #             VAR = VAR.replace(VAR, 'NODE0')
    #         if VAR.find('B0') != -1:
    #             VAR = VAR.replace(VAR, 'B01')
    #         if metadata[locator_method]['file_type'] == 'epw':
    #             VAR = None
    #         if metadata[locator_method]['file_type'] == 'xlsx' or metadata[locator_method]['file_type'] == 'xls':
    #             for var in metadata[locator_method]['schema'][VAR]:
    #                 SCRIPT[locator_method] = [scr+':'+VAR, var]
    #         else:
    #             SCRIPT[locator_method] = [scr, VAR]

    # cross reference all variables(in order of priority) with naming.csv, variables_gloss.csv for descriptions
    # cross reference all variables with variables_gloss.csv for TYPE and VALUES
    # if variable not found in either - TO DO labels
    #TODO this could probably be done more easily
    csv = pandas.DataFrame(columns=['VARIABLE', 'SCRIPT', 'DESCRIPTION', 'UNIT', 'TYPE', 'VALUES', 'COLOR'])
    vars = []
    desc = []
    dtype = []
    values = []
    scripts = []
    color = []
    unit = []
    locator_method = []
    oldvar = []
    newvar = []

    for var, method, script in META_VARIABLES:
        scripts.append(script)
        locator_method.append(method)

        if var in list(naming['VARIABLE']):
            vars.append(var)
            desc.append(naming.loc[var]['SHORT_DESCRIPTION'])
            color.append(naming.loc[var]['COLOR'])
            unit.append(naming.loc[var]['UNIT'])
            if var in list(gloss['VARIABLE']):
                dtype.append(gloss.loc[var]['DTYPE'])
                values.append(gloss.loc[var]['VALUES'])
            if var not in list(gloss['VARIABLE']):
                dtype.append('TODO')
                values.append('TODO')

        elif var in list(gloss['VARIABLE']):
            vars.append(var)
            desc.append(gloss.loc[var]['SHORT_DESCRIPTION'])
            dtype.append(gloss.loc[var]['DTYPE'])
            values.append(gloss.loc[var]['VALUES'])
            unit.append(gloss.loc[var]['UNIT'])
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
        for VAR, method, script in META_VARIABLES:
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
    csv = csv.sort_values(by=['SCRIPT', 'LOCATOR_METHOD', 'VARIABLE', 'VALUES'])
    csv.to_csv(output, columns=['SCRIPT', 'LOCATOR_METHOD', 'VARIABLE', 'DESCRIPTION', 'UNIT', 'VALUES', 'TYPE', 'COLOR'], index=False)

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
        naming = pandas.read_csv(NAMING_FILE_PATH)
        naming = naming.set_index(naming['VARIABLE'])
        naming = naming.sort_values(by=['LOCATOR_METHOD','VARIABLE'])

        metadata = get_meta()
        META_VARIABLES = get_meta_variables()

        input_locator_methods = set()
        output_locator_methods = set()
        glossdata = set()

        for locator_method in metadata:
            if metadata[locator_method]['created_by'] == []:
                input_locator_methods.add((locator_method, '-' * len(locator_method)))
            else:
                output_locator_methods.add((locator_method, '-' * len(locator_method)))

        for var in META_VARIABLES:
            if var in list(naming.index):
                glossdata.add(tuple(naming.loc[var]))




        template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
        template = Template(open(template_path, 'r').read())
        output = template.render(headers=input_locator_methods, tuples=glossdata)
        with open('input_files.rst', 'w') as gloss:
            gloss.write(output)

        template_path = os.path.join(documentation_dir, 'templates\\gloss_template.rst')
        template = Template(open(template_path, 'r').read())
        output = template.render(headers=output_locator_methods, tuples=glossdata)
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


