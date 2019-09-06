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
import functools


class NullPlotCache(object):
    """A dummy cache that doesn't cache anything - for comparing performance of PlotCache"""
    def lookup(self, _, __, producer):
        return producer()

    def lookup_plot_div(self, _, producer):
        return producer()

    def lookup_table_div(self, _, producer):
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

    def _cached_div_file(self, plot):
        data_path = os.path.join(plot.category_name, plot.id())
        return self._cached_data_file(data_path, plot.parameters) + '.div'

    def _cached_table_file(self, plot):
        data_path = os.path.join(plot.category_name, plot.id())
        return self._cached_data_file(data_path, plot.parameters) + '.table.div'

    def lookup(self, data_path, plot, producer):
        cache_timestamp = self.cache_timestamp(self._cached_data_file(data_path, plot.parameters))
        if cache_timestamp < self.newest_dependency(plot.input_files):
            return self.store_cached_value(data_path, plot.parameters, producer)
        return self.load_cached_value(data_path, plot.parameters)

    def lookup_plot_div(self, plot, producer):
        """Lookup the cache of a plot created with plot.plot_div()"""
        div_file = self._cached_div_file(plot)
        cache_timestamp = self.cache_timestamp(div_file)
        if cache_timestamp < self.newest_dependency(plot.input_files):
            plot_div = producer()
            folder = os.path.dirname(div_file)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(div_file, 'w') as div_fp:
                div_fp.write(plot_div)
        else:
            print('Loading plot_div from cache: {div_file}'.format(div_file=div_file))
            with open(div_file, 'r') as div_fp:
                plot_div = div_fp.read()
        return plot_div

    def lookup_table_div(self, plot, producer):
        """Lookup the cache of a table created with plot.table_div()"""
        div_file = self._cached_table_file(plot)
        cache_timestamp = self.cache_timestamp(div_file)
        if cache_timestamp < self.newest_dependency(plot.input_files):
            table_div = producer()
            folder = os.path.dirname(div_file)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(div_file, 'w') as div_fp:
                div_fp.write(table_div)
        else:
            # print('Loading table_div from cache: {div_file}'.format(div_file=div_file))
            with open(div_file, 'r') as div_fp:
                table_div = div_fp.read()
        return table_div

    def cache_timestamp(self, path):
        """Return a timestamp (like ``os.path.getmtime``) to compare to. Returns 0 if there is no data in the cache"""
        if not os.path.exists(path):
            return 0
        else:
            return os.path.getmtime(path)

    def newest_dependency(self, input_files):
        """Returns the newest timestamp (``os.path.getmtime`` and ``time.time()``) of the input_files - the idea being,
        that if the cache is newer than this, then the cache is valid.

        :param input_files: A list of tuples (locator method, args) that, when applied, produce a path"""
        try:
            return max(os.path.getmtime(locator_method(*args)) for locator_method, args in input_files)
        except:
            print('Could not read input files for cache!')
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
        return pd.read_pickle(self._cached_data_file(data_path, parameters))


class MemoryPlotCache(PlotCache):
    """Extend the PlotCache to also keep a copy of the cache in memory"""
    def __init__(self, project):
        super(MemoryPlotCache, self).__init__(project)
        self._cache = {}  # _cached_data_file -> df

    def load_cached_value(self, data_path, parameters):
        """Check memory cache before loading from disk"""
        key = self._cached_data_file(data_path, parameters)
        if not key in self._cache:
            self._cache[key] = super(MemoryPlotCache, self).load_cached_value(data_path, parameters)
        return self._cache[key]

    def store_cached_value(self, data_path, parameters, producer):
        """Update memory cache when storing to disk"""
        data = super(MemoryPlotCache, self).store_cached_value(data_path, parameters, producer)
        key = self._cached_data_file(data_path, parameters)
        self._cache[key] = data
        return data


def cached(producer):
    """Calls to a function wrapped with this decorator are cached using ``self.cache.lookup``"""
    @functools.wraps(producer)
    def wrapper(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, producer.__name__),
                                 plot=self, producer=lambda: producer(self))
    return wrapper