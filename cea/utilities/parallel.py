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
from typing import TypeVar, ParamSpec, Callable, Any, List

import multiprocessing
import sys
import logging
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

P = ParamSpec('P')
T = TypeVar('T')
CallbackFunc = Callable[[int, int, tuple, Any], None]


def vectorize(
    func: Callable[P, T],
    processes: int = 1,
    on_complete: CallbackFunc | None = None
) -> Callable[..., List[T]]:
    """
    Similar to ``numpy.vectorize``, this function wraps ``func`` so that it operates on sequences (of same length)
    of inputs and outputs a sequence of results, similar to ``map(func, *args)``.

    The main point of using ``vectorize`` is to unify single-processing with multi-processing - if processes > 1,
    then multiprocessing is used and the function will be run on a pool of processes. STDOUT and STDERR of these
    processes are fed through a ``cea.workerstream.QueueWorkerStream`` so it can be shown in the dashboard job output.

    The parameter ``on_complete`` is an optional callable that is called for each completed call of ``func``. It takes
    4 arguments:

    - i: the 0-based order in which this call was completed
    - n: the total number of function calls to be made
    - args: the arguments passed to this call to ``func``
    - result: the return value of this call to ``func``

    .. note: due to the way multiprocessing works, ``func`` and ``on_complete`` need to be module-level functions

    .. note: the if processes > 1, then the first argument to the vectorized ``func`` will be converted to a list before
        running. This should not have any side effects, but is necessary if the args are constructed with
        ``itertools.repeat``.

    :param func: The function to vectorize
    :param int processes: The number of processes to use (use ``config.get_number_of_processes()``)
    :param on_complete: An optional function to call for each completed call to ``func``.
    """
    if processes > 1:
        return __multiprocess_wrapper(func, processes, on_complete)
    else:
        return single_process_wrapper(func, on_complete)


def __multiprocess_wrapper(func: Callable[P, T], processes: int, on_complete: CallbackFunc | None) -> Callable[..., List[T]]:
    """Create a worker pool to map the function, taking care to set up STDOUT and STDERR"""

    def wrapper(*args: ...) -> List[T]:
        print("Using {processes} CPU's".format(processes=processes))
        ctx = multiprocessing.get_context("spawn")
        pool = ctx.Pool(processes)
        manager = ctx.Manager()

        # a queue for STDOUT and STDERR output of sub-processes (see cea.utilities.workerstream.QueueWorkerStream)
        queue = manager.Queue()

        # make sure the first arg is a list (not a generator) since we need the length of the sequence
        args_list = [list(a) for a in args]
        n = len(args_list[0])  # the number of iterations to map

        # set up the list of i-values for on_complete
        i_queue = manager.Queue()
        for i in range(n):
            i_queue.put(i)

        _args = [repeat(func, n),
                repeat(queue, n),
                repeat(on_complete, n),
                repeat(i_queue, n),
                repeat(n, n)] + args_list
        _args = zip(*_args)

        map_result = pool.map_async(__apply_func_with_worker_stream, _args)

        while not map_result.ready():
            stream_from_queue(queue)
        result = map_result.get()

        pool.close()
        pool.join()

        # process the rest of the queue
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

    # set up logging
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(logging.WARNING)
    from cea import suppress_3rd_party_debug_loggers
    suppress_3rd_party_debug_loggers()

    # unpack the arguments
    func, queue, on_complete, i_queue, n, args = args[0], args[1], args[2], args[3], args[4], args[5:]

    # set up printing to stderr and stdout to go through the queue
    sys.stdout = QueueWorkerStream('stdout', queue)
    sys.stderr = QueueWorkerStream('stderr', queue)

    # CALL
    result = func(*args)

    if on_complete:
        on_complete(i_queue.get(), n, args, result)

    return result


def single_process_wrapper(func: Callable[P, T], on_complete: CallbackFunc | None) -> Callable[..., List[T]]:
    """The simplest form of vectorization: Just loop"""

    def wrapper(*args: ...) -> List[T]:
        print("Using single process")

        args_list= [list(a) for a in args]
        n: int = len(args_list[0])
        map_result: List[T] = []
        for i, instance_args in enumerate(zip(*args_list)):
            result = func(*instance_args)
            if on_complete:
                on_complete(i, n, instance_args, result)
            map_result.append(result)
        return map_result

    return wrapper


def test(a, b):
    print("test {a}+{b}".format(a=a, b=b))
    return a + b


if __name__ == '__main__':
    print(vectorize(test, 4)(range(10, 20), range(20, 30)))
