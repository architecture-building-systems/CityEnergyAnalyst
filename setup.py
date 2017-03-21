"""Installation script for the City Energy Analyst"""

import os


__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.2a2"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

LONG_DESCRIPTION = """TODO: add long description"""

if os.environ.get('READTHEDOCS', False) == 'True':
    # trick to make cea installable for readthedocs
    INSTALL_REQUIRES = []
else:
    # TODO: list all the requirements for installing
    INSTALL_REQUIRES = ['geopandas', 'pandas', 'shapely', 'fiona', 'descartes', 'pyproj', 'xlrd', 'requests',
                        'doit==0.29.0']


setup(name='cityenergyanalyst',
      version=__version__,
      description='City Energy Analyst',
      license='MIT',
      author='Architecture and Building Systems',
      author_email='cea@arch.ethz.ch',
      url='http://cityenergyanalyst.com',
      long_description=LONG_DESCRIPTION,
      packages=['cea', 'cea.analysis', 'cea.analysis.sensitivity', 'cea.demand', 'cea.demand.preprocessing',
                'cea.geometry', 'cea.optimization', 'cea.plots', 'cea.resources', 'cea.technologies',
                'cea.utilities', 'cea.interfaces', 'cea.interfaces.arcgis'],
      package_data={},
      install_requires=INSTALL_REQUIRES,
      include_package_data=True,
      entry_points={
          'console_scripts': ['ceabin=cea.cli:main'],
      },
      )
