"""
This file implements ``multiprocessing.pool.map``, but captures stdout and stderr.
"""
import sys

# copied from here: https://stackoverflow.com/a/54802737/2260
def chunks(l, n):
    """Yield n number of sequential chunks from l."""
    d, r = divmod(len(l), n)
    for i in range(n):
        si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
        yield l[si:si+(d+1 if i < r else d)]

def map(number_of_processes, func, iterable, stdout=sys.stdout, stderr=sys.stderr):
    pool =