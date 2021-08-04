"""
Functions which generate reports from the JPER system

"""

from service.models import RoutedNotification, FailedNotification, Account, MatchProvenance
import os
import unicodecsv
from octopus.lib import clcsv
from copy import deepcopy
from datetime import datetime
from octopus.core import app

# 2019-10-08 TD : adding an overall admin report statistics 
#
def admin_routed_report(from_date, to_date, reportfile):
    """
    Generate a (monthly) routed report from from_date to to_date.  It is assumed that 
    from_date is the start of a month, and to_date is the end of a month.

    Dates must be strings of the form YYYY-MM-DDThh:mm:ssZ

    :param from_date:   start of month date from which to generate the report
    :param to_date: end of month date up to which to generate the report (if this is not specified, it will default to datetime.utcnow())
    :param reportfile:  file path for existing/new report to be output
    :return:
    """
    # work out the whole months that we're operating over
    frstamp = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%SZ")
    if to_date is None:
        tostamp = datetime.utcnow()
    else:
        tostamp = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%SZ")
    months = list(range(frstamp.month, tostamp.month + 1))

    with open(reportfile,'wb') as f:
        writer = unicodecsv.writer(f,delimiter=',',quoting=unicodecsv.QUOTE_ALL,encoding='utf-8')
        writer.writerow( ('Send Date','Analysis Date','Publisher','ISSN','DOI','Repository','Reason','Match Date','Id') )
        # go through each routed notification 
        q = AdminReportQuery(from_date, to_date)
        types = None
        if RoutedNotification.__conn__.index_per_type:
            types = 'routed20*'
        for note in RoutedNotification.scroll(q.query(), page_size=2000, keepalive="25m", types=types):
            assert isinstance(note, RoutedNotification)
            nid = note.id
            created = note.created_date
            analysis = note.analysis_date
            publisher = note.publisher
            repos = list(set(note.repositories)) # trick to kill duplicate entries
 
            for match in MatchProvenance.pull_by_notification(nid):
                assert isinstance(match, MatchProvenance)
                matched = match.created_date
                bibid = match.bibid
                doi = match.alliance.get('doi')
                issn = match.alliance.get('issn')
                reason = match.provenance[0].get('explanation')
                repo = match.repository
                if repo in repos:
                    row = (created,analysis,publisher,issn,doi,bibid,reason,matched,nid)
                    writer.writerow(row)

def admin_failed_report(from_date, to_date, reportfile):
    """
    Generate a (monthly) failed report from from_date to to_date.  It is assumed that 
    from_date is the start of a month, and to_date is the end of a month.

    Dates must be strings of the form YYYY-MM-DDThh:mm:ssZ

    :param from_date:   start of month date from which to generate the report
    :param to_date: end of month date up to which to generate the report (if this is not specified, it will default to datetime.utcnow())
    :param reportfile:  file path for existing/new report to be output
    :return:
    """
    # work out the whole months that we're operating over
    frstamp = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%SZ")
    if to_date is None:
        tostamp = datetime.utcnow()
    else:
        tostamp = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%SZ")
    months = list(range(frstamp.month, tostamp.month + 1))

    with open(reportfile,'wb') as f:
        writer = unicodecsv.writer(f,delimiter=',',quoting=unicodecsv.QUOTE_ALL,encoding='utf-8')
        writer.writerow( ('Send Date','Analysis Date','Publisher','ISSN','DOI','Reason','Id') )
        # go through each failed notification 
        q = AdminReportQuery(from_date, to_date)
        for note in FailedNotification.scroll(q.query(), page_size=2000, keepalive="25m"):
            assert isinstance(note, FailedNotification)
            nid = note.id
            created = note.created_date
            analysis = note.analysis_date
            reason = note.reason
            if 'stalled' in reason.lower():
                publisher = note.provider_id
                issns = ['n/a']
                dois = ['n/a']
            else:
                publisher = note.publisher
                issns = [ k['id'] for k in note.identifiers if k['type']=='issn' ]
                dois = [ k['id'] for k in note.identifiers if k['type']=='doi' ]
                if len(dois) < 1:
                    dois = ['n/a']

            for issn in issns:
                for doi in dois:
                    row = (created,analysis,publisher,issn,doi,reason,nid)
                    writer.writerow(row)

