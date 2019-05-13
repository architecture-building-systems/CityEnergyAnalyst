"""
This file implements ``multiprocessing.pool.map``, but captures stdout and stderr.
"""
import sys

def map(number_of_processes, func, iterable, stdout=sys.stdout, stderr=sys.stderr):
    pool =