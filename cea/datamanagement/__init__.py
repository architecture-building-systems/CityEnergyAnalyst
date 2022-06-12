from os.path import join, dirname

import osmnx.settings

# Store cache near script
osmnx.settings.cache_folder = join(dirname(__file__), ".cache")
