"""
Building model installation script
"""

from setuptools import setup, find_packages

setup(
    name="building_model",
    version="0.1",
    py_modules=find_packages(),
    install_requires=["numpy", "pandas", "CoolProp", "scipy", 'pvlib'])
