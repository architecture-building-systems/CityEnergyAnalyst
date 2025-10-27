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
import time
import logging
from typing import Any

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

# Set up logger
logger = logging.getLogger(__name__)


def post_with_retry(url: str, max_retries: int = 3, initial_delay: float = 0.5,
                   backoff_factor: float = 2.0, timeout: float = 3.0, **kwargs) -> bool:
    """
    Make a POST request with retry logic and exponential backoff.

    Args:
        url: The URL to POST to
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 0.5)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        timeout: Request timeout in seconds (default: 3.0)
        **kwargs: Additional arguments to pass to requests.post()

    Returns:
        True if successful, False if all retries failed
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):  # +1 to include the initial attempt
        try:
            response = requests.post(url, timeout=timeout, **kwargs)
            response.raise_for_status()  # Raise exception for bad status codes

            if attempt > 0:
                logger.debug(f"Successfully posted to '{url}' after {attempt} retry attempt(s)")
            return True

        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Failed to POST to '{url}' (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    f"Failed to POST to '{url}' after {max_retries + 1} attempts. "
                    f"Last error: {last_exception}"
                )

    return False


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


def close_streams():
    """Close and flush all streams properly"""
    if hasattr(sys.stdout, 'close'):
        sys.stdout.close()
    if hasattr(sys.stderr, 'close'):
        sys.stderr.close()


def fetch_job(jobid: str, server) -> JobInfo:
    response = requests.get(f"{server}/jobs/{jobid}")
    job = response.json()
    return JobInfo(**job)


def run_job(job: JobInfo, suppress_warnings: bool = False):
    import warnings
    parameters = read_parameters(job)
    script = read_script(job)
    
    if suppress_warnings:
        with warnings.catch_warnings():
            # Suppress FutureWarning and DeprecationWarning from all modules
            # End user does not need to see these warnings
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", DeprecationWarning)

            output = script(**parameters)
    else:
        output = script(**parameters)
    return output


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


def post_success(jobid: str, server: str, output: Any = None):
    # Close streams before sending success
    close_streams()
    requests.post(f"{server}/jobs/success/{jobid}", json={"output": output})


def post_error(message: str, stacktrace: str, jobid: str, server: str):
    # Close streams before sending error
    close_streams()
    requests.post(f"{server}/jobs/error/{jobid}", json={"message": message, "stacktrace": stacktrace})


def worker(jobid: str, server: str, suppress_warnings: bool = False):
    """This is the main logic of the cea-worker."""
    print(f"Running cea-worker with jobid: {jobid}, url: {server}")
    try:
        job = fetch_job(jobid, server)

        configure_streams(jobid, server)
        post_started(jobid, server)
        output = run_job(job, suppress_warnings)
        post_success(jobid, server, output)
    except (SystemExit, Exception) as e:
        message = f"Job [{jobid}]: exited with code {e.code}" if isinstance(e, SystemExit) else str(e)
        print(f"\nERROR: {message}")
        exc = traceback.format_exc()
        post_error(message, exc, jobid, server)
    finally:
        # Ensure streams are closed
        close_streams()


def main():
    args = parse_arguments()
    worker(args.jobid, args.url, args.suppress_warnings)


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("jobid", type=str, help="Job id to run - use 0 to run the next job")
    parser.add_argument("url", type=str, help="URL of the CEA server api")
    parser.add_argument("--suppress-warnings", action="store_true", help="Suppress warnings from external libraries, keep CEA warnings")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
