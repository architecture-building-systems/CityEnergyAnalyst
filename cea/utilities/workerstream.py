"""
This file implements ``WorkerStream`` for capturing stdout and stderr.
"""
import Queue
import sys


class WorkerStream(object):
    """File-like object for wrapping the output of the scripts into connection messages"""

    def __init__(self, name, connection):
        self.name = name  # 'stdout' or 'stderr'
        self.connection = connection

    def __repr__(self):
        return "WorkerStream({name})".format(name=self.name)

    def close(self):
        self.connection.close()

    def write(self, str):
        self.connection.send((self.name, str))

    def isatty(self):
        return False

    def flush(self):
        pass


class QueueWorkerStream(object):
    """File-like object for wrapping the output of the scripts with queues - to be created in child process"""

    def __init__(self, name, queue):
        self.name = name  # 'stdout' or 'stderr'
        self.queue = queue

    def __repr__(self):
        return "QueueWorkerStream({name})".format(name=self.name)

    def close(self):
        pass

    def write(self, str):
        self.queue.put((self.name, str))

    def isatty(self):
        return False

    def flush(self):
        pass


def stream_from_queue(queue):
    """Stream the contents from the queue to STDOUT / STDERR - to be called from parent process"""
    try:
        stream, msg = queue.get(block=True, timeout=0.1)
        if stream == 'stdout':
            sys.stdout.write(msg)
        elif stream == 'stderr':
            sys.stderr.write(msg)
    except Queue.Empty:
        pass