import os
import cea.config
import cea.scripts
from subprocess import check_output

all_scripts = cea.scripts.list_scripts()

def get_script_dependencies(viz_path):
    dependencies = []
    for script in sorted(all_scripts):
        viz_file = os.path.join(os.path.curdir, (script.name + '.gv'))
        if os.path.isfile(viz_file):
            with open(viz_file) as viz:
                digraph = viz.read()
                underline = '-' * len(script.name)
            contents = [[script.name, underline, digraph]]
            dependencies.extend(contents)
    return dependencies

def meta_naming_merge(meta_location, output):
    import pandas
    import yaml

    # create dataframe from variables_gloss.csv without duplicates
    gloss_path = os.path.join(os.path.dirname(cea.config.__file__), '../docs/variables_gloss.csv')
    gloss = pandas.read_csv(gloss_path, delimiter=';')
    gloss = gloss.set_index(gloss['VARIABLE'])
    gloss = gloss[~gloss.index.duplicated(keep='first')]

    # create dataframe from naming.csv
    NAMING_FILE_PATH = os.path.join(os.path.dirname(cea.config.__file__), 'plots/naming.csv')
    naming = pandas.read_csv(NAMING_FILE_PATH)
    naming = naming.set_index(naming['VARIABLE'])

    # create dataframe from trace_inputlocator.output.yml
    TRACE_PATH = os.path.join(os.path.dirname(meta_location), 'baseline\\outputs\\trace_inputlocator.output.yml')
    with open(TRACE_PATH, 'r') as db:
        TRACE = yaml.load(db)

    # set of unique variables in trace_inputlocator.output.yml
    TRACE_DATA = set()
    # dict containing variables mapped to scripts which wrote them
    SCRIPT = {}
    for index in TRACE:
        if not TRACE[index]['created_by']:
            scr = 'primary_input'
        else:
            scr = TRACE[index]['created_by'][0]
        for VAR in TRACE[index]['schema']:
            if VAR.find('srf') != -1:
                VAR = VAR.replace(VAR, 'srf0')
            if VAR.find('PIPE') != -1:
                VAR = VAR.replace(VAR, 'PIPE0')
            if VAR.find('NODE') != -1:
                VAR = VAR.replace(VAR, 'NODE0')
            if VAR.find('B0') != -1:
                VAR = VAR.replace(VAR, 'B01')
            if TRACE[index]['file_type'] == 'epw':
                VAR = None
            if TRACE[index]['file_type'] == 'xlsx':
                for var in TRACE[index]['schema'][VAR]:
                    TRACE_DATA.add(var)
                    SCRIPT[var] = scr
            else:
                TRACE_DATA.add(VAR)
                SCRIPT[VAR] = scr

    # cross reference all variables(in order of priority) with naming.csv, variables_gloss.csv for descriptions
    # cross reference all variables with variables_gloss.csv for TYPE and VALUES
    # if variable not found in either - TO DO labels
    csv = pandas.DataFrame(columns=['VARIABLE', 'SCRIPT', 'DESCRIPTION', 'TYPE', 'VALUES'])
    vars = []
    desc = []
    dtype = []
    values = []
    script = []
    for var in TRACE_DATA:
        script.append(SCRIPT[var])
        if var in list(naming['VARIABLE']):
            vars.append(var)
            desc.append(naming.loc[var]['SHORT_DESCRIPTION'])
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
        else:
            vars.append(var)
            desc.append('TODO')
            dtype.append('TODO')
            values.append('TODO')

    # assign to dataframe and write
    csv['VARIABLE'] = vars
    csv['DESCRIPTION'] = desc
    csv['TYPE'] = dtype
    csv['VALUES'] = values
    csv['SCRIPT'] = script
    csv = csv.sort_values(by=['SCRIPT', 'VARIABLE', 'VALUES'])
    csv.to_csv(output, columns=['SCRIPT', 'VARIABLE', 'DESCRIPTION', 'VALUES', 'TYPE'], index=False)

def main(config):
    docmode = config.doc.mode

    # easy access to paths
    originalpath = os.path.curdir
    docspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\docs'))
    ceapath = os.path.join(docspath, '..\\')
    sphinxbuild = os.path.join(docspath, '_build\\html\\index.html')

    # record the change files in git diff
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

    elif docmode == 'gloss':
        import cea.inputlocator

        locator = cea.inputlocator.InputLocator(config.Configuration().scenario).scenario
        print locator
        output = os.path.join(os.path.dirname(cea.config.__file__), 'tests/variable_declaration.csv')

        undeclared_vars = meta_naming_merge(locator, output)


    elif docmode == 'viz':
        from jinja2 import Template

        template_path = os.path.join(docspath, '\\templates\\script_dependencies_template.rst')
        template = Template(open(template_path, 'r').read())
        dependencies = get_script_dependencies()
        output = template.render(dependencies=dependencies)
        os.chdir(os.path.join('..copy output from command line python\\', os.curdir))
        with open('script-input-outputs.rst', 'w') as cea:
            cea.write(output)

    elif docmode == 'api':
        os.system('make-api-doc')

    elif docmode == 'clean':
        os.chdir('modules')
        print 'Removing existing module api builds'
        os.system('del cea*.rst')
        os.chdir(docspath)
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


