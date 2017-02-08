Getting started
===============

The City Energy Analyst V1.0b is stored in a public repository in Github
under the name of
`CEAforArcGIS <https://github.com/architecture-building-systems/CEAforArcGIS>`__.
The repository is divided in the next folder structure:

The ``CEA`` folder
------------------

The folder ``cea`` stores the core of the City Energy Analyst. Access to
this folder is available to both contributors and normal users. Pulling
requests and merging activities are in principle limited to contributors
Level 3 and the board (`See team
conventions <./users_and_credentials.md>`__)

Contributors level 2 could create a pull request if their contribution
requires an explicit modification to ``cea``. For this,a branch under
the name of their contribution should be created first and then pushed
to master. the board will take a look and accept.

The ``SANDBOX`` folder
----------------------

The folder ``Sandbox`` is the playground of contributors level 2 and 3.
Each developer has been assigned a sub-folder under his name. i.e.,
``sandbox/shsieh/``. Here you can put anything you want. You can play
around with new practices or theories that might/might not be one day
part of the CEA tool. The Sandbox facilitates mutual interaction while
scripting a new plug-in/module/class for the CEA tool. Developers level
2 and 3 are free to merge their work to the sub-folder under their name
in the Master branch.

The ``CONTRIBUTIONS`` folder
----------------------------

The folder ``contributions`` stores contributions of developers level 2
and 3 after tested, documented and accepted by the board. Generally,
this is a plug-in/module/class created out of work in the Sandbox. These
contributions are presented in the form of a sub-folder structure like
``contributions/energystorage/simplewatertank/``. Developers level 2 and
3 o merge their contributions in the Master branch.
