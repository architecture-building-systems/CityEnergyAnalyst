============================
How to clean up CEA git repository
============================

This section describes the steps necessary to clean up the City Energy Analyst (CEA) git repository.

CEA Git Repository
------------------
Over the years, the CEA git repository has accumulated a lot of files in it's git history, many of which we do not use anymore.
Because of this, the size of the repository to be around 1.7GB (as of December 2021) even though the size of the main source code is only around 200MB.
This makes it really slow to clone the repository from GitHub.


Cleaning up the Repository
-------------------------
With the help of the `git-filter-repo <https://github.com/newren/git-filter-repo>`__ tool, we will remove large and/or old files, which are not relevant to the current version of CEA anymore, "permanently" from the git history.

.. note:: These steps are considered "permanent" only if the steps here are followed correctly. It is still possible for the changes to be reverted if the old git history is reintroduced (merged) into the new (clean) history by some way. In that case, we can redo these steps again to remove it.


Pre-flight Checks
~~~~~~~~~~~~~~~~~
#. Make sure that you have backed up the existing CEA repository somewhere safe.
    - This could be done by cloning the latest CEA repository to your local machine and copying folder somewhere else.

#. Inform internal developers to complete and merge any branches that they are currently working on into the main branch.
    - This is to ensure that local git branches (local machines) are not going to reintroduce any old history into the remote git repository (GitHub).
    - If for some reason that is not possible, one way to solve it is to do a rebase instead of a merge commit when merging the branch using GitHub Pull Requests. Read `here <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges>`__ if you want to know more about the difference.


Prerequisites (software)
~~~~~~~~~~~~~
- Have `git <https://git-scm.com/downloads>`__ installed and accessible through terminal.

    -  For Windows, use the Git Bash Terminal that is installed with the Git for Windows installation.

- Install `git-filter-repo <https://github.com/newren/git-filter-repo/blob/main/INSTALL.md>`__ tool.


Using the git-filter-repo tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After all the necessary checks are done, we can run the git-filter-repo tool using 2 ways, manually or using a script.

Manually
^^^^^^
#. Open a Terminal / Command Prompt.
#. Enter ``cd PATH_TO_CEA_REPO``, replacing ``PATH_TO_CEA_REPO`` with the path of your local CEA git repository.
#. Enter ``git filter-repo --invert-paths --paths-from-file ./bin/files_to_remove.txt``

Using Script *(Experimental)*
^^^^^^
#. Open a Terminal

    -  For Windows, use the Git Bash Terminal that is installed with the Git for Windows installation.

#. Enter ``PATH_TO_CEA_REPO/bin/repo_cleanup.sh``, replacing ``PATH_TO_CEA_REPO`` with the path of your local CEA git repository.

We can then proceed to update these changes to GitHub

Updating git history of CEA repo on GitHub
~~~~~~
To update the git history on GitHub, follow these `steps <https://docs.github.com/en/enterprise-cloud@latest/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository#using-git-filter-repo>`__ from step 7.


Adding additional files to clean from history
--------------------------------
If you want to remove other files from the history, other than the ones found in ``bin/files_to_remove.txt``, add the path of the  new lines to the file and re-run the tool as per above.
Read `this <https://htmlpreview.github.io/?https://github.com/newren/git-filter-repo/blob/docs/html/git-filter-repo.html>`__ document for more information on how to use the git-filter-repo tool.