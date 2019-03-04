"""Installation script for CONCEPT package"""

from setuptools import setup, find_packages

setup(
    name='concept',
    version='0.1',
    py_modules=find_packages(),
    install_requires=[  # TODO: Check compatibility issues
        'pandas==0.20.3',
        'numpy',
        'CoolProp',
        'geopandas',
        'deap',
        'networkx',
        'matplotlib',  # ==2.2.3
        'pyomo',
        'simpledbf',
        'xlrd',
        'scipy',  # ==1.1.0
        'pvlib==0.5.2',
        'pyshp',
        'sqlalchemy',  # No real dependency, just to suppress warning
        'pandapower',
    ]
)
