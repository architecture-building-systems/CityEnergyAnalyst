"""Installation script for the City Energy Analyst"""

import os


__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install

LONG_DESCRIPTION = """TODO: add long description"""

if os.environ.get('READTHEDOCS', False) == 'True':
    # trick to make cea installable for readthedocs
    INSTALL_REQUIRES = []
else:
    # TODO: list all the requirements for installing
    INSTALL_REQUIRES = ['geopandas', 'pandas', 'shapely', 'fiona', 'descartes', 'pyproj', 'xlrd', 'requests',
                        'doit==0.29.0']


class PostInstall(install):
    """Add a link to the python.exe that ran setup.py to user's home directory in the file cea_python.pth"""
    def run(self):
        # do the stuff ``install`` normally does
        install.run(self)

        # write out path to python.exe to the file cea_python.pth
        import sys
        import os.path
        with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
            f.write(sys.executable)


setup(name='cityenergyanalyst',
      version='1.0',
      description='City Energy Analyst',
      license='MIT',
      author='Architecture and Building Systems',
      author_email='cea@arch.ethz.ch',
      url='http://cityenergyanalyst.com',
      long_description=LONG_DESCRIPTION,
      packages=['cea', 'cea.analysis', 'cea.analysis.sensitivity', 'cea.demand', 'cea.demand.preprocessing',
                'cea.geometry', 'cea.GUI', 'cea.optimization', 'cea.plots', 'cea.resources', 'cea.technologies',
                'cea.utilities'],
      package_data={},
      install_requires=INSTALL_REQUIRES,
      cmdclass={'install': PostInstall},
      )
