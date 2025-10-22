import importlib
import warnings

from cea.utilities import parse_string_to_list


def instantiate_plugin(plugin_fqname):
    """Return a new CeaPlugin based on it's fully qualified name - this is how the config object creates plugins"""
    try:
        plugin_path = plugin_fqname.split(".")
        plugin_module = ".".join(plugin_path[:-1])
        plugin_class = plugin_path[-1]
        module = importlib.import_module(plugin_module)
        instance = getattr(module, plugin_class)()
        return instance
    except Exception as ex:
        warnings.warn(f"Could not instantiate plugin {plugin_fqname} ({ex})")
        return None


def add_plugins(default_config, user_config):
    """
    Patch in the plugin configurations during __init__ and __setstate__

    :param configparser.ConfigParser default_config:
    :param configparser.ConfigParser user_config:
    :return: (modifies default_config and user_config in-place)
    :rtype: None
    """
    plugin_fqnames = parse_string_to_list(user_config.get("general", "plugins"))
    for plugin in [instantiate_plugin(plugin_fqname) for plugin_fqname in plugin_fqnames]:
        if plugin is None:
            # plugin could not be instantiated
            continue
        for section_name in plugin.config.sections():
            if section_name in default_config.sections():
                raise ValueError("Plugin tried to redefine config section {section_name}".format(
                    section_name=section_name))
            default_config.add_section(section_name)
            if not user_config.has_section(section_name):
                user_config.add_section(section_name)
            for option_name in plugin.config.options(section_name):
                if option_name in default_config.options(section_name):
                    raise ValueError("Plugin tried to redefine parameter {section_name}:{option_name}".format(
                        section_name=section_name, option_name=option_name))
                default_config.set(section_name, option_name, plugin.config.get(section_name, option_name))
                if "." not in option_name and not user_config.has_option(section_name, option_name):
                    user_config.set(section_name, option_name, default_config.get(section_name, option_name))
