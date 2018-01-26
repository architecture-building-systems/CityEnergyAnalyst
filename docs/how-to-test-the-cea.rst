:orphan:

How to test the CEA
===================

This document explains how to test the CEA during the development of the software. It is meant for developers interested
in extending the software as well as a documentation of the process used for quality ensurance.

The tests are located in the ``cea/tests`` folder and can be run with the ``cea test`` command. Additionally, each time
a pull request is created or pushed to, the Jenkins (see below) runs the tests and reports the results back to GitHub.
The same is also done for each merge of a branch back to master.

Types of tests performed
------------------------

The CEA employs two types of tests: Unit tests and an integration test. The boundaries between the two are not clearly
defined in the CEA. This has historical reasons, mainly for the integration test.

The integration tests are defined in the file ``cea/tests/test_calc_thermal_loads.py``. They test the demand calculation
engine to make sure changes to the code don't result in unexpected changes to the results. If results do change, the
program ``cea/tests/create_unittest_data.py`` can be used to update the test data to compare against. The test data
is stored in the file ``cea/tests/test_calc_thermal_loads.config``. Note, you will need to verify the new results using
another method before merging back to master.

Strictly speaking, the integration tests in ``test_calc_thermal_loads.py`` are coded as unit tests.

The rest of the python files in ``cea/tests`` that start with ``test_`` contain unit tests. See the python documentation
on the unittest_  module and also take a look at the pymotw_ page on the ``unittest`` module.

There is a separate file called ``cea/tests/dodo.py`` that deserves mentioning. It is an input file for the pydoit_
automation tool. This script runs the unit tests and also runs a list of CEA tools on the example reference case as well
as a list of reference cases in a private GitHub repository. When you run the ``cea test`` command, this is the script
that actually gets run. See below (chapter "dodo") for more information.

.. _unittest: https://docs.python.org/2/library/unittest.html
.. _pymotw: https://pymotw.com/2/unittest/
.. _pydoit: http://pydoit.org/


Running tests locally
---------------------

Before commit your work on a branch you should run the test suite locally. There are two ways to do this: Either using
the command line interface (CLI) or using the unit test functionality in PyCharm itself.

To run the tests from the command line interface, use the command ``cea test``. This will run the unit tests as well
as the integration test with the reference case that ships with the CEA. To test the other reference cases, run the
command like this: ``cea test --reference-case all`` - note, that you will need to set up authentication to the private
repository to do this. First, `Generate a personal access token on GitHub`_, then run the command
``cea test --save --user USERNAME --token PERSONAL_ACCESS_TOKEN`` replacing ``USERNAME`` and ``PERSONAL_ACCESS_TOKEN``
with your GitHub username and the generated token, respectively.

.. _Generate a personal access token on GitHub: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/

Running the unit tests from PyCharm is as simple as right-clicking the folder ``cea/tests`` in the project tool window
and choosing "Run Unittests in tests" from the context menu. Note that just running the unit tests will not also check
the other scripts.


The Jenkins
-----------

The Jenkins_ instance at http://ceajenkins.localtunnel.me/ is set up to run the test suite for every push to a pull
request and every merge to master. Access to this website can be provided by the project administrators.

Since updates to pull requests can happen frequently, only the short version of the tests is run - the equivalent of
running ``cea test`` locally. If the pull request page on GitHub states that "All checks have failed", checking out the
branch and running ``cea test`` will help with debugging the problem.

When a branch is merged into master, a full test is performed, equivalent to running ``cea test --reference-case all``.
This ensures that the master branch is kept in a defined state. This doesn't mean there are no bugs. Just that those
we have found don't creep back.

.. _Jenkins: https://jenkins.io/

Dodo
----

The Jenkins is set up to run the script ``cea/tests/dodo.py``. This script uses a library called pydoit_ - an
implementation of a build system (e.g. make_ or ant_) in python using python syntax to descript the targets and actions.
The dodo script is equivalent to a ``Makefile`` in the standard make_. We use this script to describe the integration
tests - a selection of scripts from the CEA are run on a set of reference cases to ensure that they at least run through
without producing errors. In addition, the set of unit tests is also run, actually testing the output of parts of the
functionality.

.. _make: https://www.gnu.org/software/make/
.. _ant: http://ant.apache.org/

Test Driven Development
-----------------------

New code added to the CEA should be accompanied with unit tests. There are many benefits of using unit tests as a
starting point for writing new code, a concept known as `Test Driven Development (TDD)`_. Developing in this style
can turn the workflow "inside out", starting bottom-up, testing at the level of equations and only aggregating later
on in the development life-cycle. This can help reduce bugs and think about code internals. It also is a good way to
run small "bits" of code quickly. Try it, and see how the style fits your work!

.. _Test Driven Development (TDD): https://en.wikipedia.org/wiki/Test-driven_development


