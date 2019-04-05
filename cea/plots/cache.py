"""
Implements a cache for plot data at the project level. Cached plot data has a "path" (e.g. 'optimization/generations_data')
and dependencies (a list of files that are used to produce that data) as well as the parameters used in that data.
The cache object is passed to the `calc_graph` method and the plot is responsible for retrieving data from the cache.
"""

from __future__ import division
from __future__ import print_function
import os
import time
import hashlib
import pandas as pd


class NullPlotCache(object):
    """A dummy cache that doesn't cache anything - for comparing performance of PlotCache"""
    def lookup(self, _, __, producer):
        return producer()


class PlotCache(object):
    """A cache for plot data. Use the ``lookup`` method to retrieve data from the cache."""
    def __init__(self, project):
        """Initialize the cache from disk"""
        self.parameter_guard = {}  # data_path => set(parameters.keys()) - just a check for programming errors
        self.project = project

    def _parameter_hash(self, parameters):
        return hashlib.md5(repr(sorted(parameters.items()))).hexdigest()

    def _cached_data_file(self, data_path, parameters):
        return os.path.join(self.project, '.cache', data_path, self._parameter_hash(parameters))

    def lookup(self, data_path, plot, producer):
        if self.cache_timestamp(data_path, plot.parameters) < self.newest_dependency(plot.input_files):
            return self.store_cached_value(data_path, plot.parameters, producer)
        return self.load_cached_value(data_path, plot.parameters)

    def cache_timestamp(self, data_path, parameters):
        """Return a timestamp (like ``os.path.getmtime``) to compare to. Returns 0 if there is no data in the cache"""
        data_file = self._cached_data_file(data_path, parameters)
        if not os.path.exists(data_file):
            return 0
        else:
            return os.path.getmtime(data_file)

    def newest_dependency(self, input_files):
        """Returns the newest timestamp (``os.path.getmtime`` and ``time.time()``) of the input_files - the idea being,
        that if the cache is newer than this, then the cache is valid."""
        try:
            return max(os.path.getmtime(f) for f in input_files)
        except:
            print('Could not read input_files for cache!')
            return time.time()

    def store_cached_value(self, data_path, parameters, producer):
        """Store the Dataframe returned from producer and return it."""
        data = producer()
        data_folder = os.path.join(self.project, '.cache', data_path)
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        data.to_pickle(self._cached_data_file(data_path, parameters))
        return data

    def load_cached_value(self, data_path, parameters):
        """Load a Dataframe from disk"""
        return pd.read_pickle(self.cache_timestamp(data_path, parameters))

