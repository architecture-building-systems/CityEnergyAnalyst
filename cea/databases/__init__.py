from __future__ import annotations
from typing import TYPE_CHECKING

import os

from cea.datamanagement.database.archetypes import Archetypes
from cea.datamanagement.database.assemblies import Assemblies
from cea.datamanagement.database.components import Components

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

FILE_EXTENSIONS = ['.csv']
databases_folder_path = os.path.dirname(os.path.abspath(__file__))


def get_regions():
    return [folder for folder in os.listdir(databases_folder_path) if folder != "weather"
            and os.path.isdir(os.path.join(databases_folder_path, folder))
            and not folder.startswith('.')
            and not folder.startswith('__')]


def get_weather_files():
    weather_folder_path = os.path.join(databases_folder_path, 'weather')
    return [os.path.splitext(f)[0] for f in os.listdir(weather_folder_path) if f.endswith('.epw')]


class CEADatabase:
    def __init__(self, locator: InputLocator):
        self.assemblies = Assemblies.init_database(locator)
        self.components = Components.init_database(locator)
        self.archetypes = Archetypes.init_database(locator)

    def to_dict(self):
        return {'assemblies': self.assemblies.to_dict(),
                'components': self.components.to_dict(),
                'archetypes': self.archetypes.to_dict()}


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    _dict = CEADatabase(locator).to_dict()
    print(_dict.keys())

