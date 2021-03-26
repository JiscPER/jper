"""
This is a migrate file from the old montly delivery report to the new one.

On production this should be run once, and never again, as it removes the old report and builds a new one
in its place.  This means no historical data will be kept from the before time.
"""
from octopus.core import add_configuration, app
from service import reports
from datetime import datetime
import os

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    parser.add_argument("-f", "--from_date", help="(format: yyyy-mm-ddThh:mm:ssZ) date to run the report from (the year yyyy is also taken as a part of the .csv report file name)")
    parser.add_argument("-t", "--to_date", help="(format: yyyy-mm-ddThh:mm:ssZ) date to run the report to (the total time period 'from-to' shall be strict lesser than one year!).")

    parser.add_argument("-p", "--publisher", help="report the publishers' activities (switch: PUBLISHER='x' calls this report)")

    args = parser.parse_args()

    if args.config:
        add_configuration(app, args.config)

    pycharm_debug = app.config.get('DEBUG_PYCHARM', False)
    if args.debug:
        pycharm_debug = True

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_SERVER_HOST', 'localhost'), port=app.config.get('DEBUG_SERVER_PORT', 51234), stdoutToServer=True, stderrToServer=True)
        print("STARTED IN REMOTE DEBUG MODE")

    if not args.from_date or not args.to_date:
        parser.print_help()
        exit(0)

    dt = datetime.strptime(args.from_date, "%Y-%m-%dT%H:%M:%SZ")
    year = dt.year

    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    if not args.publisher:
        reportfile = reportsdir + '/monthly_notifications_to_institutions_' + str(year) + '.csv'
        if os.path.exists(reportfile):
            os.remove(reportfile)
        reports.delivery_report(args.from_date, args.to_date, reportfile)
    else:
        reportfile = reportsdir + '/monthly_items_from_publishers_' + str(year) + '.csv'

        #if os.path.exists(reportfile):
        #    os.remove(reportfile)

        reports.publisher_report(args.from_date, args.to_date, reportfile)

    print("Done: Report written to '{f}'".format(f=reportfile))
    print()

