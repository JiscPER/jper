"""
This is a script to load participant data of a Alliance License in a live system,
as it is returned from a EZB service call.  A license id corresponding to the ids
found *MUST* already exist in the live system.

All records are put into possibly already existing alliance data. 
This means historical data will probably be overwritten/updated. 
So be warned/informed now!
"""
from octopus.core import add_configuration, app
from service.models import License, Alliance
import requests, csv, os
import lxml.html

EZB_SEARCH_HOST = "http://rzbvm016.ur.de"
"""EZB web service hostname"""

EZB_SEARCH_PAGE = "OA_participants"
"""page name in the EZB instance"""


def upload_csv(newf, alid):
    try:
        with open(newf, 'r') as fd:
            license = License.pull_by_key('identifier.id', alid)
            if license and len(license) > 0:
                alliance = Alliance.pull_by_key('identifier.id', alid)
                if not alliance:
                    alliance = Alliance()
                alliance.set_alliance_data(license[0].id, alid, csvfile=fd)
                print("INFO: data for alliance '{a}' uploaded to system.".format(a=alid))
            else:
                print("WARNING: alliance '{a}' not found in system; skipping: data not uploaded.".format(a=alid))
    except Exception as e:
        print("WARNING: could not process .csv file '{x}' for database upload.".format(x=newf))
        print("WARNING: message: '{x}'".format(x=str(e)))


def close_and_upload_csv(csvfile, newf, alid):
    try:
        if csvfile and not csvfile.closed: 
            csvfile.close()
            with open( newf, 'r' ) as fd:
                license = License.pull_by_key('identifier.id', alid)
                if license and len(license)>0:
                    alliance = Alliance.pull_by_key('identifier.id', alid)
                    if not alliance:
                        alliance = Alliance()
                    alliance.set_alliance_data(license[0].id, alid, csvfile=fd)
                    print("INFO: data for alliance '{a}' uploaded to system.".format(a=alid))
                else:
                    print("WARNING: alliance '{a}' not found in system; skipping: data not uploaded.".format(a=alid))
    except Exception as e:
        print("WARNING: could not reopen .csv file '{x}' for database upload.".format(x=newf))
        print("WARNING: message: '{x}'".format(x=str(e)))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # parser.add_argument("-f", "--from_date", help="date to run the report from")
    # parser.add_argument("-t", "--to_date", help="date to run the report to")
    parser.add_argument("-s", "--source", help="use this .csv file (e.g. 'EZB-*_OA_*.csv') for upload")

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

    if args.source:
        newf = args.source
        filename = os.path.basename(newf)
        t = filename.find('_')
        alid = filename[:t].upper()
        upload_csv(newf, alid)
        exit(0)

    fname = app.config.get('EZB_SEARCH_PAGE', EZB_SEARCH_PAGE) # + "-EZB_current.csv"
    ia = app.config.get('EZB_SEARCH_HOST', EZB_SEARCH_HOST) + '/' + app.config.get('EZB_SEARCH_PAGE', EZB_SEARCH_PAGE)

    ae = requests.get(ia)

    if ae.status_code == 200:
        try:
            tree = lxml.html.fromstring(ae.content)
        except:
            print("ERROR: Could not parse .html page as tree.")
            print()
            exit(-3)

        print("INFO: xml tree read.")

        newf = "dummy"
        alid = "0"
        fieldnames = ["Institution", "EZB-Id", "Sigel"]
        csvfile = None
        part = {}

        for el in tree.iter():
            if el.tag == 'br' and el.tail is None: 
                continue
            if el.tag == 'h3':                              # h3 headline as AL seperator

                close_and_upload_csv(csvfile, newf, alid)   # first, pass all collected data so far to Alliance class
                                                            #        (i.e. import *previous* AL data to database)
                item = el.text.strip()
                s = item.rfind('(')
                t = item.rfind(')', s)
                alid = "0"
                if s >= 0 and t > s:
                    alid = item[s+1:t].upper()
                newf = "{x}-EZB_current-{a}.csv".format(a=alid, x=fname)
                try:
                    csvfile = open(newf, 'w')
                    outp = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                                   delimiter='\t', quoting=csv.QUOTE_ALL,
                                                   lineterminator='\n')
                    outp.writeheader()
                except IOError:
                    print("ERROR: could not write .csv file '{x}' (IOError).".format(x=newf))
                    print()
                    exit(-4)

            item = el.tail

            if item and item.startswith(': '):           # kill leading colon ': ' and, if necessary,
                item = item[1:].replace("\u0096", '-')   # funny hyphens...
            if el.text == 'Institution':
                if len(part) > 0:
                    if outp:
                        outp.writerow(part)
                    part = {}
                part[el.text] = item.strip().encode('utf-8')
            elif el.text == 'EZB-Id':
                part[el.text] = item.strip().encode('utf-8')
            elif el.text == 'Sigel':
                part[el.text] = item.strip().encode('utf-8')
            elif el.text is None and item:
                part['Institution'] = part.get('Institution', "") + " \r" + item.strip().encode('utf-8')

        if len(part) > 0:
            if outp:
                outp.writerow(part)

        print(csvfile, newf, alid)
        close_and_upload_csv(csvfile, newf, alid)

    else:
        print("ERROR: web page '{x}' not available (http {y}).".format(x=ia, y=ae.status_code))
