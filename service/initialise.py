"""
JPER service initialise module, run at application startup.

The main initialise() function is run when the app is started every time
"""

from octopus.core import app
from werkzeug import generate_password_hash
import uuid, requests, json, logging, os, scheduler
from logging import Formatter
from logging.handlers import RotatingFileHandler

ELASTIC_SEARCH_HOST = "http://gateway:9200"
"""Elasticsearch hostname"""

ELASTIC_SEARCH_INDEX = "jper"
"""JPER index name in the elasticsearch instance"""

def initialise():
    """
    Initialise the application at startup.

    Ths function will be executed for you whenever you start the app.

    It will do the following things:

    1. create the initial admin account if it does not already exist
    2. set up the logging
    3. start the task scheduler (if RUN_SCHEDULE is True, otherwise scheduler should be started manually)

    :return:
    """
    i = app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/'
    un = 'admin'
    ia = i + '/account/' + un
    ae = requests.get(ia)
    if ae.status_code != 200:
        su = {
            "id":un, 
            "role": ["admin"],
            "email":"mark@cottagelabs.com",
            "api_key":"admin",
            "password":generate_password_hash(un)
        }
        c = requests.post(ia, data=json.dumps(su))
        print "first superuser account created for user " + un + " with password " + un 
        print "THIS FIRST SUPERUSER ACCOUNT IS INSECURE! GENERATE A NEW PASSWORD FOR IT IMMEDIATELY! OR CREATE A NEW ACCOUNT AND DELETE THIS ONE..."
                
    file_handler = RotatingFileHandler(app.config.get('LOGFILE','/home/mark/jperlog'), maxBytes=1000000000, backupCount=5)
    lvl = app.config.get('LOGLEVEL','info')
    if lvl == 'debug':
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d %(module)s %(funcName)s]'
    ))
    app.logger.addHandler(file_handler)

    # NOTE / TODO scheduler may have to be started separately once running app in production under supervisor
    if app.config.get('RUN_SCHEDULE',False):
        if not app.config.get("DEBUG",False) or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print "starting scheduler"
            app.logger.info("Scheduler - starting up on startup of app.")
            scheduler.go()
