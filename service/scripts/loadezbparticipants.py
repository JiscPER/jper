"""
This is a script to load participant data of a Alliance License in a live system,
as it is returned from a EZB service call.  A license id corresponding to the ids
found *MUST* already exist in the live system.

All records are put into a new Alliance class. This means historical data will 
be kept.
"""
from octopus.core import add_configuration, app
from service.models import License, Alliance
# from datetime import datetime
import os, requests, json, csv
import lxml.html

EZB_SEARCH_HOST = "http://rzbvm016.ur.de"
"""EZB web service hostname"""

EZB_SEARCH_PAGE = "OA_participants"
"""page name in the EZB instance"""

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

    fname = app.config.get('EZB_SEARCH_PAGE',EZB_SEARCH_PAGE) # + "-EZB_current.csv"
    ia = app.config.get('EZB_SEARCH_HOST',EZB_SEARCH_HOST) + '/' + app.config.get('EZB_SEARCH_PAGE',EZB_SEARCH_PAGE)
    ae = requests.get(ia)
    if ae.status_code == 200:
        try:
            tree = lxml.html.fromstring(ae.content)
        except:
            print "ERROR: Could not parse .html page as tree."
            print
            exit(-3)

        print "INFO: xml tree read."

        fieldnames = ["Institution", "EZB-Id", "Sigel"]
        csvfile = None
        part = {}

        for el in tree.iter():
            if el.tag == 'br' and el.tail is None: continue
            if el.tag == 'h3':
                #
            item = el.tail
            if item and item.startswith(': '):
                item = item[1:].replace(u"\u0096",'-')
            if el.text == 'Institution':
                #
                part[el.text] = item.strip().encode('utf-8')
            elif el.text == 'EZB-Id':
                part[el.text] = item.strip().encode('utf-8')
            elif el.text == 'Sigel':
                part[el.text] = item.strip().encode('utf-8')
            elif el.text is None and item:
                part['Institution'] = part.get('Institution',"") + " \r" + item.strip().encode('utf-8')
