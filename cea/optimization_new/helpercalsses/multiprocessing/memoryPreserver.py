"""
This class defines how the fitness of an individual of the optimisation algorithm is evaluated. This is a copy of
the deap.base.Fitness class.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


import inspect

import cea.optimization_new as optimization_module


class MemoryPreserver(object):

    def __init__(self, multiprocessing=False, class_list=None):

        self.multiprocessing = multiprocessing
        self.recorded_memory = {}

        if multiprocessing:
            if class_list is None:
                class_list = []
            elif inspect.isclass(class_list):
                class_list = [class_list]
            elif not isinstance(class_list, list):
                raise ValueError('Please indicate a valid list of classes to be recorded by the MemoryPreserver.')
            elif not all([inspect.isclass(cls) for cls in class_list]):
                raise ValueError('Please variables in the list to be recorded by the MemoryPreserver are classes.')

            self.record_class_variables(class_list)


    def record_class_variables(self, classes_for_storage):
        for cls in classes_for_storage:
            self.recorded_memory[cls.__name__] = {i: j for i, j in vars(cls).items()
                                                  if (not callable(j) and not isinstance(j, staticmethod)
                                                     and not isinstance(j, property) and not i[:2] == '__')}

    def recall_class_variables(self):

        if self.multiprocessing:
            memorised_classes = {}
            modules = inspect.getmembers(optimization_module, inspect.ismodule)
            while len(self.recorded_memory) > len(memorised_classes) and modules:
                memorised_classes.update({cls[0]: cls[1] for module in modules
                                          for cls in inspect.getmembers(module[1], inspect.isclass)
                                          if cls[0] in self.recorded_memory.keys()})
                namespace_modules = [module for module in modules
                                     if (hasattr(module[1], '__path__') and
                                         getattr(module[1], '__file__', None) is None)]
                modules = [module for namespace_module in namespace_modules
                           for module in inspect.getmembers(namespace_module[1], inspect.ismodule)]

            for cls_name in self.recorded_memory.keys():
                for cls_var_name, cls_var_value in self.recorded_memory[cls_name].items():
                    setattr(memorised_classes[cls_name], cls_var_name, cls_var_value)
