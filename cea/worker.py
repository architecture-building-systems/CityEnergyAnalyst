"""
cea-worker: a worker-process that uses the /server/jobs/ api to figure out what needs to be loaded to
complete a job. All output is wired through the /server/streams/ api.

In the future, file reading / writing will happen through a /server/data api.

This script is _not_ part of the ``scripts.yml``, because it's a _consumer_ of that file: It is installed
with it's own distutils entry-point (``cea-worker``) with it's own semantics for argument processing: A single
integer argument, the jobid, that is used to fetch all other information from the /server/jobs api, as well
as an URL for locating the /server/jobs api.
"""
from __future__ import division
from __future__ import print_function

import sys
import requests
import logging
import Queue
import threading
import cea.config
import cea.scripts

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# set logging level to WARN for fiona and shapely
shapely_log = logging.getLogger('shapely')
shapely_log.setLevel(logging.WARN)
fiona_log = logging.getLogger('Fiona')
fiona_log.setLevel(logging.WARN)
fiona_log = logging.getLogger('fiona')
fiona_log.setLevel(logging.WARN)


def stream_poster(jobid, server, queue):
    """Post items from queue until a sentinel (the EOFError class object) is read."""
    msg = queue.get(block=True, timeout=None)  # block until first message
    while not msg is EOFError:
        requests.put("{server}/streams/write/{jobid}".format(**locals()), data=msg)
        msg = queue.get(block=True, timeout=None)  # block until next message


class JobServerStream(object):
    """A File-like object for capturing STDOUT and STDERR form cea-worker processes on the server."""
    def __init__(self, jobid, server, stdout):
        self.jobid = jobid
        self.server = server
        self.stdout = stdout  # keep the original STDOUT around for debugging purposes
        self.queue = Queue.Queue()
        self.stream_poster = threading.Thread(target=stream_poster, args=[jobid, server, self.queue])
        self.stream_poster.start()

    def close(self):
        """Send sentinel that we're done writing"""
        self.queue.put(EOFError)
        self.stream_poster.join()

    def write(self, str):
        self.queue.put_nowait(str)
        print(str, end='', file=self.stdout)

    def isatty(self):
        return False

    def flush(self):
        pass


def configure_streams(jobid, server):
    """Capture STDOUT and STDERR writes and post them to the /server/"""
    sys.stdout = JobServerStream(jobid, server, sys.stdout)
    sys.stderr = JobServerStream(jobid, server, sys.stderr)


def fetch_job(jobid, server):
    response = requests.get("{server}/jobs/{jobid}".format(**locals()))
    job = response.json()
    return job


def run_job(config, job, server):
    import cea.api
    script_method = getattr(cea.api, job["script"])
    script_method(config=config, **job["parameters"])


def post_success(job, server):
    pass


def post_error(ex, job, server):
    print(ex)


def worker(config, jobid, server):
    print("Running cea-worker with jobid: {jobid}, url: {server}".format(**locals()))
    job = fetch_job(jobid, server)
    try:
        configure_streams(jobid, server)
        run_job(config, job, server)
        post_success(job, server)
    except Exception as ex:
        post_error(ex, job, server)


def main(config=None):
    if not config:
        config = cea.config.Configuration()
    default_url = config.worker.url

    args = parse_arguments(default_url)
    worker(config, args.jobid, args.url)


def parse_arguments(default_url):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("jobid", type=int, help="Job id to run - use 0 to run the next job", default=0)
    parser.add_argument("-u", "--url", type=str, help="URL of the CEA server api", default=default_url)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main(cea.config.Configuration())
