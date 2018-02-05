"""
Provide a graphical user interface (GUI) to the user configuration file (``cea.config``).
"""
from __future__ import division
from __future__ import print_function

import os
import json
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


class Backend(htmlPy.Object):
    """Contains the backend functions, callable from the GUI."""
    def __init__(self, config):
        super(Backend, self).__init__()
        # Initialize the class here, if required.
        self.config = config

    @htmlPy.Slot(str, str, result=None)
    def save_section(self, section_name, json_data):
        print("Saving section: %s" % section_name)
        print(json_data)
        values = json.loads(json_data)
        print(values)
        for key, value in values.items():
            print("Setting %s to %s" % (key, value))
            self.config.sections[section_name].parameters[key].set(value)
        self.config.save()
        return

    @htmlPy.Slot(str, result=str)
    def get_parameters(self, section_name):
        result = json.dumps({p.name: p.typename for p in self.config.sections[section_name].parameters.values()})
        return result



def main(config):
    """
    Start up the editor to edit the configuration file.

    :param config: the configuration file wrapper object
    :type config: cea.config.Configuration
    :return:
    """
    app = htmlPy.AppGUI(title=u"CEA Configuration File Editor", maximized=False, developer_mode=True)

    app.template_path = os.path.join(BASE_DIR, 'templates')
    app.static_path = os.path.join(BASE_DIR, 'static')

    app.template = ("config_editor.html", {"config": config})
    app.bind(Backend(config), variable_name='backend')
    app.start()


if __name__ == '__main__':
    main(cea.config.Configuration())
