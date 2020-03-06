:orphan:

How to set up the Jenkins server on a new PC
============================================

.. note:: you only need to do this when the current Jenkins server dies

.. note:: this guide assumes you are installing on a Windows 10 Professional system. Adjust accordingly for other
    systems, but keep in mind that some functionality of the CEA is dependant on Windows.

There are a few steps to take to setting up a Jenkins server:

- installation of some prerequisites
- installation of Jenkins
- installation of a tunnel to the Jenkins server
- global configuration of Jenkins
- configuration of the Jenkins items
  - cea test for new pull requests
  - cea test for merges to master


Installation of some prerequisites
----------------------------------

You will need to install these softwares:

- `CityEnergyAnalyst <https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/latest>`_
  (install with the ``Setup_CityEnergyAnalyst_<VERSION>.exe`` installer)

  - we'll be using the Python environment shipped with the CEA to test the CEA
  - we'll also be using the `git.exe` shipped with the CEA

Installation of Jenkins
-----------------------

- Download & install jenkins from https://jenkins.io

  -  LTS version Jenkins for Windows (last time this document was used, it was version 2.204.4)
  -  just double click the installer, next, next, next (all default values)
  -  set jenkins service to use local user

     - Open up the Services Manager (search for "Services" in the Windows menu)
     - locate and open the "Jenkins" service
     - make sure the Startup type is set to "Automatic" so the Jenkins starts up again after reboots
     - on the tab "Log On", select "This account" instead of "Local System account" and enter in your credentials

       - this will allow the Jenkins to have access to your user profile. You can create an account just for this
         service and use that for the rest of this guide.

