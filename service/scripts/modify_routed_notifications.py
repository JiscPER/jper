# This Python file uses the following encoding: utf-8
# This Python file uses the following encoding: utf-8
"""
This script removes repository IDs from notifications already being 
routed. The special use case has been the clean up FID repositories
from "gold" providers MPI / Future Scrience.

Usage: modify_routed_notifications.py [-r REPOIDS] [-z FAILEDID]
                                      [-a ACCOUNTID] [-f FILE] 
                                      [--show] [--update]
                                      [-p PAGESIZE] [--run] [-h] 
Parameters:
  -r REPOIDS, 
  --repoids REPOIDS   DeepGreen Repository Account IDs (comma separated list)
  
  -z FAILEDID, 
  --failedid FAILEDID DeepGreen Repository's Account ID for failed notifications
  
  -f FILE, 
  --file FILE            File containing notification IDs
  -a ACCOUNTID, 
  --accountid ACCOUNTID  DeepGreen Publisher's Account ID
  (Either a publisher ID or a File with notification IDs can be processed)

  --show                show matching notifications only
  --update              update matching notifications
  (Either --show or --update switch can be used)
  
  --run                 a tiny but effective(!!) security switch in conjunction with update
    
  -p PAGESIZE,
  --pagesize PAGESIZE
                        page size of ES response to queries

  -h, --help            show this help message and exit

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

# def process_notes (provider_id, repo_ids, page_size=1000):
def process_notes(provider_id, repo_ids, failedid=None, notification_list=None, perform_update=False, page_size=1000):
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
            #print raw['_id']
            #print raw['_type']
            #print raw['_source']
            if '_source' in raw:
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                note_provider_id = note.provider_id
                repos = []
                # print raw['_id'], note.id, notification_list
                
                if notification_list == [] or note.id in notification_list:  
                    # print 'Notif: %s' % note.id
                    
                    if (provider_id is None) or provider_id==note_provider_id:
                        # print 'Notif/Prov: %s %s' % (note.id, note_provider_id)
                        
                        if sublist_element_in_list(repo_list,note.repositories):
                            number_matched_notfications = number_matched_notfications + 1
                            for rid in note.repositories:
                                if rid not in repo_list:
                                    repos.append(rid)
                            if repos==[] and failedid is not None:
                                repos.append(failedid)
                            print 'Type:  %s' % typ
                            print 'Notif: %s' % note.id
                            print 'Prov:  %s' % note_provider_id
                            print 'Repo:  %s' % repo_ids
                            print 'REPOS: %s' % note.repositories
                            print 'REPOS: %s' % repos
                            
                            note.repositories = list(set(repos))
                            nrepos = len(note.repositories)
                            if note.repositories == [failedid]:
                                note.reason = "Matched to dummy repository only, regard this as a failed notification"
                            if nrepos > 1:
                                note.reason = "Matched to {num} qualified repositories.".format(num=nrepos)
                            print "Repos:  ", note.repositories
                            print "Reason: ", note.reason
                            print
                            
                            if perform_update:
                                print note
                                # print "update not implemented yet"
                                print                                
                                note.save(type=typ)

    print
    print "INFO: %s routed notifications processed and %s need to be adjusted." % (total, number_matched_notfications)

    return True



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    # parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")
    parser.add_argument("-p", "--pagesize", help="page size of ES response to queries")
    parser.add_argument("--run",    action="store_true",  help="a tiny but effective(!!) security switch")
    parser.add_argument("--show",   action="store_true",  help="show matching notifications only")
    parser.add_argument("--update", action="store_true",  help="update matching notifications")

    parser.add_argument("-f", "--file",      help="File containing notification IDs")
    parser.add_argument("-r", "--repoids",   help="DeepGreen Repository Account IDs (comma separated  list)")
    parser.add_argument("-a", "--accountid", help="DeepGreen Publisher's Account ID")
    parser.add_argument("-z", "--failedid",  help="DeepGreen Repository's Account ID for failed notifications")
    

    args = parser.parse_args()
    notification_list = []

    print """
Publisher Account: %s
Repositories:      %s
Account/Failked:   %s
File:              %s
Perform Update:    %s
Show:              %s
Update:            %s""" % (args.accountid, args.repoids, args.failedid, args.file, args.update, args.show, args.update)
        
    
    if (args.show and args.update) or (not args.show and not args.update):
        print "ERROR: 'either --show or --update switch must be used!"
        print
        exit(-1)

    if (args.update and args.failedid is None):
        print "ERROR: 'either --update is only allowed with parameter --failedid!"
        print
        exit(-1)

    if (args.accountid is None and args.file is None) or (args.accountid is not None and args.file is not None):
        print "ERROR: 'either parameter --accountid or --file parameter must be used!"
        print
        exit(-1)
     
    if args.repoids is None:
        print "ERROR: '--repoids parameter required (DeepGreen Repository IDs (comma separated  list))'"
        print
        exit (-1)    

    if args.file is not None:
        with open(args.file) as f:
            notification_list = f.read().splitlines()
    
    if args.update is True and args.run is not True:
        print "ERROR: '--run switch is needed when running update!"
        print
        exit(-1)
        
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)
    print 'running ...'
    
    print """
Publisher Account: %s
Repositories:      %s
Account/Failked:   %s
Notifications:     %s
Perform Update:    %s
Page Size:         %s""" % (args.accountid, args.repoids, args.failedid, notification_list, args.update, page_size)
    #exit(-1)
    
    rc = process_notes(args.accountid, args.repoids, args.failedid, notification_list, args.update, page_size)
    exit(0)
    