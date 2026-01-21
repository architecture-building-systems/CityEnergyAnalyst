============================
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

All code requiring knowledge of the current version number should read the version from here.

In python modules this can be achieved by::

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


Create a Release Branch
-----------------------
- Create a branch ``Release-x.x.x`` from master.


Update the CREDITS.md file
--------------------------

For each minor release (2.2, 2.3, ...) the ``CREDITS.md`` file needs to be updated to include all the authors that
worked on that release. Update the "How to Cite" section with the Zenodo link to the correct version and doi.


Update CHANGELOG
----------------

- Run ``python cea/dev/create_changelog.py`` from the repository root.
- Update ``CHANGELOG.md`` with the latest changes from the outputs.


Updating the CEA GUI interface
------------------------------

You'll need yarn_ and `Node.js <https://nodejs.org/en/>`_ installed.

.. _yarn: https://classic.yarnpkg.com/en/docs/install/#windows-stable

For the installer to be able to pick up the newest version of the CEA GUI interface, make sure you

- Pull the newest version of the ``CityEnergyAnalyst-GUI`` repository
- Open CEA Console, navigate to the GitHub repo of the ``CityEnergyAnalyst-GUI`` repository
- Type ``yarn``, wait for the command to complete (this will update packages if necessary)

Creating the installer
----------------------

- First, make sure you have the Nullsoft Scriptable Installation System (NSIS) installed. See :docs:`how-to-set-up-nsis`
- Next, make sure the command `cea-dev build` is configured properly. The configuration should look something like this::

    (CEA) λ cea-config build
    City Energy Analyst version 3.11.0
    Configuring `cea build` with the following parameters:
    - development:nsis = C:\Program Files (x86)\NSIS\Bin\makensis.exe
      (default: )
    - development:conda = C:\Users\darthoma\miniconda3\condabin\conda.bat
      (default: )
    - development:gui = c:\Users\darthoma\Documents\GitHub\CityEnergyAnalyst-GUI
      (default: )
    - development:yarn = C:\Users\darthoma\AppData\Roaming\npm\yarn.cmd
      (default: )

You can either edit the ``cea.config`` file directly or use ``cea-config build --nsis C:\...\makensis.exe --conda ...``.

Note: The paths will be different on your system. Use the ``conda.bat`` in ``condabin`` of your Anaconda/Miniconda
installation. The path to ``gui`` should be set to the repository folder of the CityEnergyAnalyst-GUI repository.

- Install ``conda-pack`` by typing ``conda install conda-pack``.
- Creating the installer is then as easy as ``cea-dev build``. This will run quite some time as it will create
  a new conda environment for the version, conda-pack it, and do a lot of compressing.
- Locate the installer in the CityEnergyAnalyst repository under ``setup/Output``.

Create a Release Draft on GitHub
--------------------------------

- Tag the release with the correct version number.

Testing in a virtual machine
----------------------------

In order to test the release, it is a good idea to run the installation guide / installer on a clean virtual machine,
e.g. with VirtualBox_.

This test should go as far as running ``cea test --workflow slow`` just to be sure everything
is still working. This test goes a bit further than the regular test in that it makes sure the installation instructions
still work on a new installation. This is important because it can find missing packages in the dependency lists etc.

It's a good idea to use a different username on the VM as the one you used to create the installer - some ``pip`` bugs
can be found that way.

.. _VirtualBox: https://www.virtualbox.org/

Merge the Release Branch
-------------------------
- Update the "How to Cite" section inside CREDITS.md with the Zenodo link to the correct version and doi.
- Merge the branch ``Release-x.x.x`` into master.

Publish the Release on GitHub
-----------------------------
- The release should be published so that it could be found on the CityEnergyAnalyst_ repository on GitHub. Add the
installer you created in the previous step.
- It is recommended to also publish a release on the CityEnergyAnalyst-GUI_ repository that corresponds to the version
on the CityEnergyAnalyst_ repository.

.. _CityEnergyAnalyst: https://github.com/architecture-building-systems/CityEnergyAnalyst
.. _CityEnergyAnalyst-GUI: https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI/releases


Building the documentation
--------------------------

Well documented code is an essential part of the release, allowing your code's legacy to only grow in glory and admiration.

The documentation will be rendered via the readthedocs_ site, allowing future developers, practitioners, researchers and students
to understand and build upon your work. CEA uses sphinx_ to document all module code, and GraphViz to render flow charts
(please install Graphviz_ to view graphs).

First, launch the CEA Console created by the installer and call (please address any errors (red text) which appears during the sphinx build)::

 cea-doc html

This tool will:

- Remove any outdated module rst files
- Rebuild all module rst files
- Render all rst files to html
- Open any documentation html's for files identified by a Gitdiff.

Finally, any changes to the conda environment need to be reflected in the ``CityEnergyAnalyst/environment.yml`` file and if your code writes any new output variables or files,
the ``CityEnergyAnalyst/cea/schemas.yml`` should be updated accordingly.

For more information, check out the :doc:`/tutorials/how-to-document-cea`.

.. _readthedocs: http://city-energy-analyst.readthedocs.io/en/latest/index.html
.. _sphinx: https://www.sphinx-doc.org/en/master/usage/installation.html
.. _GraphViz: http://www.graphviz.org/Download.php


Updating Link in www.cityenergyanalyst.com/try-cea
--------------------------------------------------

- Go to http://www.cityenergyanalyst.com
- Press Esc and try logging into squarespace
- Go to Pages/Try CEA  (it is the last page in the list)
- Go to edit 'Page content'
- Go to edit 'Form'
- Change 'Form Name' to the name of the new version of CEA you just released
- Go to the tab 'Advanced'
- Change 'POST-SUBMIT REDIRECT' to the link where the .exe of CEA can be downloaded from
- Change 'POST-SUBMIT MESSAGE'/here, to the link where the .exe of CEA can be downloaded from
- Click 'Apply'
- Click 'Save'

.. _here: https://city-energy-analyst.readthedocs.io/en/latest/communication.html#cea-website


Uploading to PyPI
-----------------

.. note:: This step is not necessary anymore for installation.

- Check long-description with this commandline::

    python setup.py --long-description | for /f %i in ('where rst2html.py') do python %i > %temp%\ld.html && start %temp%\ld.html

  - make sure the output is valid / no errors, as this will be the text of the CEA on PyPI

- Delete any old distributions from dist folder (you can just delete the whole ``dist`` folder if you like)

- Do ``python setup.py sdist bdist_wheel``

  - this will recreate the ``dist`` folder with two files that look similar to these:

    - cityenergyanalyst-2.2-py2-none-any.whl
    - cityenergyanalyst-2.2.tar.gz

- Use twine to upload to PyPI (``twine upload dist/*``)

  - you can get twine_ with ``pip install twine`` (it should be pre-installed in the CEA Console)
  - the command above assumes you have set the ``TWINE_PASSWORD`` and ``TWINE_USERNAME`` environment variables
    if not, use the ``--username`` and ``--password`` positional arguments
  - ask the repository admins for username and password

.. _twine: https://pypi.python.org/pypi/twine
