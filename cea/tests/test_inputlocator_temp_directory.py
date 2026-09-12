"""The temporary directory is shared across processes but owned by one of them.

Workers write per-building files into it and the parent reads them back, so every copy of a
locator must name the same directory -- while only the process that created it may delete it.
Creation stays lazy: most of the many `InputLocator` instantiations in a run never need one.
"""

import multiprocessing
import os
import pickle

import cea.config
from cea.inputlocator import InputLocator


def _locator() -> InputLocator:
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    return InputLocator(config.scenario)


def _write_in_worker(args):
    """Runs in a spawned process: write a file and report the directory used."""
    locator, name = args
    path = locator.get_temporary_file(f"{name}T.csv")
    with open(path, "w") as handle:
        handle.write("value\n1\n")
    return os.path.dirname(path)


def _folder_in_worker(locator) -> str:
    return locator.get_temporary_folder()


def test_a_locator_that_is_never_used_creates_no_directory():
    """The point of the laziness: ~200 construction sites should cost nothing."""
    locator = _locator()

    assert locator._InputLocator__temp_directory is None


def test_pickling_shares_the_directory_even_if_it_was_never_used():
    """Pickling is the moment the directory has to become real -- the unpickled copy cannot
    create its own, or writer and reader would disagree."""
    locator = _locator()
    assert locator._InputLocator__temp_directory is None

    restored = pickle.loads(pickle.dumps(locator))

    assert restored.get_temporary_folder() == locator.get_temporary_folder()


def test_workers_write_where_the_parent_reads():
    """The reported failure: `write_aggregate_buildings` could not find the workers' files."""
    locator = _locator()
    names = ["B1001", "B1002", "B1003"]

    context = multiprocessing.get_context("spawn")
    pool = context.Pool(2)
    try:
        worker_folders = pool.map(_write_in_worker, [(locator, name) for name in names])
    finally:
        pool.close()
        pool.join()

    assert set(worker_folders) == {locator.get_temporary_folder()}
    for name in names:
        assert os.path.exists(locator.get_temporary_file(f"{name}T.csv"))


def test_a_worker_exiting_does_not_delete_the_parents_directory():
    """The latent half: radiation stages Daysim inside this folder while workers run.

    Needs `close()`/`join()` rather than `Pool` as a context manager -- the latter calls
    `terminate()`, which skips the atexit handlers this guards.
    """
    locator = _locator()
    marker = os.path.join(locator.get_temporary_folder(), "parent_owns_this.txt")
    with open(marker, "w") as handle:
        handle.write("still here\n")

    context = multiprocessing.get_context("spawn")
    pool = context.Pool(2)
    try:
        pool.map(_folder_in_worker, [locator, locator])
    finally:
        pool.close()
        pool.join()

    assert os.path.exists(marker), "a worker removed the directory the parent still owns"


def test_only_the_creating_process_cleans_up():
    """Unit-level counterpart to the test above, without spawning anything."""
    locator = _locator()
    folder = locator.get_temporary_folder()

    restored = pickle.loads(pickle.dumps(locator))
    # Pretend this copy lives in another process.
    restored._InputLocator__temp_directory_pid = os.getpid() + 1
    restored._cleanup_temp_directory()
    assert os.path.exists(folder)

    locator._cleanup_temp_directory()
    assert not os.path.exists(folder)
