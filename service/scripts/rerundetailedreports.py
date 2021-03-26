"""
This is a update file for the /detailed/ delivery reports.

It runs on the current year by default, or the year provided by the caller.

Could take its time, so be informed by now!
"""
from octopus.core import add_configuration, app
from service import reports
import os, time

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # parser.add_argument("-f", "--from_date", help="date to run the report from")
    # parser.add_argument("-t", "--to_date", help="date to run the report to")

    parser.add_argument("-y", "--year", help="generate/update reports for this year (Format: YYYY)")

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

    # if not args.from_date or not args.to_date:
    #     parser.print_help()
    #     exit(0)
    if not args.year:
        year = int(time.strftime('%Y'))
    else:
        year = int(args.year)
    
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')

    for mnth in range(1,13):
        nxmth = (mnth+1) % 13
        from_date = "%04d-%02d-01T00:00:00Z" % (year,mnth)
        fstem = "%04d-%02d.csv" % (year,mnth)
        if nxmth == 0:
            year = year + 1
            nxmth = 1
        to_date = "%04d-%02d-01T00:00:00Z" % (year,nxmth)
        #
        fname = os.path.join(reportsdir,"detailed_routed_notifications_" + fstem)
        reports.admin_routed_report(from_date, to_date, fname)
        lines = sum(1 for l in open(fname))
        print("Report written to '{f}',\nsize: {s} lines.".format(f=fname,s=lines))
        #
        fname = os.path.join(reportsdir,"detailed_failed_notifications_" + fstem)
        reports.admin_failed_report(from_date, to_date, fname)
        lines = sum(1 for l in open(fname))
        print("Report written to '{f}',\nsize: {s} lines.".format(f=fname,s=lines))
        #
        print()

    print("All done.")
    print()
