'''
ceajenkins.py - run localtunnel in a loop because it sometimes crashes...
'''
import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import socket
import sys
import traceback
import os


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "ceajenkins"
    _svc_display_name_ = "CEA Jenkins keepalive"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self._running = True
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self._running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        servicemanager.LogInfoMsg('ceajenkins before main')
        try:
            self.main()
        except:
            servicemanager.LogErrorMsg(traceback.format_exc())
            sys.exit(-1)
        servicemanager.LogInfoMsg('normal exit')

    def main(self):
        while self._running:
            servicemanager.LogInfoMsg('restarting subprocess')
            try:
                output = subprocess.check_output(
                    [os.path.expandvars(r'%APPDATA%\npm\lt.cmd'), '--port', '8080', '--subdomain', 'ceajenkins'],
                    stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                servicemanager.LogInfoMsg('restarting localtunnel')
        servicemanager.LogInfoMsg(output)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
