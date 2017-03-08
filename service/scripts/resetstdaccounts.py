"""
This is a script to create (or delete!!) account data in a live system,
as it is collected from a previous EZB service call.  

All records are put into possibly already existing alliance data. 
This means historical data will probably be overwritten/updated. 
So be warned/informed now!
"""
#from octopus.core import add_configuration, app
#from service.models import License, Alliance
## from datetime import datetime
import os, re, requests, csv
import glob, lxml.html

EZB_SEARCH_HOST = "http://rzbvm016.ur.de"
"""EZB web service hostname"""

EZB_SEARCH_PAGE = "OA_participants"
"""page name in the EZB instance"""

AFF_XPATH = "//datafield[@tag='110' or @tag='410' and not(./subfield[contains(@code,'b')]) and not(./subfield[contains(@code,'9')]) and not(./subfield[contains(@code,'g')]) and not(./subfield[contains(@code,'x')])]/subfield[@code='a']"
ADU_XPATH = "//datafield[@tag='510' and contains(./subfield[@code='9'],'4:adue')]/subfield[@code='0']"

def find_affiliation(http,recursion="full"):
    ans = []
    ia = http + '/about/marcxml'
    ae = requests.get(ia)
    
    if ae.status_code == 200:
        try:
            mrcxml = lxml.html.fromstring(ae.content)
            addrs = [x.text for x in mrcxml.xpath(ADU_XPATH) if x.text.startswith("http")]

            if recursion == "noadue" or len(addrs) == 0:
               return [x.text for x in mrcxml.xpath(AFF_XPATH)]
            else:
               for ht in addrs:
                   ans += find_affiliation(ht,recursion)
               return ans
        except:
            print "ERROR: Could not parse/xpath mrcxml for '{x}'.".format(x=http)
            print
            exit(-7)
    else:
        print "WARNING: Could not GET '{x}': HTTP/1.1 {y} {z}.".format(x=ia,
                                                                       y=ae.status_code,
                                                                       z=ae.reason)
    return ans


def load_gndidx(fname):
    txt = ""
    try:
        with open(fname,'r') as f:
            txt = f.read()
    except IOError:
        print "ERROR: could not gndidx file '{x}' (IOError).".format(x=fname)
        print
        exit(-3)

    return txt


def load_ezb2gnd(fname):
    gnd = {}
    try:
        with open(fname,'r') as f:
            for line in f:
                line=unicode(line.replace('\r','; '),'utf-8')
                key, val = line.split('\t')
                if key in gnd: 
                    gnd[key] += [ val[:-1] ] # [unicode(val[:-1],'utf-8')]
                else: 
                    gnd[key] = [ val[:-1] ] # [unicode(val[:-1],'utf-8')]
    except IOError:
        print "ERROR: Could not read ezb2gnd map '{x}' (IOError).".format(x=fname)
        print
        exit(-3)

    return gnd


def grep(text,pattern):
    return re.findall(r'%s' % pattern, text, flags=re.M)



def find_in_gndidx(fullname,ezbid,sigel,ezb2gnd,fname):

    print (u" %7s == %s ('%s')" % (ezbid, fullname, sigel)).encode('utf-8')

    recursion = 'full'

    if 'Planck' in fullname or 'Fraunhofer' in fullname or 'Leibniz' in fullname or 'Helmholtz' in fullname:
        recursion = 'noadue'

    if ezbid in ['aDLLR', 'aDZNE', 'aFZJUE', 'aDESY', 'aGFZPO', 'aIFZ', 'aMBCB', 
                 'aDM', 'aZBW', 'aFAB', 'aUBWH', 'aDPMA', 'aSUBHH', 'aHDZ' ]:
        recursion = 'noadue'

    if fullname in ezb2gnd:
        affs = []
        for corp in ezb2gnd[fullname]:
            # 2017-03-07 TD : Working here with 'popen' instead regular expressions
            #                 due to different encodings in ezb2gnd and gndidx
            #                 Needs review though: Adopt to new subprocess module!
            cmd = (u'grep "^%s\t" "%s"' % (corp,fname)).encode('utf-8')
            ### cmd = (u'grep "^%s\t" "%s" | cut -f2' % (corp,fname)).encode('utf-8')
            ans = os.popen(cmd).read().split('\n')
            while len(ans[-1]) == 0: ans = ans[:-1]
            ##print "DEBUG: {d}".format(d=ans)
            #if ans:
            #    https = unicode( ','.join(ans), 'utf-8' )
            #    print (u" %7s => %s : %s" % (ezbid, corp, https)).encode('utf-8')
            #else:
            print (u" %7s => %s" % (ezbid, corp)).encode('utf-8')

            for s in ans:
                http = s.split('\t')
                if http[0]: affs += [unicode(http[0],'utf-8')]
                if http[1]: affs += find_affiliation(http[1], recursion=recursion)

        for aff in sorted(set(affs)):
            if aff: print (u'%s' % aff).encode('utf-8')

    print
    return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # parser.add_argument("-f", "--from_date", help="date to run the report from")
    # parser.add_argument("-t", "--to_date", help="date to run the report to")

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

    oalist = glob.glob('OA_participants-EZB_current-NAL*.csv')

    if oalist:
        part = {}
        for fname in oalist:
            try:
                with open(fname, 'r') as f:
                    reader = csv.DictReader(f, fieldnames=['Institution', 'EZB-Id', 'Sigel'],
                                               quoting=csv.QUOTE_ALL, 
                                               delimiter='\t')
                    for row in reader:
                        if 'EZB-Id' in row and 'Institution' in row:
                            if 'Institution' in row['Institution']: continue 
                            part[unicode("a"+row['EZB-Id'],'utf-8')] = ( unicode(row['Institution'].replace('\r','; '),'utf-8'), unicode(row['Sigel'],'utf-8') )
            except IOError:
                print "ERROR: Could not read/parse '{x}' (IOError).".format(x=fname)

            print "INFO: Participant file '{x}' successfully read/parsed.".format(x=fname)

        print "INFO: All participant files processed; a total of {y} institution(s) found.".format(y=len(part))

        # print "DEBUG: {d}".format(d=part)
        # print "DEBUG:"
        idx = load_ezb2gnd('ezb_institution2gnd_corporate.csv')
        txt = "" # load_gndidx('gnd_corporate_tag110_idx.csv')

        for ezbid,val in part.items():
           fullname, sigel = val
           find_in_gndidx(fullname, ezbid, sigel, idx, 'gnd_corporate_tag110_idx.csv')

    else:
        print "ERROR: no flies 'OA_participants-EZB_current*.csv' found."
        print
        exit(-3)

