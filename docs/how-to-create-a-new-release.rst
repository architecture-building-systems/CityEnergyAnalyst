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

The repository admin merging a pull request to master is responsible for updating the

.. _PyPI: https://pypi.python.org/pypi
.. _PEP440: https://www.python.org/dev/peps/pep-0440
.. _GitHub issues milestones list: https://github.com/architecture-building-systems/CEAforArcGIS/milestones


Uploading to PyPI
=================


Creating the installer for the planner's edition
================================================

Testing in a virtual machine
============================

Building the documentation
==========================



