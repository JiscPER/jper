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

def sublist_element_in_list(sublist, list):
    for element in sublist:
        if element in list:
            return True
    return False

def process_notes (provider_id, repo_ids, page_size=1000):
    repo_list = repo_ids.split(",")
    print 'Provider ID    (DeepGreen Account): %s' % provider_id
    print 'Repository IDs (DeepGreen Account): %s' % repo_ids
    total = RoutedNotification.query(size=0).get('hits',{}).get('total',0)
    if total <= 0:
        print "ERROR: No routed notifications found."
        return False

    pages = (total / page_size) + 1
    print 'Pages: %s, %s ' % (pages, page_size)
    
    number_matched_notfications  = 0
    for page in xrange(pages):
        frm = page*page_size
        print "% 8d" % frm
        for raw in RoutedNotification.query(_from=frm,size=page_size).get('hits',{}).get('hits',[]):
            if '_source' in raw:
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                note_provider_id = note.provider_id
                repos = []
                
                if provider_id==note.provider_id and sublist_element_in_list(repo_list,note.repositories):
                    number_matched_notfications = number_matched_notfications + 1
                    for rid in note.repositories:
                        if rid not in repo_list:
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
    print "INFO: %s routed notifications processed and %s need to be adjusted." % (total, number_matched_notfications)

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    # parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")
    parser.add_argument("-p", "--pagesize", help="page size of ES response to queries")
    parser.add_argument("--show", action="store_true", help="a tiny but effective(!!) security switch")

    parser.add_argument("-r", "--repoids",   help="DeepGreen Repository IDs (comma separated  list)")
    parser.add_argument("-a", "--accountid", help="DeepGreen Publisher's Account ID")

    args = parser.parse_args()

    if args.accountid is None:
        print "ERROR: '--accountid parameter required (DeepGreen Publisher's Account ID)'"
        print
        exit (-1) 
    
    if args.repoids is None:
        print "ERROR: '--repoids parameter required (DeepGreen Repository IDs (comma separated  list))'"
        print
        exit (-1)    
 
    if args.show is not True:
        print "ERROR: '--show switch is needed!"
        print
        exit(-1)
       
    #if args.config:
    #    add_configuration(app, args.config)
    
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)
    print 'running ...'
    rc = process_notes(args.accountid, args.repoid, page_size)
    exit(0)
    