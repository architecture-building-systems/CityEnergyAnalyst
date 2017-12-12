"""
Provide a graphical user interface (GUI) to the user configuration file (``cea.config``).

This implementation is based on TkInter for maximal portability.
"""
from __future__ import division
from __future__ import print_function

import os
import htmlPy
import cea.config

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
print(BASE_DIR)

def main(config):
    """
    Start up the editor to edit the configuration file.

    :param config: the configuration file wrapper object
    :type config: cea.config.Configuration
    :return:
    """
    app = htmlPy.AppGUI(title=u"CEA Configuration File Editor", maximized=False, developer_mode=True)

    app.template_path = os.path.abspath(BASE_DIR)
    app.static_path = os.path.abspath(BASE_DIR)

    app.template = ("config_editor.html", {"sections": config.sections.values()})
    with open(os.path.expandvars('%TEMP%/config.html'), 'w') as f:
        f.write(app.html)
    app.start()


if __name__ == '__main__':
    main(cea.config.Configuration())
