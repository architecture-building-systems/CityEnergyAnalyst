"""
"Makefile" for doit to test the whole package with Jenkins.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import requests
import os



def task_download_reference_case_zug():
    """Download the (current) state of the reference-case-zug"""
    def download_reference_case_zug():
        with open(os.path.expandvars(r'%TEMP%\cea-reference-case.zip')) as f:
            f.write(r.content, 'wb')

    return {
        'actions': [download_reference_case_zug],
        'targets': [r'c:\reference-case-zug\baseline\input']
    }