#
# 2019-10-08 TD : end addition

def publisher_report(from_date, to_date, reportfile):
    """
    Generate a monthly publisher report from from_date to to_date.  It is assumed that 
    from_date is the start of a month, and to_date is the end of a month.

    Dates must be strings of the form YYYY-MM-DDThh:mm:ssZ

    :param from_date:   start of month date from which to generate the report
    :param to_date: end of month date up to which to generate the report (if this is not specified, it will default to datetime.utcnow())
    :param reportfile:  file path for existing/new report to be output
    :return:
    """
    # work out the whole months that we're operating over
    frstamp = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%SZ")
    if to_date is None:
        tostamp = datetime.utcnow()
    else:
        tostamp = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%SZ")
    months = list(range(frstamp.month, tostamp.month + 1))

    # prep the data structures where we're going to record the results
    result = {}
    uniques = {}
    for m in months:
        uniques[m] = {"md" : 0, "content" : 0, "failed": 0}
    pubs = {}

    # go through each routed *AND* failed notification and count against the publisher ids whether 
    # something is a md-only or a with-content notification, and at the same time count the 
    # unique md-only vs with-content notifications that were routed *OR* not
    q = DeliveryReportQuery(from_date, to_date)
    types = None
    if RoutedNotification.__conn__.index_per_type:
        types = 'routed20*'
    for note in RoutedNotification.scroll(q.query(), page_size=200, keepalive="25m", types=types):
        assert isinstance(note, RoutedNotification)
        nm = note.analysis_datestamp.month

        is_with_content = False
        if len(note.links) > 0:
            is_with_content = True
            uniques[nm]["content"] += 1
        else:
            uniques[nm]["md"] += 1

        p = note.provider_id
        if p not in result:
            result[p] = {}
            for m in months:
                result[p][m] = {"md" : 0, "content" : 0, "failed": 0}

        if is_with_content:
            result[p][nm]["content"] += 1
        else:
            result[p][nm]["md"] += 1

    # now (almost) the same procedure for the rejected notes (with NO delivery)
    for note in FailedNotification.scroll(q.query(), page_size=1500, keepalive="30m"):
        assert isinstance(note, FailedNotification)
        nm = note.analysis_datestamp.month

        #is_with_content = False
        #if len(note.links) > 0:
        #    is_with_content = True
        #    uniques[nm]["content"] += 1
        #else:
        #    uniques[nm]["md"] += 1
        uniques[nm]["failed"] += 1

        ##for p in [note.provider_id,]:
        p = note.provider_id
        if p not in result:
            result[p] = {}
            for m in months:
                result[p][m] = {"md" : 0, "content" : 0, "failed": 0}

        #if is_with_content:
        #    result[p][nm]["content"] += 1
        #else:
        #    result[p][nm]["md"] += 1
        result[p][nm]["failed"] += 1


    # now flesh out the report with account names and totals
    for k in list(result.keys()):
        acc = Account.pull(k)
        if acc is None:
            pubs[k] = k
        else:
            if acc.data["email"] is not None:
                pubs[k] = acc.data["email"].split("@")[0]
            else:
                pubs[k] = k

        # print "Publisher '{name}' encountered.".format(name=pubs[k])

        for mon in list(result[k].keys()):
            result[k][mon]["total"] = result[k][mon]["md"]
            result[k][mon]["total"] += result[k][mon]["content"]
            result[k][mon]["total"] += result[k][mon]["failed"] 

    for mon in list(uniques.keys()):
        uniques[mon]["total"] = uniques[mon]["md"]
        uniques[mon]["total"] += uniques[mon]["content"]
        uniques[mon]["total"] += uniques[mon]["failed"]

    # some constant bits of information we're going to need to convert the results into a table
    # suitable for a CSV

    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    headers = ['Publisher','ID',
               'Jan md-only', "Jan with-content", "Jan rejected", "Jan Total",
               'Feb md-only', "Feb with-content", "Feb rejected", "Feb Total",
               'Mar md-only', "Mar with-content", "Mar rejected", "Mar Total",
               'Apr md-only', "Apr with-content", "Apr rejected", "Apr Total",
               'May md-only', "May with-content", "May rejected", "May Total",
               'Jun md-only', "Jun with-content", "Jun rejected", "Jun Total",
               'Jul md-only', "Jul with-content", "Jul rejected", "Jul Total",
               'Aug md-only', "Aug with-content", "Aug rejected", "Aug Total",
               'Sep md-only', "Sep with-content", "Sep rejected", "Sep Total",
               'Oct md-only', "Oct with-content", "Oct rejected", "Oct Total",
               'Nov md-only', "Nov with-content", "Nov rejected", "Nov Total",
               'Dec md-only', "Dec with-content", "Dec rejected", "Dec Total"]

    template = {}
    for k in headers:
        template[k] = 0

    # an interim data-structure that we'll use to store the objects to be written, which we
    # can then order by the key (which will be the Pub name)
    data = {}

    # read any existing data in from the current spreadsheet
    if os.path.exists(reportfile):
        sofar = clcsv.ClCsv(file_path=reportfile)
        for obj in sofar.objects():
            # convert all the fields to integers as needed
            for k in list(obj.keys()):
                if k not in ["Publisher", "ID"]:
                    if obj[k] == "":
                        obj[k] = 0
                    else:
                        try:
                            obj[k] = int(obj[k])
                        except:
                            app.logger.warn("Unable to coerce existing report value '{x}' to an integer, so assuming it is 0".format(x=obj[k]))
                            obj[k] = 0

            data[obj.get("Publisher")] = obj


    # now add any new data from the report
    for id, res in result.items():
        pub = pubs.get(id)
        if pub not in data:
            data[pub] = deepcopy(template)
        data[pub]["Publisher"] = pub
        data[pub]["ID"] = id
        for mon, info in res.items():
            mn = month_names[mon - 1]
            mdk = mn + " md-only"
            ctk = mn + " with-content"
            rjk = mn + " rejected"
            tk = mn + " Total"
            data[pub][mdk] = info.get("md")
            data[pub][ctk] = info.get("content")
            data[pub][rjk] = info.get("failed")
            data[pub][tk] = info.get("total")

    # remove the "total" and "unique" entries, as we need to re-create them
    if "Total" in data:
        del data["Total"]
    existing_unique = deepcopy(template)
    existing_unique["Publisher"] = "Unique"
    existing_unique["ID"] = ""
    if "Unique" in data:
        existing_unique = data["Unique"]
        del data["Unique"]

    # calculate the totals for all columns
    totals = {}
    for k in headers:
        totals[k] = 0

    totals["Publisher"] = "Total"
    totals["ID"] = ""

    for pub, obj in data.items():
        for k, v in obj.items():
            if k in ["Publisher", "ID"]:
                continue
            if isinstance(v, int):
                totals[k] += v

    data["Total"] = totals

    # add the uniques
    data["Unique"] = existing_unique
    data["Unique"]["Publisher"] = "Unique"

    for mon, info in uniques.items():
        mn = month_names[mon - 1]
        mdk = mn + " md-only"
        ctk = mn + " with-content"
        rjk = mn + " rejected"
        tk = mn + " Total"
        data["Unique"][mdk] = info.get("md")
        data["Unique"][ctk] = info.get("content")
        data["Unique"][rjk] = info.get("failed")
        data["Unique"][tk] = info.get("total")

    orderedkeys = list(data.keys())
    orderedkeys.remove('Unique')
    orderedkeys.remove('Total')
    orderedkeys.sort()
    orderedkeys.append('Total')
    # 2018-01-09 TD : Unique row for publishing houses makes not really sense, so we better 
    #                 leave it out (just to avoid endless discussions, justifications, headaches)
    #orderedkeys.append('Unique')

    # remove the old report file, so we can start with a fresh new one
    try:
        os.remove(reportfile)
    except:
        pass

    out = clcsv.ClCsv(file_path=reportfile)
    out.set_headers(headers)

    for pk in orderedkeys:
        pub = data[pk]
        out.add_object(pub)

    out.save()



