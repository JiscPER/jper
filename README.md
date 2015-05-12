# Jisc Publications Event Router

Core notification manager for JPER - receives incoming notifications, matches to target recipients, and delivers notifications onward.

## Developers

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


## Installation

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

Install esprit and magnificent octopus (in that order)

    cd myapp/esprit
    pip install -e .
    
    cd myapp/magnificent-octopus
    pip install -e .
    
Create your local config

    cd myapp
    touch local.cfg

Then you can override any config values that you need to

To start the application, you'll also need to install it into the virtualenv just this first time

    cd myapp
    pip install -e .

Then, start your app with

    python service/web.py

If you want to specify your own root config file, you can use

    APP_CONFIG=path/to/rootcfg.py python service/web.py
    
