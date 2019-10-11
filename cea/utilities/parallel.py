"""
Standardizes multiprocessing use. In the CEA, some functions are run using the standard ``multiprocessing`` library.
They are run by ``map``ing the function to a list of arguments (see ``multiprocessing.Pool.map_async``) and waiting
for the processes to finish, while at the same time piping STDOUT, STDERR through
``cea.utilities.workerstream.QueueWorkerStream`` - this ensures that the dashboard interface can read the output from
the sub-processes.

The way this was done in CEA < v2.23 included boiler plate code that needed to be repeated every time multiprocessing
was used. Issue [#2344](https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/2344) was a result of
not applying this technique to the demand script.

This module exports the function `map` which is intended to replace both ``map_async`` and the builtin ``map`` function
(which was used when ``config.multiprocessing == False``). This simplifies multiprocessing.
"""
from __future__ import division
from __future__ import print_function

import multiprocessing
import sys
from itertools import repeat
from cea.utilities.workerstream import stream_from_queue, QueueWorkerStream

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def vectorize(func, processes=1):
    """
    Similar to ``numpy.vectorize``, this function wraps ``func`` so that it operates on sequences (of same length)
    of inputs and outputs a sequence of results, similar to ``map(func, *args)``.

    The main point of using ``vectorize`` is to unify single-processing with multi-processing - if processes > 1,
    then multiprocessing is used and the function will be run on a pool of processes. STDOUT and STDERR of these
    processes are fed through a ``cea.workerstream.QueueWorkerStream`` so it can be shown in the dashboard job output.

    Note: the if processes > 1, then the first argument to the vectorized ``func`` will be converted to a list before
    running. This should not have any side effects, but is necessary if the args are constructed with ``itertools.repeat``.
    """
    if processes > 1:
        return __multiprocess_wrapper(func, processes)
    else:
        return single_process_wrapper(func)


def __multiprocess_wrapper(func, processes):
    """Create a worker pool to map the function, taking care to set up STDOUT and STDERR"""
    def wrapper(*args):
        print("Using {processes} CPU's".format(processes=processes))
        pool = multiprocessing.Pool(processes)
        queue = multiprocessing.Manager().Queue()

        # make sure the first arg is a list (not a generator) since we need the length of the sequence
        args = [list(a) for a in args]
        n = len(args[0])  # the number of iterations to map
        args = [list(repeat(func, n)), list(repeat(queue, n))] + args
        args = zip(*args)

        map_result = pool.map_async(__apply_func_with_worker_stream, args)

        while not map_result.ready():
            stream_from_queue(queue)
        result = map_result.get()

        pool.close()
        pool.join()

        # process the rest of the Queue
        while not queue.empty():
            stream_from_queue(queue)
        return result
    return wrapper


def __apply_func_with_worker_stream(args):
    """
    Call func, using ``queue`` to redirect stdout and stderr, with a tuple of args because multiprocessing.Pool.map
    only accepts one argument for the function.

    This function is called _inside_ a separate process.
    """
    func, queue, args = args[0], args[1], args[2:]
    # set up printing to stderr and stdout to go through the queue
    sys.stdout = QueueWorkerStream('stdout', queue)
    sys.stderr = QueueWorkerStream('stderr', queue)
    return func(*args)


def single_process_wrapper(func):
    """The simplest form of vectorization: Just use the python builtin ``map``"""
    def wrapper(*args):
        print("Using single process")
        return map(func, *args)
    return wrapper


def test(a, b):
    print("test {a}+{b}".format(a=a, b=b))
    return a + b


if __name__ == '__main__':
    print(vectorize(test, 4)(range(10, 20), range(20, 30)))