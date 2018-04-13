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
Github desktop is a handy user interface for tracking and merging local alterations to the global master repository. When addressing an
issue raised in Zenhub, it is important to note the following steps:

#. Open Github Desktop
#. Click Pull origin (pulling ensures your version of the project is the latest edition of the master)
#. If altering an existing branch:
    - Select current branch and search for the issue number assigned by Zenhub.
   If creating a new branch:
    - Press Ctrl+Shift+N (or current branch>new branch from the drop down list).
    - Name the new branch based on the following format ``issue#-issue-name-lower-case-hyphenated``
	e.g. ``107-documentation-needs-updating`` 
#. Click Repository from the drop down menu.
#. Select *Open in command prompt* or *Show in explorer* depending on your preference.
#. Make necessary modifications to script or files.
#. Save alterations.
#. Return to Github desktop.
#. Review all changes in the *Changes* tab on the left hand side.
#. Ensure all changes are tested for functionality.
#. In the bottom left corner, write a brief summary of your changes followed by a description of what has been changed and why.
#. Click *Commit to...* button (committing updates the current branch with all added documents and alterations).
#. Repeat processes (including pull requests from the master repository) until you're are reading to merge.
#. Select *Push changes* (this submits a request to the repository administrators to review and merge changes).
