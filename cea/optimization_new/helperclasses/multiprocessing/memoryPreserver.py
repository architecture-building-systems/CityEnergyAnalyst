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

from cea.optimization_new import get_optimization_module_classes


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
                                                      and not isinstance(j, classmethod)
                                                      and not isinstance(j, property) and not i[:2] == '__')}

    def recall_class_variables(self):

        if self.multiprocessing:
            modules = get_optimization_module_classes()
            memorised_classes = {module[0]: module[1] for module in modules}

            for cls_name in self.recorded_memory.keys():
                for cls_var_name, cls_var_value in self.recorded_memory[cls_name].items():
                    setattr(memorised_classes[cls_name], cls_var_name, cls_var_value)

    def update(self, classes=[]):
        classes_for_storage = [cls[1] for cls in get_optimization_module_classes() if cls[0] in classes]
        self.record_class_variables(classes_for_storage)

    def clear_variables(self, variables=['_civ_memory']):
        for cls_name in self.recorded_memory.keys():
            for var_name, var_value in self.recorded_memory[cls_name].items():
                if var_name in variables:
                    self.recorded_memory[cls_name][var_name].clear()

    def consolidate(self, child_process_memory, variables=['_civ_memory']):
        for cls_name in self.recorded_memory.keys():
            for var_name, var_value in self.recorded_memory[cls_name].items():
                if var_name in variables:
                    self.recorded_memory[cls_name][var_name].consolidate(
                        child_process_memory.recorded_memory[cls_name][var_name])
