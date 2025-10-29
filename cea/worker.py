"""
cea-worker: a worker-process that uses the /server/jobs/ api to figure out what needs to be loaded to
complete a job. All output is wired through the /server/streams/ api.

In the future, (Dataframe-) file reading / writing will happen through a /server/data api.

This script is _not_ part of the ``scripts.yml``, because it's a _consumer_ of that file: It is installed
with it's own distutils entry-point (``cea-worker``) with it's own semantics for argument processing: A single
integer argument, the jobid, that is used to fetch all other information from the /server/jobs api, as well
as an URL for locating the /server/jobs api.
"""

import os
import sys
import time
import logging
import signal
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


def signal_handler(signum, _):
    """
    Handle termination signals (SIGTERM, SIGINT) for immediate shutdown.

    Design: Uses os._exit(0) for fastest possible termination without cleanup.

    Why no cleanup is needed:
    - Server already set job state to CANCELED before sending signal
    - Stream threads are daemon threads (killed automatically on exit)
    - SIGCHLD handler on server automatically reaps zombie process
    - No resources need explicit cleanup (temp files cleaned by server)

    Why os._exit() instead of sys.exit() or raise SystemExit:
    - os._exit(0): Immediate termination, bypasses all Python cleanup
    - No finally blocks run (no 1s delay from close_streams)
    - No exception handling overhead
    - Process exits in <10ms instead of >1s
    - SIGCHLD handler still reaps zombie immediately

    This is the recommended pattern for signal handlers requiring immediate termination.

    Args:
        signum: Signal number received
        _: Current stack frame (unused but required by signal.signal signature)
    """
    # Immediate exit without cleanup - fastest shutdown possible
    os._exit(0)


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


def put_with_retry(url: str, max_retries: int = 3, initial_delay: float = 0.5,
                   backoff_factor: float = 2.0, timeout: float = 3.0, **kwargs) -> bool:
    """
    Make a PUT request with retry logic and exponential backoff.

    Args:
        url: The URL to PUT to
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 0.5)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        timeout: Request timeout in seconds (default: 3.0)
        **kwargs: Additional arguments to pass to requests.put()

    Returns:
        True if successful, False if all retries failed
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):  # +1 to include the initial attempt
        try:
            response = requests.put(url, timeout=timeout, **kwargs)
            response.raise_for_status()  # Raise exception for bad status codes

            if attempt > 0:
                logger.debug(f"Successfully put to '{url}' after {attempt} retry attempt(s)")
            return True

        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Failed to PUT to '{url}' (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    f"Failed to PUT to '{url}' after {max_retries + 1} attempts. "
                    f"Last error: {last_exception}"
                )

    return False


def stream_poster(jobid, server, queue):
    """Post items from queue until a sentinel (the EOFError class object) is read."""
    msg = queue.get(block=True, timeout=None)  # block until first message

    while msg is not EOFError:
        msg = consume_nowait(queue, msg)
        put_with_retry(f"{server}/streams/write/{jobid}", data=msg)
        msg = queue.get(block=True, timeout=None)  # block until next message


class JobServerStream:
    """A File-like object for capturing STDOUT and STDERR form cea-worker processes on the server."""

    def __init__(self, jobid, server, stream):
        self.jobid = jobid
        self.server = server
        self.stream = stream  # keep the original STDOUT around for debugging purposes
        self.queue = queue.Queue()
        self.stream_poster = threading.Thread(target=stream_poster, args=[jobid, server, self.queue])
        # Make thread daemon so it doesn't block process exit on signal
        # This is critical for Docker/Linux where non-daemon threads prevent graceful shutdown
        self.stream_poster.daemon = True
        self.stream_poster.start()

    def close(self, timeout: float = 5.0):
        """
        Send sentinel that we're done writing and wait for thread to finish.

        Since the thread is a daemon, process exit won't be blocked even if the thread
        is still running. However, we still try to wait for it to finish cleanly.

        Args:
            timeout: Maximum time in seconds to wait for thread to finish (default: 5.0)
        """
        try:
            self.queue.put(EOFError, block=False)
        except queue.Full:
            # Queue is full, thread likely blocked - that's okay since it's daemon
            pass

        self.stream_poster.join(timeout=timeout)

        # If thread didn't finish in time, that's okay - it's daemon so won't block exit
        if self.stream_poster.is_alive():
            logger.debug(f"Stream poster thread still alive after {timeout}s, but won't block process exit (daemon thread)")

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


def close_streams(timeout: float = 5.0):
    """
    Close and flush all streams properly with timeout.

    Args:
        timeout: Maximum time in seconds to wait for each stream to close (default: 5.0)
    """
    # Check if stdout is a JobServerStream and close with timeout
    if isinstance(sys.stdout, JobServerStream):
        sys.stdout.close(timeout=timeout)
    elif hasattr(sys.stdout, 'close'):
        sys.stdout.close()

    # Check if stderr is a JobServerStream and close with timeout
    if isinstance(sys.stderr, JobServerStream):
        sys.stderr.close(timeout=timeout)
    elif hasattr(sys.stderr, 'close'):
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

            # Hide user warnings for now
            warnings.simplefilter("ignore", UserWarning)

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
    post_with_retry(f"{server}/jobs/started/{jobid}")


def post_success(jobid: str, server: str, output: Any = None):
    # Close streams before sending success (longer timeout for normal completion)
    close_streams(timeout=5.0)
    post_with_retry(f"{server}/jobs/success/{jobid}", json={"output": output})


def post_error(message: str, stacktrace: str, jobid: str, server: str):
    # Close streams before sending error (longer timeout for normal error handling)
    close_streams(timeout=5.0)
    post_with_retry(f"{server}/jobs/error/{jobid}", json={"message": message, "stacktrace": stacktrace})


def worker(jobid: str, server: str, suppress_warnings: bool = False):
    """
    Main logic of the cea-worker with signal handling for graceful shutdown.

    Registers signal handlers for SIGTERM and SIGINT to ensure proper cleanup
    when the worker process is terminated (e.g., job cancellation or server shutdown).

    Signal handling flow:
    1. Signal received -> signal_handler() raises SystemExit(0)
    2. SystemExit caught here, treated as cancellation (not error)
    3. finally block ensures streams are always closed
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print(f"Running cea-worker with jobid: {jobid}, url: {server}")
    try:
        job = fetch_job(jobid, server)

        configure_streams(jobid, server)
        post_started(jobid, server)
        output = run_job(job, suppress_warnings)
        post_success(jobid, server, output)
    except SystemExit as e:
        # SystemExit from explicit sys.exit() calls in CEA scripts (not from signal handler)
        # Signal handler uses os._exit(0) which bypasses exception handling
        message = f"Job [{jobid}]: exited with code {e.code}"
        print(f"\nERROR: {message}", file=sys.__stderr__)
        exc = traceback.format_exc()
        post_error(message, exc, jobid, server)
        # Re-raise SystemExit to actually exit the process after cleanup
        raise
    except Exception as e:
        # Actual errors during job execution
        message = str(e)
        print(f"\nERROR: {message}")
        exc = traceback.format_exc()
        post_error(message, exc, jobid, server)
    finally:
        # Ensure streams are always closed, even after signal
        # Use shorter timeout (1s) for signal-triggered cleanup to prevent hanging
        close_streams(timeout=1.0)


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
