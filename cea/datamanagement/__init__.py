import os
import osmnx.settings

# Enable caching to reduce chance of timeouts due to API rate limiting (default is True)
osmnx.settings.use_cache = True

# Use os.path.join() for cross-platform path handling
cache_dir = os.path.expanduser("~") # Gets home directory on both Windows (~) and Linux ($HOME)
cache_folder = os.path.join(cache_dir, ".cache", "osmnx")
osmnx.settings.cache_folder = cache_folder

# Enable logging for debugging 
osmnx.settings.log_console = True
