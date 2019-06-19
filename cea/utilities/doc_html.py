"""
doc_html.py

This script performs the following:
    - Cross references the api documentation, building new files and deleting outdated ones.
    - Runs a sphinx html build from the docs directory via the docs make.bat
    - Opens the html files of the corresponding change files from Gitdiff (not yet functional)

"""
import cea.config
import cea.inputlocator
import os
import subprocess

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)


def preview_files(documentation_dir):
    """
    This method performs a Gitdiff, storing the documentation relevant change files as a set.
    """
    cea_path = os.path.dirname(cea.__file__)

    gitdiff = subprocess.check_output('git diff --name-only', shell=True, cwd=cea_path, stderr=open(os.devnull, 'wb')).split('\n')

    preview_docs = set()

    # the directories and file types docs is concerned with
    dir_list = ['cea', 'docs']
    file_types = ['py', 'rst']

    for altered_file in gitdiff:
        dir_name = altered_file.split('/')[0]
        file_type = altered_file.split('.')[-1]
        if dir_name in dir_list and file_type in file_types:
            preview_docs.add(altered_file)

    for doc in preview_docs:
        print doc
        if os.path.basename(os.path.dirname(doc)) != 'modules' and doc.rsplit('.')[-1] == 'py':
            preview_html = os.path.dirname(doc).replace('/', '.')+'.html'
            os.system(os.path.join(os.path.abspath(documentation_dir), '_build', 'html', 'modules', preview_html))
        if os.path.dirname(doc) == 'docs':
            preview_html = os.path.basename(doc).rsplit('.', 1)[0] + '.html'
            os.system(os.path.join(documentation_dir, '_build', 'html', preview_html))


def get_all_module_rsts(cea_path):
    module_rst_set = set()
    for dirpath, dirnames, filenames in os.walk(cea_path):
        rel_path = os.path.relpath(dirpath, os.path.join(cea_path, '..'))
        for module in filenames:
            if module.rsplit('.')[-1] == 'py':
                module_rst_set.add(rel_path.replace(os.sep, '.') + '.rst')
    return module_rst_set


def rebuild_altered_module_documentation(documentation_dir):
    """
    This method deletes any old api documentation; rebuilding relevant cea.modules.rst files.
    """

    module_rst_set = get_all_module_rsts(os.path.abspath(os.path.join(documentation_dir, '..', 'cea')))

    # if the rst exists but the module does not, delete the documentation for it
    for document in os.listdir(os.path.join(documentation_dir, 'modules')):
        if document not in module_rst_set and document != 'modules.rst':
            print 'Removing %s documentation' % document
            os.remove(os.path.join(documentation_dir, 'modules', document))
    subprocess.check_call(os.path.join(documentation_dir, 'make-api-doc.bat'), cwd=documentation_dir)


def main(_):
    documentation_dir = os.path.join(os.path.dirname(os.path.dirname(cea.config.__file__)), 'docs')

    # compare python modules to pre-existing documentation and rebuild
    # rebuild_altered_module_documentation(documentation_dir)

    # run the make.bat from docs
    # subprocess.check_call([os.path.join(documentation_dir, 'make.bat'), 'html'])

    # preview uncommitted module and documentation htmls
    preview_files(documentation_dir)


