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

- Miniconda2 (Python 2.7, 64-bit, download here: https://conda.io/miniconda.html)

  - this setup expects you installed Miniconda with the "Just for me" option. You might need to change some paths along
    the way if you install for all users.
  - to the default folder (`%USERPROFILE%\Miniconda2`),
  - you don't need to add it to the PATH environment variable
  - I registered it as the default Python 2.7 (but I don't think that is necessary)

- git (I think any version will do, make sure `git.exe` is in your `PATH` by opening a command prompt and typing
  `git --version`)
- NodeJS (https://nodejs.org/en/download/current/)

Installation of Jenkins
-----------------------

- Download & install jenkins from https://jenkins.io
  -  LTS version Jenkins 2.60.3 for Windows
  -  just double click the installer, next, next, next (all default values)
  -  set jenkins service to use local user

     - Open up the Services Manager (search for "Services" in the Windows menu)
     - locate and open the "Jenkins" service
     - make sure the Startup type is set to "Automatic" so the Jenkins starts up again after reboots
     - on the tab "Log On", select "This account" instead of "Local System account" and enter in your credentials

       - this will allow the Jenkins to have access to your user profile. You can create an account just for this
         service and use that for the rest of this guide.

- open browser to http://localhost:8080

  - follow instructions to enter initial admin password

   - click "install suggested plugins"
   - create first admin user

     - Username: *cea*
     - Password: (same as *cityea* user in outlook)
     - Full name: *City Energy Analyst*
     - E-mail address: *cea@arch.ethz.ch*

   - Click "Manage Jenkins"

     - click "Configure System" (following this guide here: https://wiki.jenkins.io/display/JENKINS/Github+Plugin#GitHubPlugin-GitHubhooktriggerforGITScmpolling)
     -  set "#  of executors" to 1 (let's just make it dead simple, no concurrency, less headache)

Installation of a tunnel to the Jenkins server
----------------------------------------------

This guide assumes you're running the Jenkins on a PC inside a corporate network. We use the `localtunel.me`_ service
to tunnel webhooks triggered by GitHub back to the Jenkins server.

.. _localtunel.me: https://localtunnel.github.io/www/

- run ``npm install -g localtunnel`` on the command line

    - (``npm`` is the NodeJS package manager and was installed in the prerequisites section)

- test it with this: ``lt --port 8080 --subdomain ceajenkins``

  - you should now be able to access your Jenkins installation by going to https://ceajenkins.localtunnel.me
    from any computer with access to the internet
  - press CTRL+C to shutdown the tunnel

- create a folder in ``%APPDATA%`` called ``bin``
- copy the ``CityEnergyAnalyst\bin\ceajenkins.py`` file to ``%APPDATA%\bin``
- open the Anaconda Prompt and do ``conda create --name ceajenkins python=2.7 pywin32``, then do ``activate ceajenkins``
- open a new Anaconda Prompt with administrator rights (right click, then "Run as Administrator")
- run ``python %APPDATA%\bin\ceajenkins.py install``
- in order for the service to find required DLL's, ensure the PATH includes the following folders (use the windows

  search function to find the control panel item "Edit System Environment Variables"):
  - ``%USERPROFILE%\Miniconda2\envs\ceajenkins\``
  - ``%USERPROFILE%\Miniconda2\envs\ceajenkins\lib\site-packages\win32``

- open the windows services panel (just search for "Services" in the windows menu)

  - locate "CEA Jenkins keepalive", right click, "Properties"
  - set Startup type to "Automatic"
  - set the account in the "Log On" tab to your user account (the one that you used to install all of the above stuff)
  - start the service!
  - you should now be able to access your Jenkins installation by going to https://ceajenkins.localtunnel.me
    from any computer with access to the internet (test this)


Global configuration of Jenkins
-------------------------------

Now that we have a tunnel set up, we can start configuring the Jenkins server, mainly following this guide_:

.. _guide: https://wiki.jenkins.io/display/JENKINS/Github+Plugin#GitHubPlugin-GitHubhooktriggerforGITScmpolling

- open browser to http://localhost:8080 and log in
- click "Manage Jenkins" and then "Configure System"
  - set "#  of executors" to 1 (let's just make it dead simple, no concurrency, less headache)
  - scroll to "GitHub" section
  - click "Advanced"
  - dropdown "Manage additional GitHub actions", click "Convert login and password to token
  - choose "From login and password", enter GitHub user and password, click "Create token credentials"
  - Click "Add GitHub Server"

    - Name: (leave blank)
    - Credentials: (choose the GitHub credentials auto-generated for your username)
    - click "Test connection" - expect this message: "Credentials verified for user <username>"
    - check "Override Hook URL"
    - enter hook url https://ceajenkins.localtunnel.me

  - click "Save"

Next, we make sure all the required Jenkins plugins are installed

- open browser to http://localhost:8080 and log in
- click "Manage Jenkins" and then "Manage Plugins"

  - install the following plugins / make sure they're installed:

    - github-api plugin (https://wiki.jenkins-ci.org/display/JENKINS/GitHub+API+Plugin)
    - github plugin (https://wiki.jenkins-ci.org/display/JENKINS/GitHub+Plugin)
    - git plugin (https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin)
    - credentials plugin (https://wiki.jenkins-ci.org/display/JENKINS/Credentials+Plugin)
    - plain credentials plugin (https://wiki.jenkins-ci.org/display/JENKINS/Plain+Credentials+Plugin)
    - github pull request builder plugin (https://github.com/jenkinsci/ghprb-plugin)


Next, we configure the GitHub Pull Request Builder plugin, following the instructions here:
https://github.com/jenkinsci/ghprb-plugin

- open browser to http://localhost:8080 and log in
- click "Manage Jenkins" and then "Configure System"
- scroll down to the "GitHub Pull Request Builder" section

  - leave the GitHub Server API URL: ``https://api.github.com``
  - set the Jenkins URL overrride: ``https://ceajenkins.localtunnel.me``
  - leave the Shared secret: (bunch of \*'s... idk...)
  - select the credentials (This should be the GitHub auto generated token credentials you created above)
  - select Auto-manage webhooks
  - set the Admin list to the two lines ``daren-thomas`` and ``JIMENOFONSECA``

- click Save


Configuration of the Jenkins items
----------------------------------

First, we configure a Jenkins item for pull requests:

- open browser to http://localhost:8080 and log in
- click "New Item"
- Enter an item name: ``run cea test for pull requests``

  - Choose "Freestyle project"
  - Project name: "run cea test for pull requests"
  - Description: "Check out the CityEnergyAnalyst, create a conda environment for it and run ``cea test``"
  - check "Discard old builds"

    - Strategy: "Log Rotation"
    - Max # of builds to keep: 10

  - check "GitHub project"
  - Project url: "https://github.com/architecture-building-systems/CityEnergyAnalyst"
  - section "Source Code Management":

    - select "Git"
    - Repository URL: ``https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
    - Credentials: (use the ones created above)
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

- open browser to http://localhost:8080 and log in
- click "New Item"
- Enter an item name: ``run cea test on merge to master``

  - Choose "Freestyle project"
  - Project name: "run cea test on merge to master"
  - Description: "Check out the CityEnergyAnalyst, create a conda environment for it and run
    ``cea test --reference-case all``"
  - check "Discard old builds"

    - Strategy: "Log Rotation"
    - Max # of builds to keep: 10

  - check "GitHub project"
  - Project url: "https://github.com/architecture-building-systems/CityEnergyAnalyst"
  - section "Source Code Management":

    - select "Git"
    - Repository URL: ``https://github.com/architecture-building-systems/CityEnergyAnalyst.git``
    - Credentials: (use the ones created above)
    - Refspec: ``+refs/heads/master:refs/remotes/origin/master``
    - Branches to build: ``refs/heads/master``

  - section "Build Triggers":

    - check "GitHub hook trigger for GITScm polling"

  - section "Build"

    - Execute Windows batch command: ``bin\ceatestall.bat``

- open GitHub Integrations & services (https://github.com/architecture-building-systems/CityEnergyAnalyst/settings/installations)

  - dropdown "Add service"

    - select "Jenkins (GitHub plugin)"
    - enter Jenkins hook url: ``https://ceajenkins.localtunnel.me``
    - click "Add service" to save

