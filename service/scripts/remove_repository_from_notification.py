# This Python file uses the following encoding: utf-8
"""
This script copies (i.e. reassigns) each routed notifications so far collected
for standard accounts (i.e. hidden accounds in the background) to the corresponding
regular account if it exists (i.e. is registered with DeepGreen!) **AND** is given 
in some input CSV file (the same as for 'resetregularaccounts.py').
"""
try:
    from octopus.core import add_configuration, app
    from service.models import Account,RoutedNotification
except:
    print "ERROR: Need to run from a virtualenv enabled setting, i.e."
    print "ERROR: run 'source ../../bin/activate' in some DG installation root folder first!"
    exit(-1)

import os


#def process_notes (provider_id = '2316c44c4a504b489f20df170c1762da', repo_id = '16f01467d20c4e9484f8aeb6db25bf21', page_size=1000):
def process_notes (provider_id, repo_id, page_size=1000):
    total = RoutedNotification.query(size=0).get('hits',{}).get('total',0)
    if total <= 0:
        print "ERROR: No routed notifications found."
        return False

    pages = (total / page_size) + 1
    print 'Pages: %s, %s ' % (pages, page_size)
    
    for page in xrange(pages):
        frm = page*page_size
        print "% 8d" % frm
        for raw in RoutedNotification.query(_from=frm,size=page_size).get('hits',{}).get('hits',[]):
            if '_source' in raw:
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                note_provider_id = note.provider_id
                repos = []
                
                if provider_id==note.provider_id and repo_id in note.repositories:
                    for rid in note.repositories:
                        if rid<>repo_id:
                            repos.append(rid)
                    print 'Type:  %s' % typ
                    print 'Notif: %s' % note.id
                    print 'Prov:  %s' % note_provider_id
                    print 'Repo:  %s' % repo_id
                    print 'REPOS: %s' % note.repositories
                    print 'REPOS: %s' % repos
                    print
                #note.repositories = list(set(repos))
                #nrepos = len(note.repositories)
                #if nrepos > 1:
                #    note.reason = "Matched to {num} qualified repositories.".format(num=nrepos)
                # note.save(type=typ)

    print
    print "INFO: {total} routed notifications processed and adjusted.".format(total=total)

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    # parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")
    parser.add_argument("-p", "--pagesize", help="page size of ES response to queries")
    parser.add_argument("--run", action="store_true", help="a tiny but effective(!!) security switch")

    parser.add_argument("-r", "--repoid", help="DeepGreen Repository ID")
    parser.add_argument("-l", "--licid", help="DeepGreen License ID")

    args = parser.parse_args()

    if args.run is not True:
        print "ERROR: '--run switch is needed!"
        print
        exit(-1)

    if args.licid is None:
        print "ERROR: '--licid parameter required (DeepGreen License ID)'"
        print
        exit (-1) 
    
    if args.repoid is None:
        print "ERROR: '--repid parameter required (DeepGreen Repository ID)'"
        print
        exit (-1)    
        
    #if args.config:
    #    add_configuration(app, args.config)
    
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)
    print 'running ...'
    rc = process_notes(args.licid, args.repoid, page_size)
    exit(0)
    