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
from subprocess import check_output

__author__ = "Jack Hawthorne"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jack Hawthorne"]
__license__ = "MIT"
__version__ = "2.14"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

locator = cea.inputlocator.InputLocator(cea.config.Configuration().scenario)

def preview_set():
    """
    This method performs a Gitdiff, storing the documentation relevant change files as a set.
    :return: preview_docs: set of documentation relevant files produced by Gitdiff
    """
    os.chdir(os.path.dirname(cea.__file__))

    gitdiff = check_output('git diff --name-only', shell=True).split('\n')
    preview_docs = set()
    for altered_file in gitdiff:
        if altered_file.split('/')[0] == 'cea' or altered_file.split('/')[0] == 'docs':
            if altered_file.split('.')[-1] == 'py' or altered_file.split('.')[-1] == 'rst':
                preview_docs.add(altered_file)

    return preview_docs


def rebuild_altered_module_documentation(preview_docs):
    """

    sphinx-apidoc skips any pre-existing module api documentation, even if changes have occurred.
    This method deletes any old api documentation, rebuilding relevant cea.modules.rst files.

    :param preview_docs: set of documentation relevant files produced by Gitdiff
    :return: none
    """

    for doc in preview_docs:
        if doc.split('.')[-1] == 'py' and doc.split('/')[0] == 'cea':
            print 'Rebuilding %s api documentation' % doc

            rst_name = doc.rsplit('/', 1)[0].replace('/', '.')+'.rst'
            if os.path.isfile('modules/%s' % rst_name):
                os.system('del modules/%s' % rst_name)
                if not os.path.isfile('../%s' % doc):
                    os.system('del modules/%s' % rst_name)
    os.system('make-api-doc')


def main(documentation_dir):
    # get all relevant change files
    preview_files = preview_set()
    # change the dir to docs
    os.chdir(documentation_dir)
    # compare python modules to pre-existing documentation and rebuild
    rebuild_altered_module_documentation(preview_files)
    # run the make.bat from docs
    os.system('make html')

    # next step ----- make the changed files automatically open for sphinx build checking
    # for doc in Preview:
        # os.system('./_build/html/%s') etc....