"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""

### NOTE / FIXME: have this class read in the scripts.yml and schemas.yml. plots need to be python classes.

class CeaPlugin(object):
    """
    A CEA Plugin defines a list of scripts and a list of plots - the CEA uses this to populate the GUI
    and other interfaces. In addition, any input- and output files need to be defined.
    """

    @property
    def scripts(self):
        """Return a list of scripts - each is a subclass of :py:class`cea.scripts.CeaScript`"""
        return []

    @property
    def plots(self):
        """Return a list of plots - each is a subclass of :py:class:`cea.plots.base`"""
        return []

    @property
    def schemas(self):
        """Return a list of schemas - each is a subclass of :py:class:`cea.schema.Schema`"""
        return []