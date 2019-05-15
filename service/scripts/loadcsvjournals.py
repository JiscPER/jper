"""
This is a script to load complex .csv journal data of a Alliance License 
in a live system,  as it could be obtained from EZB anchor search, for example.

All records are put into a new License class. This means historical data will 
be kept.
"""
from octopus.core import add_configuration, app
from service.models import License
# from datetime import datetime
# import os, requests, json

# ELASTIC_SEARCH_HOST = "http://gateway:9200"
# """Elasticsearch hostname"""
#
# ELASTIC_SEARCH_INDEX = "jper"
# """JPER index name in the elasticsearch instance"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # parser.add_argument("-f", "--from_date", help="date to run the report from")
    # parser.add_argument("-t", "--to_date", help="date to run the report to")
    parser.add_argument("-t", "--table", help=".csv table data file")
    parser.add_argument("-l", "--licence", help="licence type of .csv table data ('alliance','national' or 'gold')")

    args = parser.parse_args()

    if args.config:
        add_configuration(app, args.config)


    if not args.table or not args.licence:
        parser.print_help()
        exit(0)

    if not args.licence in ["alliance", "national", "gold"]:
        parser.print_help()
        exit(0)

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

    with open(args.table, 'rb') as csvfile:
        license = License()
        j = 0
        for row in csvfile:
            j = j + 1
            if j == 1:
               name = row.replace('"','').strip()
               name = name[name.find(':')+2:]
               ezbid = name[name.find('[')+1:name.find(']')].upper()
            if j == 4: break

        license.set_license_data(ezbid,name,type=args.licence,csvfile=csvfile)

