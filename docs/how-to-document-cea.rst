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

Sphinx Module Documentation Standard Example::

    """
    Title of module without section denotation (e.g. i_like_pie.py)

    Brief description of what the module does.
    """


    def non_return_method(parameter1, parameter2):
        """
        This method does this and that. More information about why this method
        exists.
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        :param parameter1: description of parameter1
        :type parameter1: type of parameter1
        :param parameter2: description of parameter2
        :type parameter2: type of parameter2
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        """


    def single_return_method(parameter1, parameter2):
        """
        This method does this and that. More information about why this method
        exists.
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        :param parameter1: description of parameter1
        :type parameter1: type of parameter1
        :param parameter2: description of parameter2
        :type parameter2: type of parameter2
        :returns:
            - **return1**: description of returned
        :rtype: return1_type
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        """

    def multiple_return_method(parameter1, parameter2):
        """
        This method does this and that. More information about why this method
        exists.
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        :param parameter1: description of parameter1
        :type parameter1: type of parameter1
        :param parameter2: description of parameter2
        :type parameter2: type of parameter2
        :returns:
            - **return1** : description of return1
            - **return2** : description of return2
            - **return3** : description of return3
        :rtype: return1_type, return2_type, return3_type
                          <--------- THIS BLANK LINE IS IMPORTANT!!!
        """
     # these comments are ignored by Sphinx


You can check if your documentation will render as intended using the `Online Sphinx Editor <https://livesphinx.herokuapp.com/>`_.
Bear in mind, some documentation strings will still malfunction but it's a great starting point.

cea-doc tool
------------

Assuming you are a developer and have installed the relevant version of CEA, a couple of tools exist to assist you in documenting your code.
Please ensure you have activated the cea virtual environment by calling ``activate cea``, have installed Sphinx and created the relevant python
entry points by calling ``pip install -e .``

You can run the documentation processes by typing the following titles:

cea-doc html
^^^^^^^^^^^^

This tool performs the following:
    - Cross references the api documentation, running a `sphinx-apidoc <http://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html>`_
        for all modules in the ``CityEnergyAnalyst\cea`` repository and deleting outdated ones.
    - Runs a sphinx-build_ from the docs directory via the docs make.bat (see sphinx-tools: make html)
    - Opens the documentation relevant html files of the corresponding change files from a Gitdiff

Note, the following paths/modules are currently excluded by Sphinx::

    ../cea/databases*^
    ../cea/optimization/master/generation*^

.. _sphinx-build: http://www.sphinx-doc.org/en/master/man/sphinx-build.html

cea-doc naming-merge
^^^^^^^^^^^^^^^^^^^^

This tool merges the ``schema.yml`` with the ``plots\naming.csv``, checking for undocumented variables and
raising potentially outdated ones. The ``naming.csv`` should contain all relevant documentation for written
data which can be accessed by the dashboard.

NOTE: PLEASE AVOID USING COMMAS IN ANY DESCRIPTIONS, TYPES etc... (as sphinx's csv-table method will throw an error)

cea-doc glossary
^^^^^^^^^^^^^^^^

This tool automatically updates the glossary based on the information found within the ``schema.yml``, generating
two .rst files:

- **input_methods.rst**
    file containing all inputlocator methods associated with files which are NOT generated by CEA scripts.
- **output_methods.rst**
    file containing all inputlocator methods asscoaited with files which ARE generated by CEA scripts.

cea-doc graphviz
^^^^^^^^^^^^^^^^

This tool automatically creates the data flow digraphs for each script from the ``schema.yml``, stored in
``docs\graphviz\``. Then, it renders the ``script-data-flow.rst`` containing all the graphviz diagrams for
documentation purposes.

sphinx tools
------------

Along with the ``cea-doc`` tool, some handy sphinx commands exist within the ``docs\make.bat`` and ``docs\make-warnings.bat``.
These can be run from the ``docs`` repository by typing in the following:

make html
^^^^^^^^^
This extension of the make batch runs sphinx-build_ to generate html files in the ``CityEnergyAnalyst\docs\_build``
from each of the rst files within the ``CityEnergyAnalyst\docs`` and ``CityEnergyAnalyst\docs\modules`` repositories.
This tool will generate html files from any new rst files created since the last build, skipping pre-existing rst and corresponding html files.\

make clean
^^^^^^^^^^
This will remove all html files from the previous sphinx-build_.

make-warnings
^^^^^^^^^^^^^
This batch file runs sphinx-build_ , stopping the build when the first error is encountered.
This tool is great for de-bugging documentation builds, allowing you to check and fix errors one by one.