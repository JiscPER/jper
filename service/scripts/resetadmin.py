"""
This is a script to reset the admin account in a live system.

On production this should be run once, and never again, as it removes the old  
account and builds a new one in its place.  This means no historical data will 
be kept from the before time.
"""
from octopus.core import add_configuration, app
from werkzeug import generate_password_hash
# from datetime import datetime
import os, requests, json

ELASTIC_SEARCH_HOST = "http://gateway:9200"
"""Elasticsearch hostname"""

ELASTIC_SEARCH_INDEX = "jper"
"""JPER index name in the elasticsearch instance"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # parser.add_argument("-f", "--from_date", help="date to run the report from")
    # parser.add_argument("-t", "--to_date", help="date to run the report to")

    args = parser.parse_args()

    if args.config:
        add_configuration(app, args.config)


    # if not args.from_date or not args.to_date:
    #     parser.print_help()
    #     exit(0)

    # dt = datetime.strptime(args.from_date, "%Y-%m-%dT%H:%M:%SZ")
    # year = dt.year
    #
    # reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    # reportfile = reportsdir + '/monthly_notifications_to_institutions_' + str(year) + '.csv'
    # if os.path.exists(reportfile):
    #     os.remove(reportfile)
    #
    # reports.delivery_report(args.from_date, args.to_date, reportfile)

    i = app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/'
    un = 'admin'
    pw = 'D33pGr33n'
    ia = i + '/account/' + un
    ae = requests.get(ia)
    if ae.status_code == 200:
        su = { 
            "id":un, 
            "role": ["admin"], 
            "email":"green@deepgreen.org",
            "api_key":"admin",
            "password":generate_password_hash(pw) 
        }
        c = requests.post(ia, data=json.dumps(su))
        print "superuser account reseted for user " + un + " with password " + pw
        print "THIS SUPERUSER ACCOUNT IS INSECURE! GENERATE A NEW PASSWORD FOR IT IMMEDIATELY! OR CREATE A NEW ACCOUNT AND DELETE THIS ONE..."

