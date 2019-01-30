import subprocess


def exec_osmose(tech):
    frontend_file = tech + "_frontend.lua"
    frontend_path = "C:\\OSMOSE_projects\\hcs_windows\\Projects\\" + frontend_file
    project_path = "C:\\OSMOSE_projects\\hcs_windows"

    p = subprocess.Popen(["lua", (frontend_path)], cwd=project_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print "running Lua: ", frontend_file
    output, err = p.communicate()

    print(output.decode('utf-8'))
    return 'ok', output.decode('utf-8')


def main():
    TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD', 'HCS_IEHX']
    building_names = ['B007']

    for building in building_names:
        for tech in TECHS:
            exec_osmose(tech)



if __name__ == '__main__':
    main()