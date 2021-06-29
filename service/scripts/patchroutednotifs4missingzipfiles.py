# This Python file uses the following encoding: utf-8
"""
This script copies (i.e. reassigns) each routed notifications collected so far
for standard accounts (i.e. hidden accounds in the background) to the corresponding
regular account if it exists (i.e. is registered with DeepGreen!).

"""
try:
    from octopus.core import add_configuration
    from service.models import Account,RoutedNotification
    from service.web import app
    from service import packages
    from flask import url_for
    from werkzeug.routing import BuildError
except:
    print("ERROR: Need to run from a virtualenv enabled setting, i.e.")
    print("ERROR: run 'source ../../bin/activate' in some DG installation root folder first!")
    exit(-1)


def repair_notes4missing_zip_files(packageprefs, page_size=1000):
    #
    modified = 0
    total = RoutedNotification.query(size=0).get('hits',{}).get('total',{}).get('value', 0)
    if total <= 0:
        app.logger.error("PatchRouted4MissingZips - No routed notifications found.")
        # print "ERROR: No routed notifications found."
        return False
    #
    pages = (total / page_size) + 1
    #
    for page in range(pages):
        frm = page*page_size
        print("% 8d" % frm)
        for raw in RoutedNotification.query(_from=frm,size=page_size).get('hits',{}).get('hits',[]):
            if '_source' in raw:
                note_id = raw['_id']
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                if note.packaging_format is None:
                    continue
                # get the package manager for this notification
                pm = packages.PackageFactory.converter(note.packaging_format)
                repos = note.repositories
                npkgs = [lnk['packaging'] for lnk in note.links]
                conversions = []
                for rid in repos:
                    if rid in packageprefs:
                        prefs = packageprefs[rid]
                        for pref in prefs:
                            #
                            if (not pref in npkgs) and (pm.convertible(pref)):
                                # add 'new' package format to notification's packaging list
                                conversions.append(pref)
                #
                # make list of missing conversions unique
                #
                conversions = list(set(conversions))
                if len(conversions) == 0:
                    continue

                app.logger.info("PatchRouted4MissingZips - Notification:{x} needs also the format(s) '{y}'".format(x=note_id,y=conversions)) 
                # at this point we have a de-duplicated list of missing formats that we 
                # need to additionally convert the note to, that the package is capable 
                # of converting itself into
                #
                # this pulls everything from remote storage, runs the conversion, and 
                # then synchronises back to remote storage
                done = packages.PackageManager.convert(note_id, 
                                                       note.packaging_format, 
                                                       conversions)
                #
                for d in done:
                    with app.test_request_context():
                        burl = app.config.get("BASE_URL")
                        if burl.endswith("/"):
                            burl = burl[:-1]
                        try:
                            url = burl + url_for("webapi.retrieve_content",
                                             notification_id=note_id, 
                                             filename=d[2])
                        except BuildError:
                            url = burl + "/notification/{x}/content/{y}".format(x=note_id, y=d[2])
                    nl = {
                        "type": "package",
                        "format": "application/zip",
                        "access": "router",
                        "url": url,
                        "packaging": d[0]
                    }
                    note.add_link( nl.get("url"),
                                   nl.get("type"),
                                   nl.get("format"),
                                   nl.get("access"),
                                   nl.get("packaging") )
                # ... and, finally, save the notification that includes all new links
                note.save(type=typ)
                modified += 1

    app.logger.info("PatchRouted4MissingZips - Finally, {modified}/{total} routed notification(s) modified.".format(modified=modified,total=total))
    # print
    # print "INFO: {modified}/{total} routed notifications adjusted.".format(modified=modified,total=total)

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
        app.logger.error("PatchRouted4MissingZips - Switch '--run' is missing! Stop.")
        print()
        print("ERROR: '--run switch is needed!")
        print()
        exit(-1)

    if args.config:
        add_configuration(app, args.config)
    
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)

    repos = Account.pull_all_by_key(key='role', value='repository')
    packageprefs = { r.id: [ pref for pref in r.data.get('packaging',[]) if len(pref.split('/')) > 2 ] for r in repos if not r.data['repository']['bibid'].startswith('a') }
    ## packageprefs = { r.id: [ pref.split('/')[-1] for pref in r.data.get('packaging',[]) if len(pref.split('/')) > 2 ] for r in repos if not r.data['repository']['bibid'].startswith('a') }


    if len(packageprefs) > 0:
        rc = repair_notes4missing_zip_files(packageprefs=packageprefs, page_size=page_size)
    else:
        app.logger.error("PatchRouted4MissingZips - No packaging tags at all found in regular accounts -- somehow confused; stop.")
        # print "INFO: No packaging tags at all found in regular accounts -- somehow confused; stop."

    print()
    exit(0)
