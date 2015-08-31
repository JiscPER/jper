from octopus.core import app
from werkzeug import generate_password_hash
from service import scheduler
import uuid, requests, json, logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

ELASTIC_SEARCH_HOST = "http://gateway:9200"
ELASTIC_SEARCH_INDEX = "jper"

def initialise():
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
        
    if app.config.get('RUN_SCHEDULE',False):
        scheduler.go()
        
    file_handler = RotatingFileHandler(app.config.get('LOGFILE','/home/mark/jperlog'), maxBytes=1000000000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d %(module)s %(funcName)s]'
    ))
    app.logger.addHandler(file_handler)
