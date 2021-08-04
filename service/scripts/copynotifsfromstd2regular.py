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
    print("ERROR: Need to run from a virtualenv enabled setting, i.e.")
    print("ERROR: run 'source ../../bin/activate' in some DG installation root folder first!")
    exit(-1)

OA_PARTICIPANTS_GLOB = "OA_participants*.csv"
"""Lists of OA participants (as already determined from EZB)"""


def make_hidden2regular(hidden, regular={}):
    hid2reg = {}
    for x in hidden:
        regids = []
        ezbid = hidden[x][1:].upper()
        if ezbid in list(regular.values()):
            regids = [ y for y in regular if ezbid == regular[y] ]
        if len(regids) > 0:
            if x in hid2reg:
                regids = hid2reg[x] + regids
            hid2reg[x] = list(set(regids))

    return hid2reg


def assign_hidnotes2regular(hid2reg={}, page_size=1000):
    total = RoutedNotification.query(size=0).get('hits',{}).get('total',{}).get('value', 0)
    if total <= 0:
        print("ERROR: No routed notifications found.")
        return False

    pages = (total / page_size) + 1

    for page in range(pages):
        frm = page*page_size
        print("% 8d" % frm)
        for raw in RoutedNotification.query(_from=frm,size=page_size).get('hits',{}).get('hits',[]):
            if '_source' in raw:
                typ = raw['_type']
                note = RoutedNotification(raw['_source'])
                repos = note.repositories
                for rid in note.repositories:
                    if rid in hid2reg:
                        repos = repos + hid2reg[rid]
                note.repositories = list(set(repos))
                nrepos = len(note.repositories)
                if nrepos > 1:
                    note.reason = "Matched to {num} qualified repositories.".format(num=nrepos)

                note.save(type=typ)

    print()
    print("INFO: {total} routed notifications processed and adjusted.".format(total=total))

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    parser.add_argument("-i", "--input", help="CSV file name(s) of (regular!) repository accounts [cur.val.: `{x}´]".format(x=OA_PARTICIPANTS_GLOB))
    parser.add_argument("-p", "--pagesize", help="page size of ES response to queries")
    parser.add_argument("--run", action="store_true", help="a tiny but effective(!!) security switch")
    parser.add_argument("-e", "--ezbid", help="EZB-Id of Repo ")

    args = parser.parse_args()

    if args.run is not True:
        print("ERROR: '--run switch is needed!")
        print()
        exit(-1)

    if args.ezbid is not None and args.input is not None:
        print("ERROR: 'either use switch --ezbid or --input'")
        print()
        exit (-1
) 
    if args.config:
        add_configuration(app, args.config)
    
    page_size = 1000
    if args.pagesize is not None:
        page_size = int(args.pagesize)

    #if args.input is not None:
    #    OA_PARTICIPANTS_GLOB = args.input
    #
    #oa_plist = glob.glob(OA_PARTICIPANTS_GLOB)
    #
    #print "INFO: %s" % oa_plist

    
        
    repos = Account.pull_all_by_key(key='role', value='repository')
    hidden = { r.id: r.data['repository']['bibid'] for r in repos if r.data['repository']['bibid'].startswith('a') }
    regular = { r.id: r.data['repository']['bibid'].upper() for r in repos if not r.data['repository']['bibid'].startswith('a') }

    print("""INFO:
        hidden:  %s 
        regular: %s""" % (hidden, regular))


    filtered_reg = {}

    if args.ezbid:
        part = [ str(args.ezbid) ]
        filtered_reg = { rid : bibid for rid,bibid in list(regular.items()) if bibid in part }
    
    


    
    if False:
        # if oa_plist:
        part = []
        for fname in oa_plist:
            try:
                with open(fname, 'r') as f:
                    reader = csv.DictReader(f, fieldnames=['Institution','EZB-Id','Sigel'],
                                               quoting=csv.QUOTE_ALL,
                                               delimiter='\t')
                    for row in reader:
                        if 'EZB-Id' in row and 'Institution' in row:
                            if 'Institution' in row['Institution']: continue
                            print("DEBUG: EZB-ID: %s" % row['EZB-Id'])
                            part.append( str(row['EZB-Id'], 'utf-8') )
            except IOError:
                print("ERROR: Could not read/parse '{x}' (IOError).".format(x=fname))

            print("INFO: Participant file '{x}' successfully read/parsed.".format(x=fname))
        
        print("DEBUG: part %s" % (part))
        
        part = list(set(part))
        filtered_reg = { rid : bibid for rid,bibid in list(regular.items()) if bibid in part }
        print("INFO: Participant files processed; total of {y} institution(s) listed.".format(y=len(part)))

    
    print("INFO: Filter step with input CSV files left {y} receiving repository account(s) (of {z}).".format(y=len(filtered_reg), z=len(regular)))

    ### hid2reg = make_hidden2regular(hidden,regular)
    hid2reg = make_hidden2regular(hidden,filtered_reg)

    print("hid2reg: %s" % hid2reg)
    # exit(-1) 
    
    if len(hid2reg) > 0:
        rc = assign_hidnotes2regular(hid2reg=hid2reg, page_size=page_size)
    else:
        print("INFO: No std/hidden accounts found in ES to be processed, stop.")

    print()
    exit(0)
