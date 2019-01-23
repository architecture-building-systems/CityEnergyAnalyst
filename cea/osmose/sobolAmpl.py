import os, pystache, shutil, subprocess, html, sys
import sobol_seq
import uuid
import numpy as np


class SobolAmpl:
    def __init__(self, path, occurence):
        self.__hexuuid = None
        self.__path = path
        self.__output_path = None
        self.__occurence = occurence
        self.__control = None
        self.__sobolseq = None

    def run(self):
        self.sobolseq = self.sobol(np.array([[0,1],[0,1],[0,1],[0,10000],[0,10000]]),self.__occurence)
        print(os.path.join(os.path.dirname(os.path.realpath(__file__)),"templates"))
        for seq in self.sobolseq:
            self.create_uuid()
            os.mkdir(os.path.join(self.__path, self.__hexuuid))
            self.__output_path = os.path.join(self.__path, self.__hexuuid)
            self.__create_ampl_file(seq)
            self.__exec_ampl("run.run")

    def __create_ampl_file(self, sobol_seq):
        self.__control = {}
        self.__control['id'] = self.__hexuuid
        self.__control["ng"] = sobol_seq[0]
        self.__control["ng_ccs"] = sobol_seq[1]
        self.__control["pv"] = sobol_seq[2]
        self.__control["wind"] = sobol_seq[3]
        self.__control["wood"] = sobol_seq[4]
        fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"templates")
        os.mkdir(os.path.join(self.__output_path, "output"))
        os.mkdir(os.path.join(self.__output_path, "output", "sankey"))

        for f in os.listdir(fpath):

            if "run" in f:
                modtext = self.__serialize_ampl_file("run")
                self.__write_file("run.run", html.unescape(modtext))
            elif "dat" in f:
                modtext = self.__serialize_ampl_file("dat")
                self.__write_file("dat.dat", html.unescape(modtext))
            else:
                name = f.split('.')
                final_name = name[0] + ".mod"
                modtext = self.__serialize_ampl_file(name[0])
                self.__write_file(final_name, html.unescape(modtext))

    def create_uuid(self):
        self.__hexuuid = uuid.uuid4().hex

    def sobol(self, ranges, occurence):
        sobol_sequence = sobol_seq.i4_sobol_generate(len(ranges), occurence)
        mins = ranges[:, 0]
        maxs = ranges[:, 1]
        return (sobol_sequence * (maxs - mins) + mins)

    def __exec_ampl(self, runFile):
        p = subprocess.Popen(["ampl", runFile], cwd=self.__output_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err = p.communicate()
        if err.decode('utf-8') is not '' or 'optimal' not in output.decode('utf-8'):
            if err.decode('utf-8') is '':
                print(output.decode('utf-8'))
            print(err.decode('utf-8'))
        return output


    def __serialize_ampl_file(self, file_name):
        path_temp = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
        renderer = pystache.Renderer(file_encoding='utf-8', search_dirs=path_temp, string_encoding='utf-8')
        return renderer.render(renderer.load_template(file_name), self.__control)

    def __write_file(self, filename, text):
        datfile = os.path.join(self.__output_path, filename)
        f = open(datfile, 'w+')
        f.write(text)
        f.close()

if __name__ == '__main__':
    c = SobolAmpl('/home/looping/Bureau', 3)
    c.run()