- open browser to http://localhost:8080 (NOTE: the installer did this automatically last time tried)

  - follow instructions to enter initial admin password

    - click "install suggested plugins"
    - create first admin user

      - Username: *cea*
      - Password: (same as *cityea* user in outlook, ask Jimeno or Daren for the password)
      - Full name: *City Energy Analyst*
      - E-mail address: *cea@arch.ethz.ch*

    - Click "Manage Jenkins"

      - click "Configure System" (following this guide here: https://wiki.jenkins.io/display/JENKINS/Github+Plugin#GitHubPlugin-GitHubhooktriggerforGITScmpolling)
      -  set "#  of executors" to 1 (let's just make it dead simple, no concurrency, less headache)

Installation of a tunnel to the Jenkins server
----------------------------------------------

This guide assumes you're running the Jenkins on a Windows PC inside a corporate network. We use the `ngrok`_ service
to tunnel webhooks triggered by GitHub back to the Jenkins server.

.. _ngrok: https://ngrok.com

- download ngrok for Windows (https://ngrok.com/download)
- extract ``ngrok.exe`` to ``%PROGRAMDATA%\ceajenkins\ngrok.exe``

  - (you might need to create the folder ``ceajenkins`` first)

- create a file ``ngrok.yml`` in the folder ``%PROGRAMDATA%\ceajenkins`` with the following contents::

    authtoken: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    tunnels:
      ceajenkins:
        proto: http
        addr: 8080
        subdomain: ceajenkins

  - (replace the authtoken variable with the authtoken obtained from ngrok_

- test it with this command: ``%PROGRAMDATA%\ceajenkins\ngrok.exe start --config %PROGRAMDATA%\ceajenkins\ngrok.yml ceajenkins``

  - you should now be able to access your Jenkins installation by going to https://ceajenkins.ngrok.io
    from any computer with access to the internet
  - press CTRL+C to shutdown the tunnel

- copy the ``CityEnergyAnalyst\bin\ceajenkins.py`` file to ``%PROGRAMDATA%\ceajenkins``

    - if you haven't checked out the CEA, download it from the `CEA GitHub repository`_

- in order for the service to find required DLL's, ensure the PATH includes the following folders (use the windows
  search function to find the control panel item "Edit System Environment Variables"):

  - ``C:\Users\<user>\Documents\CityEnergyAnalyst\Dependencies\Python\``
  - ``C:\Users\<user>\Documents\CityEnergyAnalyst\Dependencies\Python\lib\site-packages\win32``
  - ``C:\Users\<user>\Documents\CityEnergyAnalyst\Dependencies\Python\lib\site-packages\pywin32_system32``
  - ``C:\Users\darthoma\Documents\CityEnergyAnalyst\Dependencies\cmder\vendor\git-for-windows\cmd\``
  - make sure to replace ``<user>`` with your username (this should be the path to the Python installed by CEA)
  - make sure you edit the System Variables, not the User Environment Variables
  - this sets up access to the Python shipped with CEA - if you installed to a different location, modify accordingly

- open ``cmd.exe`` with admin rights (right click, then "Run as Administrator")


- run ``python %PROGRAMDATA%\ceajenkins\ceajenkins.py install``


- open the windows services panel (just search for "Services" in the windows menu)

  - locate "CEA Jenkins keepalive", right click, "Properties"
  - set Startup type to "Automatic"
  - set the account in the "Log On" tab to your user account (the one that you used to install all of the above stuff)
  - start the service!
  - you should now be able to access your Jenkins installation by going to https://ceajenkins.ngrok.io
    from any computer with access to the internet (test this)

.. _`CEA GitHub repository`: https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/v2.31.1/bin/ceajenkins.py


Global configuration of Jenkins
-------------------------------

Now that we have a tunnel set up, we can start configuring the Jenkins server, mainly following this guide_:

.. _guide: https://wiki.jenkins.io/display/JENKINS/Github+Plugin#GitHubPlugin-GitHubhooktriggerforGITScmpolling

- open browser to http://ceajenkins.ngrok.io and log in
- click "Manage Jenkins" and then "Configure System"

  - set "#  of executors" to 1 (let's just make it dead simple, no concurrency, less headache)
  - in the "Jenkins Location" section set Jenkins URL to "https://ceajenkins.ngrok.io"

    - (Jenkins might be smart enough to figure this out and has filled it in for you already)

  - scroll to "GitHub" section
  - click "Advanced"
  - dropdown "Manage additional GitHub actions", click "Convert login and password to token"
  - choose "From login and password", enter GitHub user and password, click "Create token credentials"
  - Click "Add GitHub Server"

    - Name: (leave blank)
    - Credentials: (choose the GitHub credentials auto-generated for your username)
    - click "Test connection" - expect this message: "Credentials verified for user <username>"
    - check "Override Hook URL"
    - enter hook url https://ceajenkins.ngrok.io

  - click "Save"

Next, we make sure all the required Jenkins plugins are installed

- open browser to http://ceajenkins.ngrok.io and log in
- click "Manage Jenkins" and then "Manage Plugins"

  - install the following plugin:

    - GitHub Pull Request Builder Plugin (https://github.com/jenkinsci/ghprb-plugin)


Next, we configure the GitHub Pull Request Builder plugin, following the instructions here:
https://github.com/jenkinsci/ghprb-plugin

- open browser to http://ceajenkins.ngrok.io and log in
- click "Manage Jenkins" and then "Configure System"
- scroll down to the "GitHub Pull Request Builder" section

  - leave the GitHub Server API URL: ``https://api.github.com``
  - set the Jenkins URL overrride: ``https://ceajenkins.ngrok.io``
  - leave the Shared secret: (bunch of \*'s... idk...)
  - select the credentials (This should be the GitHub auto generated token credentials you created above)
  - select Auto-manage webhooks
  - set the Admin list to the two lines ``daren-thomas`` and ``JIMENOFONSECA``

- click Save


Configuration of the Jenkins items
----------------------------------

First, we configure a Jenkins item for pull requests:

- open browser to https://ceajenkins.ngrok.io and log in
- click "New Item"
- Enter an item name: ``run cea test for pull requests``

  - Choose "Freestyle project"
  - Project name: "run cea test for pull requests"
  - Description: "Check out the CityEnergyAnalyst, and run bin\ceatest.bat"
  - check "Discard old builds"

    - Strategy: "Log Rotation"
    - Max # of builds to keep: 10

  - check "GitHub project"
  - Project url: "https://github.com/architecture-building-systems/CityEnergyAnalyst"
  - section "Source Code Management":

    - select "Git"
    - Repository URL: ``https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
    - Credentials: (add a new username/password credential)
    - Branches to build: ``${ghprbActualCommit}``

  - section "Build Triggers":

    - check "GitHub Pull Request Builder"
    - GitHub API credentials: choose your credentials from the list
    - check "Use github hooks for build triggering"
    - click "Advanced"
    - List of organizations. Their members will be whitelisted: ``architecture-building-systems``

  - section "Build"

    - Execute Windows batch command: ``bin\ceatest.bat``

Next, we configure a Jenkins item for merging to master:

- open browser to https://ceajenkins.ngrok.io and log in
- click "New Item"
- Enter an item name: ``run cea test on merge to master``

  - Choose "Freestyle project"
  - Project name: "run cea test on merge to master"
  - Description: "Check out the CityEnergyAnalyst, and run bin\ceatestall.bat"
  - check "Discard old builds"

    - Strategy: "Log Rotation"
    - Max # of builds to keep: 10

  - check "GitHub project"
  - Project url: "https://github.com/architecture-building-systems/CityEnergyAnalyst"
  - section "Source Code Management":

    - select "Git"
    - Repository URL: ``https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
    - Credentials: (use the ones created above)
    - Branches to build: ``origin/master``

  - section "Build Triggers":

    - check "GitHub hook trigger for GITScm polling"

  - section "Build"

    - Execute Windows batch command: ``bin\ceatestall.bat``

- open GitHub Integrations & services (https://github.com/architecture-building-systems/CityEnergyAnalyst/settings/installations)

  - dropdown "Add service"

    - select "Jenkins (GitHub plugin)"
    - enter Jenkins hook url: ``https://ceajenkins.ngrok.io``
    - click "Add service" to save

