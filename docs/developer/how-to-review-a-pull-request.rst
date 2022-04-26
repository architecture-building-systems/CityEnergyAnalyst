How to review a pull request
============================

Code review could be time-consuming, but it is extremely important.
All pull requests (PR) to the CEA should be reviewed by at least one contributor with maintanence right.
The reviewer needs to ensure the changes in the code are align with the authors' description and does not compromise
the existing functionalities in the CEA.

1. Read the PR description and follow the test
----------------------------------------------

The author of the PR should provide the instruction on how to test the implementation of the new changes.
As the reviewer, you should be able to follow the instruction provided by the PR's author, or provide feedback if the
instruction is unclear.
Once the test provided by the author has passed, the reviewer may proceed to the next step.

2. Go through the file changes
------------------------------

It is always a good idea to go through all the changes at least once.
Please follow this guide_ to review the file changes on GitHub.

.. _guide: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/reviewing-proposed-changes-in-a-pull-request>

During this process, the reviewer should check for:

 - Conflicts with master. Make sure the branch is updated with the latest master, and all conflicts are resolved.
 - Sufficient documentation. Check if the documentation_ is sufficient for the next person to understand the code.
 - Hard-coded values. All hard-coded values should be avoid if possible.
 - Unit tests to implement. The reviewer should decide whether a unit test should be implemented, and request the PR author accordingly.
 - Changes that might affect other existing functions. In this case, the reviewer should come up with a test to ensure the existing functions are still function as intended.

.. _documentation: :doc:`how-to-document-cea`

Once all the points are checked out, the reviewer may proceed to the next step.

3. Run tests
------------
All PR is automatically sent to test by the Jenkins_, it executes ``cea test --workflow quick`` on a remote computer.
The test results is directly shown in the PR page on GitHub.

Additionally, it is always a good idea to run a complete test (``cea test --workflow slow``) on your local computer.
If Jenkins encounter any errors, you can also reproduce those errors by running ``cea test --workflow quick`` locally.
See here_ for more information on ``cea test``.

.. _here: :doc:`how-to-test-the-cea`
.. _Jenkins: https://jenkins.io/

Once ``cea test`` is passed, the reviewer may proceed to the last step!

4. Merge the Pull Request
-------------------------

Now you have made sure the PR is going to improve the CEA, thank you for your time!
You may go ahead and merge the PR.
If the new changes would affect many users, you might consider publish it on the #_critical_updates channel on Slack.

