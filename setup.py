"""Installation script for the City Energy Analyst"""

import os
from setuptools import setup, find_packages

import cea

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = cea.__version__
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

with open('README.rst', 'r') as f:
    LONG_DESCRIPTION = f.read()

INSTALL_REQUIRES = ['SALib==1.2',  # last version to work with python2
				    'ephem',
                    'doit==0.29.0',
                    'geopandas',
                    'ipython',
                    'jupyter',
                    'mock',
                    'numba',
                    'plotly',
                    'py4design==0.27',
                    'pymc3',
                    'pysal',
                    'pyyaml',
                    'requests',
                    'seaborn',
                    'setuptools',
                    'staticmap',
                    'sphinx',
                    'timezonefinder==3.4.2',  # last version to work with python2
                    'twine',
                    'utm',
                    'xlrd',
                    'xlwt']

# For building the documentation on readthedocs, exclude some of the packages, as they create build errors...
if os.environ.get('READTHEDOCS') == 'True':
    INSTALL_REQUIRES = ['setuptools']


setup(name='cityenergyanalyst',
      version=__version__,
      description='City Energy Analyst',
      license='MIT',
      author='Architecture and Building Systems',
      author_email='cea@arch.ethz.ch',
      url='http://cityenergyanalyst.com',
      long_description=LONG_DESCRIPTION,
      py_modules=[''],
      packages=find_packages(),
      package_data={},
      install_requires=INSTALL_REQUIRES,
      include_package_data=True,
      entry_points={
          'console_scripts': ['cea=cea.interfaces.cli.cli:main', 'cea-config=cea.interfaces.cli.cea_config:main'],
      },
      )
