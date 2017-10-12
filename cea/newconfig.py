from __future__ import print_function

"""
Manage configuration information for the CEA. See the cascading configuration files section in the documentation
for more information on configuration files.
"""

import os
import tempfile
import ConfigParser
import cea.databases

from cea.utilities.configuration_base import ConfigurationBase, Section, Parameter, Path, Boolean, String

class Configuration(ConfigurationBase):
    def __init__(self, scenario=None):
        self.general = Section('general',
            Parameter('default-scenario', type=Path, help=''),
            Parameter('weather', type=Path, help=''),
            Parameter('multiprocessing', type=Boolean, help=''),
            Parameter('region', type=String, help=''))

