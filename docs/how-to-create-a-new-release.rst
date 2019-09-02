:orphan:

How to create a new release?
============================

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

The current version number can be found in the module :py:mod:`cea` (actually, since :py:mod:`cea` is a package, you
need to look into the file ``__init__.py``) in the variable ``__version__``.
All code requiring knowledge of the current version number should read the version from here. In python modules this can
be achieved by:

.. source: python

    import cea
    version_number = cea.__version__


The NSIS installer (see section `Creating the installer`_) uses the helper tool
``setup/get_version.exe`` to extract the version and write it to the file ``setup/cea_version.txt`` - if importing
:py:mod:`cea` is not an option, you could explore this avenue too...


Responsibility for version numbers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The repository admin merging a pull request to master is responsible for updating the version number.


.. _PyPI: https://pypi.python.org/pypi
.. _PEP440: https://www.python.org/dev/peps/pep-0440
.. _GitHub issues milestones list: https://github.com/architecture-building-systems/CityEnergyAnalyst/milestones


Update the CREDITS.md file
--------------------------

For each minor release (2.2, 2.3, ...) the ``CREDITS.md`` file needs to be updated to include all the authors that
worked on that release.


Creating the installer
----------------------

- first, make sure you have the Nullsoft Scriptable Installation System (NSIS) installed. See :doc:`how-to-set-up-nsis`
- if the dependencies changed, you need to re-create the ``Dependencies.7z`` file and store it as a binary on the
  release.

  - Be sure to update the URL to ``Dependencies.7z`` in the file ``setup/cityenergyanalyst.nsi`` to the new release
  - To create the ``Dependencies.7z`` file, follow these steps:

    - create an empty folder called ``Dependencies``
    - locate the conda environment for the CEA (as created with ``environment.yml`` and copy it to the ``Dependencies``
      folder.
    - rename the environment folder to ``Python``
    - use the 7z_ program to compress the ``Dependencies`` folder to ``Dependencies.7z``

- create the installer by right-clicking ``setup/cityenergyanalyst.nsi`` in Windows Explorer and choosing the "Compile
  NSIS Script" option.
- upload the installer to the Release page.
- update the document :doc:`installation-on-windows` to refer to the newest installer.

.. _7z: https://www.7-zip.org/7z.html

Testing in a virtual machine
----------------------------

In order to test the release, it is a good idea to run the installation guide / installer on a clean virtual machine,
e.g. with VirtualBox_. This test should go as far as running `cea test --reference-case open` just to be sure everything
is still working. This test goes a bit further than the regular test in that it makes sure the installation instructions
still work on a new installation. This is important because it can find missing packages in the dependency lists etc.

.. _VirtualBox: https://www.virtualbox.org/

Building the documentation
--------------------------

Well documented code is an essential part of the release, allowing your code's legacy to only grow in glory and admiration.
The documentation will be rendered via the readthedocs_ site, allowing future developers, practitioners, researchers and students
to understand and build upon your work. Note: entry points created by the command ``cea install-toolbox`` should be run at least once
and you also need to install GraphViz_ to produce the graphs.

CEA uses sphinx_ to document all module code, and has a tool specific to documentation to make your life a little easier::

``cea-doc html``

Changes to the conda environment need to be reflected in the ``docs/environment.yml`` file and if your code writes any new output variables or files,
the ``schemas.yml`` should be updated accordingly.

For more information, check out the :doc:`how-to-document-cea`.

.. _readthedocs: http://city-energy-analyst.readthedocs.io/en/latest/index.html
.. _sphinx: https://www.sphinx-doc.org/en/master/usage/installation.html
.. _GraphViz: http://www.graphviz.org/Download.php

Uploading to PyPI
-----------------

- check long-description with this commandline::

    python setup.py --long-description | for /f %i in ('where rst2html.py') do python %i > %temp%\ld.html && start %temp%\ld.html

  - make sure the output is valid / no errors, as this will be the text of the CEA on PyPI
  - for ``rst2html.py`` to be installed, you will need to do a ``pip install sphinx``

- delete any old distributions from dist folder (you can just delete the whole ``dist`` folder if you like)

- do ``python setup.py sdist bdist_wheel``

  - this will recreate the ``dist`` folder with two files that look similar to these:

    - cityenergyanalyst-2.2-py2-none-any.whl
    - cityenergyanalyst-2.2.tar.gz

- use twine to upload to PyPI

::

    twine upload dist/*

  - you can get twine_ with ``pip install twine``
  - the command above assumes you have set the ``TWINE_PASSWORD`` and ``TWINE_USERNAME`` environment variables
    if not, use the ``--username`` and ``--password`` positional arguments
  - ask the repository admins for username and password

.. _twine: https://pypi.python.org/pypi/twine
