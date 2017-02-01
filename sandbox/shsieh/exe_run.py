import os
import subprocess
#command = "Studio.exe"
#os.system(command)

#subprocess.call('dir', shell=True)
output = subprocess.check_output('dir', shell = True)
print(output)