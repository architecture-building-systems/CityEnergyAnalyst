import inspect
import os.path
import sys


def get_optimization_module_classes():
    """
    Gets all classes in the optimization module
    """

    def in_optimization_module(obj):
        try:
            return os.path.realpath(inspect.getfile(obj)).startswith(os.path.dirname(os.path.realpath(__file__)))
        except TypeError:  # Ignore builtin mods
            return False

    def find_classes(module):
        objs = inspect.getmembers(module, lambda x: inspect.ismodule(x) or inspect.isclass(x))

        all_classes = []
        for name, obj in objs:
            # Ignore external modules
            if not in_optimization_module(obj):
                continue

            # Just add to list if obj is a class
            if inspect.isclass(obj):
                all_classes.append((name, obj))
                continue

            # Try to find classes in module
            classes = inspect.getmembers(obj, lambda x: inspect.isclass(x) and in_optimization_module(x))

            # could be package if obj is in module but has no classes
            # try finding more objs within
            if not len(classes):
                classes = find_classes(obj)

            all_classes.extend(classes)

        return all_classes

    return find_classes(sys.modules[__name__])
