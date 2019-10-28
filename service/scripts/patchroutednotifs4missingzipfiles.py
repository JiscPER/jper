# This Python file uses the following encoding: utf-8
"""
This script copies (i.e. reassigns) each routed notifications so far collected
for standard accounts (i.e. hidden accounds in the background) to the corresponding
regular account if it exists (i.e. is registered with DeepGreen!).

"""
try:
    from octopus.core import add_configuration, app
    from service.models import Account,RoutedNotification
except:
    print "ERROR: Need to run from a virtualenv enabled setting, i.e."
    print "ERROR: run 'source ../../bin/activate' in some DG installation root folder first!"
    exit(-1)

import os


def repair_notes4missing_zip_files(packageprefs, page_size=1000):
    total = RoutedNotification.query(size=0).get('hits',{}).get('total',0)
    if total <= 0:
        print "ERROR: No routed notifications found."
        return False

    pages = (total / page_size) + 1

    for page in xrange(pages):
        frm = page*page_size
        print "% 8d" % frm
        for raw in RoutedNotification.query(_from=frm,size=page_size).get('hits',{}).get('hits',[]):
            if '_source' in raw:
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                repos = note.repositories
                npkgs = [lnk['packaging'] for lnk in note.links]
                for rid in note.repositories:
                    if rid in packageprefs:
                        prefs = packageprefs[rid]
                        for pref in prefs:
                            #
                            # ... still missing a considerable bit here ...
                            #


                note.save(type=typ)

    print
    print "INFO: {total} routed notifications processed and adjusted.".format(total=total)

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    #parser.add_argument("-i", "--input", help="input .csv file")
    parser.add_argument("-p", "--pagesize", help="page size of ES response to queries")
    parser.add_argument("--run", action="store_true", help="a tiny but effective(!!) security switch")

    args = parser.parse_args()

    if args.run is not True:
        print "ERROR: '--run switch is needed!"
        print
        exit(-1)

    if args.config:
        add_configuration(app, args.config)
    
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)

    repos = Account.pull_all_by_key(key='role',value='repository')
    packageprefs = { r.id: [ pref.split('/')[-1] for pref in r.data['packaging'] if len(pref.split('/') > 2 ] for r in repos if not r.data['repository']['bibid'].startswith('a') }


    if len(packageprefs) > 0:
        rc = repair_notes4missing_zip_files(packageprefs=packageprefs, page_size=page_size)
    else:
        print "INFO: No packaging tags at all found in regular accounts -- somehow confused; stop."

    print
    exit(0)
