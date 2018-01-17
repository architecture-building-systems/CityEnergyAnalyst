"""
Show a dashboard of plotly plots in a CEF Python window.

The anatomy of the app is based on the Neuron project (https://github.com/Andrew-Shay/Neuron) - except the GTK stuff
was stripped away.
"""

from cefpython3 import cefpython as cef
import platform
import sys
import thread
import socket

import cea.config


def main(config):
    """
    Start up the various parts of the application.
    """
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()

    app_port = find_port()
    thread.start_new_thread(start_cyclone, (app_port,))
    flask_url = "http://localhost:" + str(app_port)

    cef.CreateBrowserSync(url=flask_url, window_title="CEA Dashboard")
    cef.MessageLoop()
    cef.Shutdown()


def find_port():
    """
    Finds available port for Tornado / Flask

    :return: Available port
    :rtype: int
    """

    port_attempts = 0
    while port_attempts < 1000:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            app_port = sock.getsockname()[1]
            sock.close()
            print("PORT: " + str(app_port))
            return app_port
        except:
            port_attempts += 1

    print("FAILED AFTER 1000 PORT ATTEMPTS")
    sys.exit(1)


def start_cyclone(app_port):
    """
    Starts Tornado which runs Flask

    :param app_port: Port that Tornado will use
    :type app_port: int
    """

    import cyclone as cyclone
    cyclone.start_cyclone(app_port)

if __name__ == '__main__':
    main(cea.config.Configuration())