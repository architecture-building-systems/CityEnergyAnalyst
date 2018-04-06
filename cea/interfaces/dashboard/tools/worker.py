"""
Wrap up the cea.api interface for use in multiprocessing - using multiprocessing.Connection objects to pipe the
STDOUT and STDERR of the scripts.
"""
import sys
import cea.api
import multiprocessing


class WorkerStream(object):
    """File-like object for wrapping the output of the scripts into connection messages"""

    def __init__(self, name, connection):
        self.name = name  # 'stdout' or 'stderr'
        self.connection = connection

    def close(self):
        self.connection.close()

    def write(self, str):
        self.connection.send((self.name, str))

    def isatty(self):
        return False

    def flush(self):
        pass


def run_script(script_name, connection, kwargs):
    stdout = WorkerStream('stdout', connection)
    stderr = WorkerStream('stderr', connection)
    sys.stdout = stdout
    sys.stderr = stderr

    script = getattr(cea.api, script_name.replace('-', '_'))
    script(**kwargs)

def main(script_name, **kwargs):
    """This is the main interface to start a worker process.
    The returned ``multiprocessing.Process`` object has allready been ``start()``ed. The ``Connection``
    has a ``recv()`` method that returns a tuple (name, message), with name being either 'stdout' or 'stdin' and
    message being the string printed to that stream.

    :return: tuple (Process, Connection)
    """
    parent, child = multiprocessing.Pipe()
    worker = multiprocessing.Process(target=run_script, args=(script_name, child, kwargs))
    worker.start()
    child.close()
    return (worker, parent)



def test_worker():
    """Run a simple test with ``cea test`` to see if the worker works"""
    worker, connection = main('demand')
    import multiprocessing
    while worker.is_alive():
        try:
            print(connection.recv())
        except EOFError:
            break
    worker.join()


if __name__ == '__main__':
    test_worker()