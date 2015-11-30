# JPER: System installation

Soon to contain the installation documentation

Set up machines

gateway
app1
app2
index1
index2

gateway receives and routes, and handles secondary tasks like running the logging
apps are configured to talk to each other where necessary and to indexes via the gateway

app1 (and extra instances of it where necessary) run the core jper app

app2 (and extra instances of it where necessary) run the supporting apps - store and sword-in and sword-out
these apps could run on separate app machines if load requires it. But first the machine can just be scaled up.
Load should be low anyway.

index1 and index2 (and extra instances of them if necessary) run the elasticsearch indexes

current setup is on amazon machines running ubuntu 14.04 but could run on similar linux systems on other cloud hosting providers or other sources of linux hardware

## For Developers

This project uses "git flow" for code development management.  Branches are as follows:

* master - main stable branch
* develop - development branch

When installing this software locally (for the first time), you should

    git clone https://github.com/JiscPER/jper.git
    git flow init
    git checkout develop

During "git flow init" accept the default settings.

To create a new feature:

    git flow feature start feature_name
    
Then push the feature branch to the repository with

    git push origin feature/feature_name
    
Major features should be raised as pull requests, and merged by another developer, where possible.


### Installation

Clone the project:

    git clone https://github.com/JiscPER/jper.git

get all the submodules

    cd myapp
    git submodule init
    git submodule update

This will initialise and clone the esprit and magnificent octopus libraries

Then get the submodules for Magnificent Octopus

    cd myapp/magnificent-octopus
    git submodule init
    git submodule update

Create your virtualenv and activate it

    virtualenv /path/to/venv
    source /path/tovenv/bin/activate

Install esprit and magnificent octopus:

    pip install -r requirements.txt

Create your local config

    cd myapp
    touch local.cfg

Then you can override any config values that you need to

To start the application, you'll also need to install it into the virtualenv just this first time

    cd myapp
    pip install -e .

Then, start your app with

    python service/web.py

    
