How to test the CEA
===================

This document explains how to test the CEA during the development of the software. It is meant for developers interested
in extending the software as well as a documentation of the process used for quality ensurance.

The tests are located in the ``cea/tests`` folder and can be run with the `cea test` command. Additionally, each time
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

Strictly speaking, the integration tests are coded as unit tests.

The rest of the python files in ``cea/tests`` that start with ``test_`` contain unit tests. See the python documentation
on the unittest_  module and also take a look at the pymotw_ page on the ``unittest`` module.

.. _unittest: https://docs.python.org/2/library/unittest.html
.. _pymotw: https://pymotw.com/2/unittest/


Running tests locally
---------------------

- CLI
- PyCharm

The Jenkins
-----------

continuous integration server. running tests remotely.
