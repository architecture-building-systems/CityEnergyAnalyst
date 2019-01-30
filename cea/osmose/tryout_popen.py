import subprocess
import numpy as np


def run_lua():
    frontend_file = "TEST_frontend.lua"
    frontend_path = "C:\\OSMOSE_projects\\hcs_windows\\Projects\\" + frontend_file
    project_path = "C:\\OSMOSE_projects\\hcs_windows"
    # p = subprocess.Popen(["lua", (frontend_path)], cwd=project_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE)
    print "running Lua: ", frontend_file
    # output, err = p.communicate('through stdin to stdout\n')
    # p2 = subprocess.Popen("C:\\Users\\Shanshan\\Desktop\\ampl\\ampl_lic.exe stop", stdin=p.stdout, stdout=subprocess.PIPE)
    p2 = subprocess.Popen("C:\\Users\\Shanshan\\Desktop\\ampl\\ampl_lic.exe start")
    output, err = p2.communicate('through stdin to stdout\n')
    # timeout = {"value": False}
    # timer = Timer(timeout_sec, kill_proc, [p, timeout])
    # timer.start()
    # output, err = p.communicate()
    # timer.cancel()
    # print(output.decode('utf-8'))
    return np.nan

def main():
    for i in range(3):
        run_lua()
    return np.nan


if __name__ == '__main__':
    main()
