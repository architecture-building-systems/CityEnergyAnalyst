"""
cea-worker: a worker-process that uses the /server/jobs/ api to figure out what needs to be loaded to
complete a job. All output is wired through the /server/streams/ api.

In the future, (Dataframe-) file reading / writing will happen through a /server/data api.

This script is _not_ part of the ``scripts.yml``, because it's a _consumer_ of that file: It is installed
with it's own distutils entry-point (``cea-worker``) with it's own semantics for argument processing: A single
integer argument, the jobid, that is used to fetch all other information from the /server/jobs api, as well
as an URL for locating the /server/jobs api.
"""

import sys
import requests
import traceback
import queue
import threading

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.interfaces.dashboard.server.jobs import JobInfo


def consume_nowait(q, msg):
    """
    Read from queue as much as possible and concatenate the results to ``msg``, returning that.
    If an ``EOFError`` is read from the queue, put it back and return the ``msg`` so far.
    """
    if not q.empty():
        messages = [msg]
        try:
            msg = q.get_nowait()
            while msg is not EOFError:
                messages.append(msg)
                msg = q.get_nowait()
            # msg is now EOFError, put it back
            q.put(EOFError)
        except queue.Empty:
            # we have read all there is in the queue for now
            pass
        finally:
            msg = ''.join(messages)
    return msg


def stream_poster(jobid, server, queue):
    """Post items from queue until a sentinel (the EOFError class object) is read."""
    msg = queue.get(block=True, timeout=None)  # block until first message

    while msg is not EOFError:
        msg = consume_nowait(queue, msg)
        requests.put(f"{server}/streams/write/{jobid}", data=msg)
        msg = queue.get(block=True, timeout=None)  # block until next message


class JobServerStream:
    """A File-like object for capturing STDOUT and STDERR form cea-worker processes on the server."""

    def __init__(self, jobid, server, stream):
        self.jobid = jobid
        self.server = server
        self.stream = stream  # keep the original STDOUT around for debugging purposes
        self.queue = queue.Queue()
        self.stream_poster = threading.Thread(target=stream_poster, args=[jobid, server, self.queue])
        self.stream_poster.start()

    def close(self):
        """Send sentinel that we're done writing"""
        self.queue.put(EOFError)
        self.stream_poster.join()

    def write(self, value):
        self.queue.put_nowait(value)
        try:
            print(f"cea-worker: {value}", end='', file=self.stream)
        except Exception as e:
            print(f"cea-worker: error writing to stream: {e}")

    def isatty(self):
        return False

    def flush(self):
        pass


def configure_streams(jobid, server):
    """Capture STDOUT and STDERR writes and post them to the /server/"""
    sys.stdout = JobServerStream(jobid, server, sys.stdout)
    sys.stderr = JobServerStream(jobid, server, sys.stderr)


def fetch_job(jobid: str, server) -> JobInfo:
    response = requests.get(f"{server}/jobs/{jobid}")
    job = response.json()
    return JobInfo(**job)


def run_job(job: JobInfo):
    parameters = read_parameters(job)
    script = read_script(job)
    script(**parameters)


def read_script(job: JobInfo):
    """Locate the script defined by the job dictionary in the ``cea.api`` module, take care of dashes"""
    import cea.api
    script_name = job.script
    py_script_name = script_name.replace("-", "_")
    script_method = getattr(cea.api, py_script_name)
    return script_method


def read_parameters(job: JobInfo):
    """Return the parameters of the job in a format that is valid for using as ``**kwargs``"""
    parameters = job.parameters or {}
    py_parameters = {k.replace("-", "_"): v for k, v in parameters.items()}
    return py_parameters


def post_started(jobid, server):
    requests.post(f"{server}/jobs/started/{jobid}")


def post_success(jobid, server):
    requests.post(f"{server}/jobs/success/{jobid}")


def post_error(exc, jobid, server):
    requests.post(f"{server}/jobs/error/{jobid}", data=exc)


def worker(jobid, server):
    """This is the main logic of the cea-worker."""
    print(f"Running cea-worker with jobid: {jobid}, url: {server}")
    try:
        job = fetch_job(jobid, server)

        configure_streams(jobid, server)
        post_started(jobid, server)
        run_job(job)
        post_success(jobid, server)
    except SystemExit as e:
        post_error(str(e), jobid, server)
        print(f"Job [{jobid}]: exited with code {e.code}")
    except Exception as e:
        exc = traceback.format_exc()
        print(exc, file=sys.stderr)
        post_error(str(e), jobid, server)
    finally:
        sys.stdout.close()
        sys.stderr.close()


def main():
    args = parse_arguments()
    worker(args.jobid, args.url)


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("jobid", type=str, help="Job id to run - use 0 to run the next job")
    parser.add_argument("url", type=str, help="URL of the CEA server api")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
