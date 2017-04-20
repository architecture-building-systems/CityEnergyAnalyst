How to create a new release
===========================

This section describes the steps necessary to create a new release of the City Energy Analyst (CEA).

Versioning
----------

Each release of the CEA needs a version number. Version numbers need to increase for PyPI_. The relevant documentation
for python version numbers is documented in PEP440_. The CEA uses the following versioning scheme in compliance with
PEP440_:

    major.minor[.revision][pre-release]

Major and minor version segments in this scheme refer to the milestone (sprint) the release was developed for. The
major version segment works on roughly a yearly time scale while the minor version segment tracks sprints inside the
major release. Each such pair (major.minor) refers to a "milestone" in the `GitHub issues milestones list`_.

If a release needs to be updated after publishing, an optional revision can be used, starting at 1 and incrementing.

During the sprint, the pre-release section is used to represent the current state of the master branch. At the beginning
of the sprint, alpha versions are used. Examples: 2.2a0, 2.2a1, 2.2a2, etc. In this phase the issues belonging to the
milestone are being added.

Once the code base settles down, beta versions can be used. Examples: 2.2b0, 2.2b1, 2.2b2, etc. In this phase, new
features should not be added anymore and instead testing / bug fixing activities should dominate.

Before releasing a milestone, the release candidates can be used. Examples: 2.2rc0, 2.2rc1, 2.2rc2, etc. In this phase
the software is just being tested with show-stopping bugs being fixed if possible.

Where to find the current version number
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current version number can be found in the source file `cea/__init__.py` in the variable `__version__`. All code
requiring knowledge of the current version number should read the version from here. In python this can be achieved by:

.. source: python

    import cea
    version_number = cea.__version__



Responsibility for version numbers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The repository admin merging a pull request to master is responsible for updating the version number.

.. _PyPI: https://pypi.python.org/pypi
.. _PEP440: https://www.python.org/dev/peps/pep-0440
.. _GitHub issues milestones list: https://github.com/architecture-building-systems/CEAforArcGIS/milestones


Uploading to PyPI
=================

- check long-description with this commandline::

    python setup.py --long-description | python %temp%\CityEnergyAnalyst\Scripts\rst2html.py > ld.html && start ld.html

  - make sure the output is valid / no errors, as this will be the text of the CEA on PyPI

- delete any old distributions from dist folder (you can just delete the whole ``dist`` folder if you like)

- do ``python setup.py sdist bdist_wheel``

  - this will recreate the ``dist`` folder with two files that look similar to these:

    - cityenergyanalyst-2.2-py2-none-any.whl
    - cityenergyanalyst-2.2.tar.gz

- **NOTE**: All this stuff could be made a lot easier if we created a pydoit-powered script (cea-admin?)

- use twine (pip install ``twine`` first, then set environment variables / use username & password)

::

    twine upload dist/*


Creating the installer for the planner's edition
================================================

- first, make sure you have the nullsoft scriptable installation system (NSIS) version 3.01 installed. You can get it
  from here: http://nsis.sourceforge.net/Download (choose the version 3.01)

- update the `*.pyd` files by running `cea/utilities/compile_pyd_files.py`

  - this requires `numba.pycc` to be installed, which can be obtained by doing `conda install numba`
  - this also requires a C compiler installed, **TODO**: figure out in a VM exactly how to set this up...

Testing in a virtual machine
============================

Building the documentation
==========================

An important part of the release process is ensuring that the documentation for readthedocs_ can be built. This can
be tested locally by executing the following commands in the repository folder::

    cd docs
    make clean
    make html

For this to run you might need to first ``pip install sphinx``. If any error messages show up, these need to be fixed
before publishing the release.

.. _readthedocs: http://city-energy-analyst.readthedocs.io/en/latest/index.html

