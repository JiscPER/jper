"""
This is a script to reset the admin account in a live system.

On production this should be run once, and never again, as it removes the old  
account and builds a new one in its place.  This means no historical data will 
be kept from the before time.
"""
from standalone_octopus.core import add_configuration, app
from werkzeug.security import generate_password_hash
# from datetime import datetime
import requests, json

ELASTIC_SEARCH_HOST = "http://gateway:9200"
"""Elasticsearch hostname"""

ELASTIC_SEARCH_INDEX = "jper"
"""JPER index name in the elasticsearch instance"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")
    args = parser.parse_args()

    if args.config:
        add_configuration(app, args.config)

    i = app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/'
    un = 'admin'
    pw = 'D33pGr33n'
    ia = i + '/account/' + un
    su = {
        "id": un,
        "role": ["admin"],
        "email": "green@deepgreen.org",
        "api_key": "admin",
        "password": generate_password_hash(pw)
    }
    c = requests.post(ia, data=json.dumps(su))
    print("superuser account reset for user " + un + " with password " + pw + " status code " + str(c.status_code))
    print("THIS SUPERUSER ACCOUNT IS INSECURE! GENERATE A NEW PASSWORD FOR IT IMMEDIATELY! OR CREATE A NEW ACCOUNT AND DELETE THIS ONE...")

