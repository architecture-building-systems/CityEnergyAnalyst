"""
Run the City Energy Analyst demand tool for a given scenario folder
and weather file and output the
"""

import subprocess
import os

DEFAULT_COLUMN = 'QHf_MWhyr'


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")


def get_environment():
    """Return the system environment to use for the execution - this is based on
    the location of the python interpreter in ``get_python_exe``"""
    root_dir = os.path.dirname(get_python_exe())
    scripts_dir = os.path.join(root_dir, 'Scripts')
    os.environ['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
    return {k: v for k, v in os.environ.items()}


def read_csv(csv_file):
    """emulate csv.DictReader for very simple csv files (no quotes, sep = ',')"""
    with open(csv_file, 'r') as f:
        content = f.readlines()
    header = content[0].split(',')
    data = content[1:]
    for row in data:
        yield {c: v for c, v in zip(header, row.split(','))}


def run_demand(scenario_path, epw_path, column='QHf_MWhyr'):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.cli',
               '--scenario', scenario_path, 'demand', '--weather', epw_path]
    print(command)
    process = subprocess.Popen(command, startupinfo=startupinfo,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=get_environment())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        print(next_line.rstrip())
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)

    result = []
    total_demand_csv = os.path.join(scenario_path, 'outputs', 'data', 'demand',
                                    'Total_demand.csv')
    reader = read_csv(total_demand_csv)
    for row in reader:
        if not column in row.keys():
            column = DEFAULT_COLUMN
        result.append((row['Name'], float(row[column])))
    return result


if run:
    data = run_demand(scenario_path, epw_path, column)
else:
    data = None