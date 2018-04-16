Main Developer Workflow
=======================

Welcome to the CEA development team! This guide will explain the main workflow of CEA, including basic functions 
and formatting preferences of the Zenhub plugin and Github Desktop.

Zenhub Plugin
-------------

The CEA team uses the `Zenhub Plugin <https://www.zenhub.com/extension/>`_ to facilitate communication between developers. The plugin creates a *Zenhub* 
tab in the CEA github repository and applies a scrum-style framework to application development. Groups of tasks can be
lumped together into themed initiatives (called epics) which comprise of discrete tasks (called issues). For example, 
``Bugs and Errors`` may be an epic containing a number of discrete issues such as ``Function X fails with KeyError Y``.

Adding an issue
^^^^^^^^^^^^^^^

New issues can be added via the green new issue clickbox to the right of the search filters. Issue titles should be 
described as concisely as possible. Issue comments should be as specific as possible, describing the source and potential solution
to the problem. Each issue can be assigned a status in the pipeline, label (e.g. documentation), assignee, milestone, estimate, epic
and release - feel free to use any which are appropriate. Zenhub will then create the issue and assign an identification number.


Github Desktop Workflow
-----------------------
Github desktop is a handy user interface for tracking and merging local alterations to the remote repository. When addressing an
issue raised in Zenhub, it is important to note the following processes:

Git pull and branching
^^^^^^^^^^^^^^^^^^^^^^

#. Open Github Desktop
#. Click pull origin if working on a clean branch (no uncommitted local changes).
	- **git fetch**: fetches any commits from the target branch and stores them in your local respository.
	- **git merge**: integrates fetched commits into your working branch and files.	
	- **git pull**: performs a git fetch and git merge. Pulling integrates any fetched commits into your current working branch, which can create merge conflicts.
#. If altering an existing branch:
	- Select current branch and search for the issue number assigned by Zenhub.
   If creating a new branch:
	- Press Ctrl+Shift+N (or current branch>new branch from the drop down list).
	- Name the new branch based on the following format ``issue#-issue-name-lower-case-hyphenated``
	e.g. ``107-documentation-needs-updating`` 
#. Click Repository from the drop down menu.
#. Select *Open in command prompt* or *Show in explorer* depending on preference.
#. Open and perform necessary modifications or additions to scripts or files.
#. Ensure all changes are tested for functionality.
#. Save alterations once completed.

Git commit
^^^^^^^^^^

#. Return to Github desktop.
#. Review all changes in the *Changes* tab on the left hand side.
#. In the bottom left corner, write a brief summary of your changes followed by a description of what has been changed and why.
#. Click *Commit to...* button, ensuring you are committing to the correct branch.
	- **git commit**: committing tracks and saves any changes or new files created locally.
#. Repeat processes until you are ready to merge with the master repository.

Git push and remote pull request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. When ready to update team members with your changes, ensure latest changes are committed.
#. Select *Push origin*.
	- **git push**: pushes your local commits to the remote respoitory.
#. Open the remote repository in your browser.
#. Click the *pull requests* tab.
#. Select *New Pull Request*.
#. Complete a final review of the changes.
#. Type a title and description outlining your changes and how to test them.
#. Finally, click *Create pull request*.