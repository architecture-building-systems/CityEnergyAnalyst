"""
cea-worker: a worker-process that uses the /server/jobs/ api to figure out what needs to be loaded to
complete a job. All output is wired through the /server/streams/ api.

In the future, (Dataframe-) file reading / writing will happen through a /server/data api.

This script is _not_ part of the ``scripts.yml``, because it's a _consumer_ of that file: It is installed
with it's own distutils entry-point (``cea-worker``) with it's own semantics for argument processing: A single
integer argument, the jobid, that is used to fetch all other information from the /server/jobs api, as well
as an URL for locating the /server/jobs api.
"""
from __future__ import division
from __future__ import print_function

import sys
import requests
import traceback
import Queue
import threading
import cea.config
import cea.scripts
from cea import suppres_3rd_party_debug_loggers

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

suppres_3rd_party_debug_loggers()


def consume_nowait(queue, msg):
    """
    Read from queue as much as possible and concatenate the results to ``msg``, returning that.
    If an ``EOFError`` is read from the queue, put it back and return the ``msg`` so far.
    """
    if not queue.empty():
        messages = [msg]
        try:
            msg = queue.get_nowait()
            while not msg is EOFError:
                messages.append(msg)
                msg = queue.get_nowait()
            # msg is now EOFError, put it back
            queue.put(EOFError)
        except Queue.Empty:
            # we have read all there is in the queue for now
            pass
        finally:
            msg = ''.join(messages)
    return msg


def stream_poster(jobid, server, queue):
    """Post items from queue until a sentinel (the EOFError class object) is read."""
    msg = queue.get(block=True, timeout=None)  # block until first message
    while not msg is EOFError:
        msg = consume_nowait(queue, msg)
        requests.put("{server}/streams/write/{jobid}".format(**locals()), data=msg)
        msg = queue.get(block=True, timeout=None)  # block until next message


class JobServerStream(object):
    """A File-like object for capturing STDOUT and STDERR form cea-worker processes on the server."""
    def __init__(self, jobid, server, stream):
        self.jobid = jobid
        self.server = server
        self.stream = stream  # keep the original STDOUT around for debugging purposes
        self.queue = Queue.Queue()
        print("Starting stream_poster for {jobid}, {server}, {stream}".format(**locals()))
        self.stream_poster = threading.Thread(target=stream_poster, args=[jobid, server, self.queue])
        self.stream_poster.start()

    def close(self):
        """Send sentinel that we're done writing"""
        self.queue.put(EOFError)
        self.stream_poster.join()

    def write(self, str):
        self.queue.put_nowait(str)
        print("cea-worker: {str}".format(**locals()), end='', file=self.stream)

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
    parameters = read_parameters(job)
    script = read_script(job)
    script(config=config, **parameters)


def read_script(job):
    """Locate the script defined by the job dictionary in the ``cea.api`` module, take care of dashes"""
    import cea.api
    script_name = job["script"]
    py_script_name = script_name.replace("-", "_")
    script_method = getattr(cea.api, py_script_name)
    return script_method


def read_parameters(job):
    """Return the parameters of the job in a format that is valid for using as ``**kwargs``"""
    parameters = job["parameters"] or {}
    py_parameters = {k.replace("-", "_"): v for k, v in parameters.items()}
    return py_parameters


def post_success(jobid, server):
    requests.post("{server}/jobs/success/{jobid}".format(**locals()))


def post_error(exc, jobid, server):
    requests.post("{server}/jobs/error/{jobid}".format(**locals()), data=exc)


def worker(config, jobid, server):
    """This is the main logic of the cea-worker."""
    print("Running cea-worker with jobid: {jobid}, url: {server}".format(**locals()))
    job = fetch_job(jobid, server)
    print("job: {job}".format(**locals()))
    try:
        configure_streams(jobid, server)
        print("Configured streams.")
        print("Starting job.")
        run_job(config, job, server)
        print("Completed job.")
        post_success(jobid, server)
        print("Posted success.")
    except Exception:
        exc = traceback.format_exc()
        print(exc, file=sys.stderr)
        post_error(exc, jobid, server)
    finally:
        sys.stdout.close()
        sys.stderr.close()


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