def delivery_report(from_date, to_date, reportfile):
    """
    Generate the monthly report from from_date to to_date.  It is assumed that from_date is
    the start of a month, and to_date is the end of a month.

    Dates must be strings of the form YYYY-MM-DDThh:mm:ssZ

    :param from_date:   start of month date from which to generate the report
    :param to_date: end of month date up to which to generate the report (if this is not specified, it will default to datetime.utcnow())
    :param reportfile:  file path for existing/new report to be output
    :return:
    """
    # work out the whole months that we're operating over
    frstamp = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%SZ")
    if to_date is None:
        tostamp = datetime.utcnow()
    else:
        tostamp = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%SZ")
    months = list(range(frstamp.month, tostamp.month + 1))

    # prep the data structures where we're going to record the results
    result = {}
    uniques = {}
    for m in months:
        uniques[m] = {"md" : 0, "content" : 0}
    heis = {}

    # go through each routed notification and count against the repository ids whether something is
    # a md-only or a with-content notification, and at the same time count the unique md-only vs with-content
    # notifications that were routed
    q = DeliveryReportQuery(from_date, to_date)
    types = None
    if RoutedNotification.__conn__.index_per_type:
        types = 'routed20*'
    for note in RoutedNotification.scroll(q.query(), page_size=200, keepalive="25m", types=types):
        assert isinstance(note, RoutedNotification)
        nm = note.analysis_datestamp.month

        is_with_content = False
        if len(note.links) > 0:
            is_with_content = True
            uniques[nm]["content"] += 1
        else:
            uniques[nm]["md"] += 1

        # 2019-03-05 TD : we need to eliminate doubles here!!! Seriously.
        for r in list(set(note.repositories)):
            if r not in result:
                result[r] = {}
                for m in months:
                    result[r][m] = {"md" : 0, "content" : 0}

            if is_with_content:
                result[r][nm]["content"] += 1
            else:
                result[r][nm]["md"] += 1

    # now flesh out the report with account names and totals
    for k in list(result.keys()):
        acc = Account.pull(k)
        if acc is None:
            heis[k] = k
        else:
            if acc.repository_name is not None:
                heis[k] = acc.repository_name
            else:
                heis[k] = k

        for mon in list(result[k].keys()):
            result[k][mon]["total"] = result[k][mon]["md"] + result[k][mon]["content"]

    for mon in list(uniques.keys()):
        uniques[mon]["total"] = uniques[mon]["md"] + uniques[mon]["content"]

    # some constant bits of information we're going to need to convert the results into a table
    # suitable for a CSV

    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    headers = ['HEI','ID',
               'Jan md-only', "Jan with-content", "Jan Total",
               'Feb md-only', "Feb with-content", "Feb Total",
               'Mar md-only', "Mar with-content", "Mar Total",
               'Apr md-only', "Apr with-content", "Apr Total",
               'May md-only', "May with-content", "May Total",
               'Jun md-only', "Jun with-content", "Jun Total",
               'Jul md-only', "Jul with-content", "Jul Total",
               'Aug md-only', "Aug with-content", "Aug Total",
               'Sep md-only', "Sep with-content", "Sep Total",
               'Oct md-only', "Oct with-content", "Oct Total",
               'Nov md-only', "Nov with-content", "Nov Total",
               'Dec md-only', "Dec with-content", "Dec Total"]

    template = {}
    for k in headers:
        template[k] = 0

    # an interim data-structure that we'll use to store the objects to be written, which we
    # can then order by the key (which will be the HEI name)
    data = {}

    # read any existing data in from the current spreadsheet
    if os.path.exists(reportfile):
        sofar = clcsv.ClCsv(file_path=reportfile)
        for obj in sofar.objects():
            # convert all the fields to integers as needed
            for k in list(obj.keys()):
                if k not in ["HEI", "ID"]:
                    if obj[k] == "":
                        obj[k] = 0
                    else:
                        try:
                            obj[k] = int(obj[k])
                        except:
                            app.logger.warn("Unable to coerce existing report value '{x}' to an integer, so assuming it is 0".format(x=obj[k]))
                            obj[k] = 0

            data[obj.get("HEI")] = obj


    # now add any new data from the report
    for id, res in result.items():
        hei = heis.get(id)
        if hei not in data:
            data[hei] = deepcopy(template)
        data[hei]["HEI"] = hei
        data[hei]["ID"] = id
        for mon, info in res.items():
            mn = month_names[mon - 1]
            mdk = mn + " md-only"
            ctk = mn + " with-content"
            tk = mn + " Total"
            data[hei][mdk] = info.get("md")
            data[hei][ctk] = info.get("content")
            data[hei][tk] = info.get("total")

    # remove the "total" and "unique" entries, as we need to re-create them
    if "Total" in data:
        del data["Total"]
    existing_unique = deepcopy(template)
    existing_unique["HEI"] = "Unique"
    existing_unique["ID"] = ""
    if "Unique" in data:
        existing_unique = data["Unique"]
        del data["Unique"]

    # calculate the totals for all columns
    totals = {}
    for k in headers:
        totals[k] = 0

    totals["HEI"] = "Total"
    totals["ID"] = ""

    for hei, obj in data.items():
        for k, v in obj.items():
            if k in ["HEI", "ID"]:
                continue
            if isinstance(v, int):
                totals[k] += v

    data["Total"] = totals

    # add the uniques
    data["Unique"] = existing_unique
    data["Unique"]["HEI"] = "Unique"

    for mon, info in uniques.items():
        mn = month_names[mon - 1]
        mdk = mn + " md-only"
        ctk = mn + " with-content"
        tk = mn + " Total"
        data["Unique"][mdk] = info.get("md")
        data["Unique"][ctk] = info.get("content")
        data["Unique"][tk] = info.get("total")

    orderedkeys = list(data.keys())
    orderedkeys.remove('Unique')
    orderedkeys.remove('Total')
    orderedkeys.sort()
    orderedkeys.append('Total')
    orderedkeys.append('Unique')

    # remove the old report file, so we can start with a fresh new one
    try:
        os.remove(reportfile)
    except:
        pass

    out = clcsv.ClCsv(file_path=reportfile)
    out.set_headers(headers)

    for hk in orderedkeys:
        hei = data[hk]
        out.add_object(hei)

    out.save()

class DeliveryReportQuery(object):
    def __init__(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {
                            "range" : {
                                "analysis_date" : {
                                    "gte" : self.from_date,
                                    "lt" : self.to_date
                                }
                            }
                        }
                    ]
                }
            },
            "sort" : [
                {"analysis_date" : {"order" :  "asc"}}
            ]
        }

class AdminReportQuery(object):
    def __init__(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {
                            "range" : {
                                "created_date" : {
                                    "gte" : self.from_date,
                                    "lt" : self.to_date
                                }
                            }
                        }
                    ]
                }
            },
            "sort" : [
                {"analysis_date" : {"order" :  "asc"}}
            ]
        }
