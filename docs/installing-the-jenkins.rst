How to set up the Jenkins server on a new PC
============================================

NOTE: you only need to do this when the current Jenkins server dies.

	* download & install jenkins from https://jenkins.io

		* LTS version Jenkins 2.60.3 for Windows
		* just double click the installer, next, next, next (all default values)
		* set jenkins service to use local user?
	* open browser to http://localhost:8080/login?from=%2F

		* follow instructions to enter initial admin password
		* click "install suggested plugins"
		* create first admin user

			* Username: cea
			* Password: (same as cityea user in outlook)
			* Full name: City Energy Analyst
			* E-mail address: cea@arch.ethz.ch
		* Click "Manage Jenkins"

			* click "Configure System" (following this guide here: https://wiki.jenkins.io/display/JENKINS/Github+Plugin#GitHubPlugin-GitHubhooktriggerforGITScmpolling)
			* set "#  of executors" to 1 (let's just make it dead simple, no concurrency, less headache)
			* scroll to "GitHub" section

				* click "Advanced"
				* dropdown "Manage additional GitHub actions", click "Convert login and password to token
				* choose "From login and password", enter GitHub user and password, click "Create token credentials"
				* Click "Add GitHub Server"

					* Name: (leave blank)
					* Credentials: (choose the GitHub credentials auto-generated for your username)
					* click "Test connection" - expect this message: "Credentials verified for user <username>"
				* check "Override Hook URL"

					* enter hook url (see ceajenkins.py script...)
			* click "Save"
			* click "Manage Plugins"

				* install the following plugins / make sure they're installed:

					* github-api plugin (https://wiki.jenkins-ci.org/display/JENKINS/GitHub+API+Plugin)
					* github plugin (https://wiki.jenkins-ci.org/display/JENKINS/GitHub+Plugin)
					* git plugin (https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin)
					* credentials plugin (https://wiki.jenkins-ci.org/display/JENKINS/Credentials+Plugin)
					* plain credentials plugin (https://wiki.jenkins-ci.org/display/JENKINS/Plain+Credentials+Plugin)
					* github pull request builder plugin (https://github.com/jenkinsci/ghprb-plugin)
				* We're following the instructions here: https://github.com/jenkinsci/ghprb-plugin

					* Go to Manage Jenkins -> Configure System -> GitHub Pull Request Builder section
					* Jenkins URL overrride: `https://ceajenkins.localtunnel.me`
					* enter admin list etc. (look this up once working!!)
		* Make sure `git.exe` is in the System PATH
		* Set up a localtunnel to route traffic to the PC (this is optional if you have a server facing the internet) - we use this to react to webhooks by GitHub

			* download and install NodeJS (https://nodejs.org/en/download/current/)
			* run `npm install -g localtunnel`

				* following this guide: https://localtunnel.github.io/www/
				* test it with this: `lt --port 8080 --subdomain ceajenkins`
			* create a folder in `%APPDATA%` called `bin`
			* copy the `CityEnergyAnalyst\bin\ceajenkins.py` file to `%APPDATA%\bin`
		* Install a conda distribution

			* using Miniconda, Python 2.7, 64-bit version
			* I installed for "Just Me (recommended)", to the default folder (`%USERPROFILE%\Miniconda2`), not adding it to the PATH environment variable, but registering as default Python 2.7
			* open Anaconda Prompt and do `conda create --name ceajenkins python=2.7 pywin32`, then `activate ceajenkins`
			* open a new Anaconda Prompt with administrator rights (right click, then "Run as Administrator")
			* run `python %APPDATA%\bin\ceajenkins.py install`
			* ensure the SYSTEM PATH includes the following folders (use the windows search function to find the control panel item "Edit System Environment Variables")

				* c:\Users\<your_user_name>\Miniconda2\envs\ceajenkins\
				* C:\Users\<your_user_name>\Miniconda2\envs\ceajenkins\lib\site-packages\win32\
				* NOTE: if you have installed the `ceajenkins` environment to a different location, adjust accordingly
				* (this is needed for the service to find required DLL's)
		* open the windows services panel (just search for "Services" in the windows menu)

			* locate "CEA Jenkins keepalive", right click, "Properties"
			* set Startup type to "Automatic"
			* set the account in the "Log On" tab to your user account (the one that you used to install all of the above stuff)
			* start the service!
		* click "New Item"

			* Enter an item name: "cea test"
			* Choose "Freestyle project"
			* Project name: "cea test"
			* Description: "Check out the CityEnergyAnalyst, create a conda environment for it and run `cea test`"
			* check "Discard old builds"

				* Strategy: "Log Rotation"
				* Max # of builds to keep: 10
			* check "GitHub project"

				* Project url: "https://github.com/architecture-building-systems/CityEnergyAnalyst"
			* Source Code Management: check "Git"

				* Repository URL: "https://github.com/architecture-building-systems/CityEnergyAnalyst.git"
				* Branches to build: "refs/heads/master"
			* Build Triggers

				* check "GitHub hook trigger for GITScm pooling


