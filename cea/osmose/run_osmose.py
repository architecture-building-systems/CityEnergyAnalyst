# All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland,
# IPESE Laboratory, Copyright 2018
# This work can be distributed under the CC BY-NC-SA 4.0 License.
# See the LICENSE file for more details.
#
# Author: Michel Lopez <michel.lopez@epfl.ch>
import sys, os, subprocess, requests
# from pika import ConnectionParameters, PlainCredentials, BlockingConnection
# import json
# from appOwnExceptions import SolverError
# from wrapper.wrapper import Wrapper



# class Server:
#     def __init__(self, user, pwd, ip, port, vhost, inqueue, outqueue, status_service, data_path):
#         self.__user = user
#         self.__pwd = pwd
#         self.__ip = ip
#         self.__port = port
#         self.__vhost = vhost
#         self.__queue = inqueue
#         self.__outqueue = outqueue
#         self.__status_url = status_service + "/api/progression"
#         self.__results_url = status_service + "/api/results"
#         self.__data_path = data_path
#         self.__hexuuid = ''
#         self.__message = {}
#
#     def run(self):
#         w = wrapper.wrapper.Wrapper(self.__user, self.__pwd, self.__ip, self.__port, self.__vhost, self.__queue, self.callback, self.__outqueue)
#         w.run()
#
#     def callback(self, ch, method, properties, body):
        # project_name = "unknown"
        # try:
        #     print("Message received")
        #     string_body = body.decode()
        #     if string_body is not None:
        #         self.__message = json.loads(string_body)
        #
        #         self.__hexuuid = self.__message['hexuuid']
        #         project_name = self.__message['project_name']
        #         project_path = os.path.join(self.__data_path, self.__hexuuid)
        #         self.send_status("IN PROGRESS : Execution of osmose start", project_name)

                # status, msg = self.exec_osmose(project_path)
        #         self.check_status(msg, status, project_name)
        #     ch.basic_ack(delivery_tag=method.delivery_tag)  # acknowledge the message receipt
        # # except SolverError as sr:
        # #     self.send_status(sr.message, project_name)
        # #     ch.basic_ack(delivery_tag=method.delivery_tag)
        # except Exception as e:
        #     print(e)
        #     self.send_status("ERROR : Osmose Got an Error", project_name)
        #     ch.basic_ack(delivery_tag=method.delivery_tag)
    #
    # def check_status(self, msg, status, project_name):
    #     if status is 'ok':
    #         self.send_objective_result(msg)
    #         self.send_status("FINISH : Osmose solve Finish with success", project_name)
    #     elif status is 'warning':
    #         self.send_status("FINISH : Osmose solve Finish with success but detect Warnings : " + msg, project_name)
    #
    # def send_objective_result(self, msg):
    #     objective_line = msg.split('OBJECTIVE FUNCTION\n')[1].split('\n')[0]
    #     objective_name = objective_line.split(': \t')[0]
    #     objective_result = objective_line.split(': \t')[1]
    #     payload = {"uuid": self.__hexuuid, "objective": objective_name, "result": objective_result}
    #     requests.post(self.__results_url, json=payload)

    # def exec_osmose():
    #     frontend_path = os.path.join("projects", "frontend.lua")
    #     print("execute lua5.1 " + frontend_path + " in folder " + project_path)
    #     frontend_path = os.path.join("C:\\OSMOSE_projects\\hcs_windows\\Projects\\","HCS_coil_frontend.lua")
    #
    #     p = subprocess.Popen(["lua5.1", frontend_path], cwd=project_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     output, err = p.communicate()
    #     if err.decode('utf-8') is not '':
    #         print(err.decode('utf-8'))
    #         if err.decode('utf-8').startswith('WARNING:'):
    #             return 'warning', err.decode('utf-8')
    #         elif err.decode('utf-8').startswith('pandoc: Could not find image'):
    #             return 'warning', err.decode('utf-8')
    #         else:
    #             raise SolverError(self.__hexuuid, "ERROR : " + err.decode('utf-8'))
    #     print(output.decode('utf-8'))
    #     return 'ok', output.decode('utf-8')

    # def send_status(self, status, project_name):
    #     payload = {"uuid": self.__hexuuid, "app": "xOsmoseServer", "status": status, "project": project_name}
    #     requests.post(self.__status_url, json=payload)

def exec_osmose(tech):
    # frontend_path = os.path.join("projects", "frontend.lua")
    # print("execute lua5.1 " + frontend_path + " in folder " + project_path)
    # project_path = "C:\\OSMOSE_projects\\hcs_windows\\Projects\\"
    #project_path = "C:\\Program Files (x86)\\Lua\\5.1"
    #frontend_path = os.path.join(project_path,"HCS_coil_frontend.lua")

    frontend_file = tech + "_frontend.lua"
    frontend_path = "C:\\OSMOSE_projects\\hcs_windows\\Projects\\" + frontend_file
    project_path = "C:\\OSMOSE_projects\\hcs_windows"

    p = subprocess.Popen(["lua", (frontend_path)], cwd=project_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print "running Lua: ", frontend_file
    output, err = p.communicate()
    # if err.decode('utf-8') is not '':
    #     print(err.decode('utf-8'))
    #     if err.decode('utf-8').startswith('WARNING:'):
    #         return 'warning', err.decode('utf-8')
    #     elif err.decode('utf-8').startswith('pandoc: Could not find image'):
    #         return 'warning', err.decode('utf-8')
    #     else:
    #         raise ValueError(err.decode('utf-8'))
            # raise SolverError(self.__hexuuid, "ERROR : " + err.decode('utf-8'))
    print(output.decode('utf-8'))
    return 'ok', output.decode('utf-8')

def main(argv=None):
    # if len(argv) is 0:
    #     print("Server need user entries")
    # else:
    #     user, pwd, ip, port, vhost, queue, outqueue, elasticserver, dataPath = argv

    # dataPath = ''
    # c = Server(user, pwd, ip, port, vhost, queue, outqueue, elasticserver, dataPath)
    # c.run()
    exec_osmose()

if __name__ == '__main__':
    # main(sys.argv[1:])
    main()