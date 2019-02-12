:orphan:

How to document CEA?
====================

Documentation language
----------------------

The documentation language of the City Energy Analyst is American English.

The documentation is written using a markup language called reStructuredText_ (rst) and is rendered
by `Sphinx <http://www.sphinx-doc.org/en/master/index.html>`_. The `Quick reStructuredText <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_
is a great introductory resource for writing rst documentation for CEA.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html

Module Documentation
---------------------
The most common tool for documenting methods and functions within Python code is the
`Field List <http://www.sphinx-doc.org/en/stable/usage/restructuredtext/basics.html#field-lists>`_. Only documentation strings
within the ``""" Three Quotation Marks """`` will be parsed by Sphinx when rendering the API documentation, with ``# Python comments``
ignored.

Module Documentation Standard Example::

    """
    Title of module without section denotation
    """

    def method(parameter1, parameter2):
        """
        This method does this and that

        The following file is created:
            - output_file: .pdf Plot of some variables.

        :param parameter1: a list of variables
        :type list: List[]
        :param parameter2: the filename (pdf) to save the results as.
        :type output_file: str

        :return: if anything is returned

        """

     # these comments are ignored by Sphinx


You can check if your documentation will render as intended using the `Online Sphinx Editor <https://livesphinx.herokuapp.com/>`_.
Bear in mind, some documentation strings will still malfunction but it's a great starting point.

Sphinx Tools
------------
Once you are ready to generate the API for your new or altered module, a couple of tools exist to assist you. You can run these
from anaconda prompt within the docs repository: ``CityEnergyAnalyst\docs``. Please ensure you have activated the cea virtual
environment by calling ``activate cea``.

You can run the batch files by typing the following titles:

make-warnings
^^^^^^^^^^^^^
This batch file runs sphinx-build_ , stopping the build when the
first error is encountered. This tool is great for de-bugging documentation builds, allowing you to check and fix errors one by one.

.. _sphinx-build: http://www.sphinx-doc.org/en/master/man/sphinx-build.html

make-api-doc
^^^^^^^^^^^^
This batch file will delete all the existing auto-generated module documentation, i.e. ``cea*.rst`` files, within the
``CityEnergyAnalyst\docs\modules`` repository. Then, it will run the `sphinx-apidoc <http://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html>`_
function, rebuilding the documentation for all modules in the ``CityEnergyAnalyst\cea`` repository.

Note, the following paths/modules are currently excluded due to module import errors::

    ../cea/databases*^
    ../cea/analysis/clustering*^
    ../cea/demand/metamodel*^
    ../cea/demand/calibration/bayesian_calibrator*^
    ../cea/demand/calibration/subset_calibrator*^
    ../cea/interfaces/dashboard*^
    ../cea/optimization/slave/test*^
    ../cea/resources/radiation_daysim/plot_points*^
    ../cea/technologies/cogeneration*^
    ../cea/technologies/thermal_network/network_layout*^
    ../cea/optimization/master/generation*^
    ../cea/tests/test_dbf*^
    ../cea/utilities/compile_pyd_files*^

    TO DO: Check/update cea VE to include missing modules.

make clean
^^^^^^^^^^
This extension of the make.bat removes the contents of the ``CityEnergyAnalyst\docs\build`` repository,
containing all the html files and `TOC trees <http://www.sphinx-doc.org/en/1.5.1/markup/toctree.html>`_ generated
from previous sphinx-build_. This tool should be run in conjunction with
make-api-doc when major changes to documentation occur, such as the addition of new modules.

make html
^^^^^^^^^
This extension of the make batch runs sphinx-build_ to generate html files in the ``CityEnergyAnalyst\docs\_build``
from each of the rst files within the ``CityEnergyAnalyst\docs`` and ``CityEnergyAnalyst\docs\modules`` repositories.
This tool will generate html files from any new rst files created since the last build,
skipping pre-existing rst and corresponding html files.


