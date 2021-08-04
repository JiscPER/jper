"""
Blueprint for providing account management
"""

import uuid, json, time, requests

from flask import Blueprint, request, url_for, flash, redirect, render_template, abort, send_file
from service.forms.adduser import AdduserForm
from flask_login import login_user, logout_user, current_user
from octopus.core import app
from octopus.lib import dates
from service.api import JPER, ParameterException
from service.views.webapi import _bad_request
from service.repository_licenses import get_matching_licenses
import math
import csv
from jsonpath_rw_ext import parse
from itertools import zip_longest
from service import models
from io import StringIO, TextIOWrapper, BytesIO

blueprint = Blueprint('account', __name__)

# Notification table/csv for repositories
ntable = {
            "screen" : ["Send Date", ["DOI","Publisher"], ["Publication Date", "Embargo"], "Title", "Analysis Date"],
            "header" : ["Send Date", "DOI", "Publisher", "Publication Date", "Embargo", "Title", "Analysis Date"],
     "Analysis Date" : "notifications[*].analysis_date",
         "Send Date" : "notifications[*].created_date",
           "Embargo" : "notifications[*].embargo.duration",
               "DOI" : "notifications[*].metadata.identifier[?(@.type=='doi')].id",
         "Publisher" : "notifications[*].metadata.publisher",
             "Title" : "notifications[*].metadata.title",
  "Publication Date" : "notifications[*].metadata.publication_date"
}

# Matching table/csv for providers (with detailed reasoning)
mtable = {
         "screen" : ["Analysis Date", "ISSN or EISSN", "DOI", "License", "Forwarded to {EZB-Id}", "Term", "Appears in {notification_field}"],
         "header" : ["Analysis Date", "ISSN or EISSN", "DOI", "License", "Forwarded to", "Term", "Appears in"],
  "Analysis Date" : "matches[*].created_date",
  "ISSN or EISSN" : "matches[*].alliance.issn",
            "DOI" : "matches[*].alliance.doi",
        "License" : "matches[*].alliance.link",
   "Forwarded to" : "matches[*].bibid",
           "Term" : "matches[*].provenance[0].term",
     "Appears in" : "matches[*].provenance[0].notification_field"
}

# Rejected table/csv for providers
ftable = {
         "screen" : ["Send Date", "ISSN or EISSN", "DOI", "Reason", "Analysis Date"],
         "header" : ["Send Date", "ISSN or EISSN", "DOI", "Reason", "Analysis Date"],
      "Send Date" : "failed[*].created_date",
  "Analysis Date" : "failed[*].analysis_date",
  "ISSN or EISSN" : "failed[*].issn_data",
            "DOI" : "failed[*].metadata.identifier[?(@.type=='doi')].id",
         "Reason" : "failed[*].reason"
}

# Config table/csv for repositories
ctable = {
        # "screen" : ["Name Variants", "Domains", "Grant Numbers", "ORCIDs", "Author Emails", "Keywords"],
        # "header" : ["Name Variants", "Domains", "Grant Numbers", "ORCIDs", "Author Emails", "Keywords"],
        "screen" : ["Name Variants", "Domains", "Grant Numbers", "Keywords"],
        "header" : ["Name Variants", "Domains", "Grant Numbers", "Dummy1", "Dummy2", "Keywords"],
 "Name Variants" : "repoconfig[0].name_variants[*]",
       "Domains" : "repoconfig[0].domains[*]",
#     "Postcodes" : "repoconfig[0].postcodes[*]",
 "Grant Numbers" : "repoconfig[0].grants[*]",
        "Dummy1" : "repoconfig[0].author_ids[?(@.type=='xyz1')].id",
        "Dummy2" : "repoconfig[0].author_ids[?(@.type=='xyz2')].id",
#        "ORCIDs" : "repoconfig[0].author_ids[?(@.type=='orcid')].id",
# "Author Emails" : "repoconfig[0].author_ids[?(@.type=='email')].id",
      "Keywords" : "repoconfig[0].keywords[*]",
}


def _list_failrequest(provider_id=None, bulk=False):
    """
    Process a list request, either against the full dataset or the specific provider_id supplied
    This function will pull the arguments it requires out of the Flask request object.  See the API documentation
    for the parameters of these kinds of requests.

    :param provider_id: the provider id to limit the request to
    :param bulk: (boolean) whether bulk (e.g. *not* paginated) is returned or not
    :return: Flask response containing the list of notifications that are appropriate to the parameters
    """
    since = _validate_since()
    page = _validate_page()
    page_size = _validate_page_size()

    try:
        if bulk is True:
            flist = JPER.bulk_failed(current_user, since, provider_id=provider_id)
        else:
            flist = JPER.list_failed(current_user, since, page=page, page_size=page_size, provider_id=provider_id)
    except ParameterException as e:
        return _bad_request(str(e))

    return flist.json()


def _list_matchrequest(repo_id=None, provider=False, bulk=False):
    """
    Process a list request, either against the full dataset or the specific repo_id supplied
    This function will pull the arguments it requires out of the Flask request object.  See the API documentation
    for the parameters of these kinds of requests.

    :param repo_id: the repo id to limit the request to
    :param provider: (boolean) whether the repo_id belongs to a publisher or not
    :param bulk: (boolean) whether bulk (e.g. *not* paginated) is returned or not
    :return: Flask response containing the list of notifications that are appropriate to the parameters
    """
    since = _validate_since()
    page = _validate_page()
    page_size = _validate_page_size()

    try:
        # nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id)
        # 2016-11-24 TD : bulk switch to decrease the number of different calls
        if bulk:
            mlist = JPER.bulk_matches(current_user, since, repository_id=repo_id, provider=provider)
        else:
            # 2016-09-07 TD : trial to include some kind of reporting for publishers here!
            mlist = JPER.list_matches(current_user, since, page=page, page_size=page_size, repository_id=repo_id,
                                      provider=provider)
    except ParameterException as e:
        return _bad_request(str(e))

    return mlist.json()


def _list_request(repo_id=None, provider=False, bulk=False):
    """
    Process a list request, either against the full dataset or the specific repo_id supplied
    This function will pull the arguments it requires out of the Flask request object.  See the API documentation
    for the parameters of these kinds of requests.

    :param repo_id: the repo id to limit the request to
    :param provider: (boolean) whether the repo_id belongs to a publisher or not
    :param bulk: (boolean) whether bulk (e.g. *not* paginated) is returned or not
    :return: Flask response containing the list of notifications that are appropriate to the parameters
    """
    since = _validate_since()
    page = _validate_page()
    page_size = _validate_page_size()

    try:
        # nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id)
        # 2016-11-24 TD : bulk switch to decrease the number of different calls
        if bulk is True:
            nlist = JPER.bulk_notifications(current_user, since, repository_id=repo_id, provider=provider)
        else:
            # 2016-09-07 TD : trial to include some kind of reporting for publishers here!
            nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id,
                                            provider=provider)
    except ParameterException as e:
        return _bad_request(str(e))

    return nlist.json()


# 2016-11-24 TD : *** DEPRECATED: this function shall not be called anymore! ***
# 2016-11-15 TD : process a download request of a notification list -- start --
def _download_request(repo_id=None, provider=False):
    """
    Process a download request, either against the full dataset or the specific repo_id supplied
    This function will pull the arguments it requires out of the Flask request object. 
    See the API documentation for the parameters of these kinds of requests.

    :param repo_id: the repo id to limit the request to
    :return: StringIO containing the list of notifications that are appropriate to the parameters
    """
    since = request.values.get("since")

    if since is None or since == "":
        return _bad_request("Missing required parameter 'since'")

    try:
        since = dates.reformat(since)
    except ValueError as e:
        return _bad_request("Unable to understand since date '{x}'".format(x=since))

    try:
        nbulk = JPER.bulk_notifications(current_user, since, repository_id=repo_id)
    except ParameterException as e:
        return _bad_request(str(e))

    return nbulk.json()


def _validate_since():
    since = request.values.get("since", None)
    if since is None or since == "":
        return _bad_request("Missing required parameter 'since'")

    try:
        since = dates.reformat(since)
    except ValueError:
        return _bad_request("Unable to understand since date '{x}'".format(x=since))

    return since


def _validate_page():
    page = request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1))
    try:
        page = int(page)
    except:
        return _bad_request("'page' parameter is not an integer")
    return page


def _validate_page_size():
    page_size = request.values.get("pageSize", app.config.get("DEFAULT_LIST_PAGE_SIZE", 25))
    try:
        page_size = int(page_size)
    except:
        return _bad_request("'pageSize' parameter is not an integer")
    return page_size


@blueprint.before_request
def restrict():
    if current_user.is_anonymous:
        if not request.path.endswith('login'):
            return redirect(request.path.rsplit('/', 1)[0] + '/login')


@blueprint.route('/')
def index():
    if not current_user.is_super:
        abort(401)
    users = [[i['_source']['id'], i['_source']['email'], i['_source'].get('role', [])] for i in
             models.Account().query(q='*', size=10000).get('hits', {}).get('hits', [])]
    return render_template('account/users.html', users=users)


# 2016-11-15 TD : enable download option ("csv", for a start...)
@blueprint.route('/download/<account_id>', methods=["GET", "POST"])
def download(account_id):
    acc = models.Account.pull(account_id)
    if acc is None:
        abort(404)

    provider = acc.has_role('publisher')
    data = None

    if provider:
        if request.args.get('rejected', False):
            fprefix = "failed"
            xtable = ftable
            html = _list_failrequest(provider_id=account_id, bulk=True)
        else:
            fprefix = "matched"
            xtable = mtable
            html = _list_matchrequest(repo_id=account_id, provider=provider, bulk=True)
    else:
        fprefix = "routed"
        xtable = ntable
        html = _list_request(repo_id=account_id, provider=provider, bulk=True)

    res = json.loads(html)

    rows = []
    for hdr in xtable["header"]:
        rows.append((m.value for m in parse(xtable[hdr]).find(res)), )

    rows = list(zip_longest(*rows, fillvalue=''))
    #
    # Python 3 you need to use StringIO with csv.write. send_file requires BytesIO, so you have to do both.
    strm = StringIO()
    writer = csv.writer(strm, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(xtable["header"])
    writer.writerows(rows)
    mem = BytesIO()
    mem.write(strm.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    strm.close()
    fname = "{z}_{y}_{x}.csv".format(z=fprefix, y=account_id, x=dates.now())
    return send_file(mem, as_attachment=True, attachment_filename=fname, mimetype='text/csv')


@blueprint.route('/details/<repo_id>', methods=["GET", "POST"])
def details(repo_id):
    acc = models.Account.pull(repo_id)
    if acc is None:
        abort(404)
    #
    provider = acc.has_role('publisher')
    if provider:
        data = _list_matchrequest(repo_id=repo_id, provider=provider)
    else:
        data = _list_request(repo_id=repo_id, provider=provider)
    #
    link = '/account/details'
    date = request.args.get('since')
    if date == '':
        date = '01/06/2019'
    if current_user.has_role('admin'):
        link += '/' + acc.id + '?since=' + date + '&api_key=' + current_user.data['api_key']
    else:
        link += '/' + acc.id + '?since=01/06/2019&api_key=' + acc.data['api_key']

    results = json.loads(data)

    page_num = int(request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1)))
    num_of_pages = int(math.ceil(results['total'] / results['pageSize']))
    if provider:
        return render_template('account/matching.html', repo=data, tabl=[json.dumps(mtable)],
                               num_of_pages=num_of_pages, page_num=page_num, link=link, date=date)
    return render_template('account/details.html', repo=data, tabl=[json.dumps(ntable)],
                           num_of_pages=num_of_pages, page_num=page_num, link=link, date=date)


# 2016-10-19 TD : restructure matching and(!!) failing history output (primarily for publishers) -- start --
@blueprint.route('/matching/<repo_id>', methods=["GET", "POST"])
def matching(repo_id):
    acc = models.Account.pull(repo_id)
    if acc is None:
        abort(404)
    #
    provider = acc.has_role('publisher')
    data = _list_matchrequest(repo_id=repo_id, provider=provider)
    #
    link = '/account/matching'
    date = request.args.get('since')
    if date == '':
        date = '01/06/2019'
    if current_user.has_role('admin'):
        link += '/' + acc.id + '?since=' + date + '&api_key=' + current_user.data['api_key']
    else:
        link += '/' + acc.id + '?since=01/06/2019&api_key=' + acc.data['api_key']

    results = json.loads(data)

    page_num = int(request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1)))
    num_of_pages = int(math.ceil(results['total'] / results['pageSize']))
    return render_template('account/matching.html', repo=data, tabl=[json.dumps(mtable)],
                           num_of_pages=num_of_pages, page_num=page_num, link=link, date=date)


@blueprint.route('/failing/<provider_id>', methods=["GET", "POST"])
def failing(provider_id):
    acc = models.Account.pull(provider_id)
    if acc is None:
        abort(404)
    #
    # provider = acc.has_role('publisher')
    # 2016-10-19 TD : not needed here for the time being
    data = _list_failrequest(provider_id=provider_id)
    #
    link = '/account/failing'
    date = request.args.get('since')
    if date == '':
        date = '01/06/2019'
    if current_user.has_role('admin'):
        link += '/' + acc.id + '?since=' + date + '&api_key=' + current_user.data['api_key']
    else:
        link += '/' + acc.id + '?since=01/06/2019&api_key=' + acc.data['api_key']

    results = json.loads(data)

    page_num = int(request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1)))
    num_of_pages = int(math.ceil(results['total'] / results['pageSize']))
    return render_template('account/failing.html', repo=data, tabl=[json.dumps(ftable)], num_of_pages=num_of_pages,
                           page_num=page_num, link=link, date=date)


@blueprint.route("/configview", methods=["GET", "POST"])
@blueprint.route("/configview/<repoid>", methods=["GET", "POST"])
def configView(repoid=None):
    app.logger.debug(current_user.id + " " + request.method + " to config route")
    if repoid is None:
        if current_user.has_role('repository'):
            repoid = current_user.id
        elif current_user.has_role('admin'):
            return ''  # the admin cannot do anything at /config, but gets a 200 so it is clear they are allowed
        else:
            abort(400)
    elif not current_user.has_role('admin'):  # only the superuser can set a repo id directly
        abort(401)
    rec = models.RepositoryConfig().pull_by_repo(repoid)
    if rec is None:
        rec = models.RepositoryConfig()
        rec.repo = repoid
        # rec.repository = repoid
        # 2016-09-16 TD : The field 'repository' has changed to 'repo' due to
        #                 a bug fix coming with a updated version ES 2.3.3 
    if request.method == 'GET':
        # get the config for the current user and return it
        # this route may not actually be needed, but is convenient during development
        # also it should be more than just the strings data once complex configs are accepted
        json_data = json.dumps(rec.data, ensure_ascii=False)
        return render_template('account/configview.html', repo=json_data)
    elif request.method == 'POST':
        if request.json:
            saved = rec.set_repo_config(jsoncontent=request.json, repository=repoid)
        else:
            try:
                if request.files['file'].filename.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=TextIOWrapper(request.files['file'], encoding='utf-8'),
                                                repository=repoid)
                elif request.files['file'].filename.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=TextIOWrapper(request.files['file'], encoding='utf-8'),
                                                repository=repoid)
            except:
                saved = False
        if saved:
            return ''
        else:
            abort(400)


@blueprint.route('/<username>', methods=['GET', 'POST', 'DELETE'])
def username(username):
    acc = models.Account.pull(username)

    if acc is None:
        abort(404)
    elif (request.method == 'DELETE' or
          (request.method == 'POST' and
           request.values.get('submit', '').split(' ')[0].lower() == 'delete')):
        if not current_user.is_super:
            abort(401)
        else:
            # 2017-03-03 TD : kill also any match configs if a repository is deleted ...
            repoconfig = None
            if acc.has_role('repository'):
                repoconfig = models.RepositoryConfig().pull_by_repo(acc.id)
                if repoconfig is not None:
                    repoconfig.delete()
            acc.remove()
            time.sleep(1)
            # 2017-03-03 TD : ... and be verbose about it!
            if repoconfig is not None:
                flash('Account ' + acc.id + ' and RepoConfig ' + repoconfig.id + ' deleted')
            else:
                flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))
    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)

        if request.values.get('email', False):
            acc.data['email'] = request.values['email']

        if 'password' in request.values and not request.values['password'].startswith('sha1'):
            if len(request.values['password']) < 8:
                flash("Sorry. Password must be at least eight characters long", "error")
                return render_template('account/user.html', account=acc)
            else:
                acc.set_password(request.values['password'])

        acc.save()
        time.sleep(2)
        flash("Record updated", "success")
        return render_template('account/user.html', account=acc)
    elif current_user.id == acc.id or current_user.is_super:
        if acc.has_role('repository'):
            repoconfig = models.RepositoryConfig.pull_by_repo(acc.id)
            licenses = get_matching_licenses(acc.id)
            license_ids = json.dumps([license['id'] for license in licenses])
        else:
            repoconfig = None
            licenses = None
            license_ids = None
        return render_template('account/user.html', account=acc, repoconfig=repoconfig, licenses=licenses,
                               license_ids=license_ids)
    else:
        abort(404)


@blueprint.route('/<username>/pubinfo', methods=['POST'])
def pubinfo(username):
    acc = models.Account.pull(username)
    if current_user.id != acc.id and not current_user.is_super:
        abort(401)

    if 'embargo' not in acc.data:
        acc.data['embargo'] = {}
    # 2016-07-12 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('embargo_form', False):
        if request.values.get('embargo_duration', False):
            acc.data['embargo']['duration'] = request.values['embargo_duration']
        else:
            acc.data['embargo']['duration'] = 0

    if 'license' not in acc.data:
        acc.data['license'] = {}
    # 2016-07-12 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('license_form', False):
        if request.values.get('license_title', False):
            acc.data['license']['title'] = request.values['license_title']
        else:
            acc.data['license']['title'] = ""
        if request.values.get('license_type', False):
            acc.data['license']['type'] = request.values['license_type']
        else:
            acc.data['license']['type'] = ""
        if request.values.get('license_url', False):
            acc.data['license']['url'] = request.values['license_url']
        else:
            acc.data['license']['url'] = ""
        if request.values.get('license_version', False):
            acc.data['license']['version'] = request.values['license_version']
        else:
            acc.data['license']['version'] = ""

    acc.save()
    time.sleep(2)
    flash('Thank you. Your publisher details have been updated.', "success")
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/repoinfo', methods=['POST'])
def repoinfo(username):
    acc = models.Account.pull(username)
    if current_user.id != acc.id and not current_user.is_super:
        abort(401)

    if 'repository' not in acc.data:
        acc.data['repository'] = {}
    # 2016-10-04 TD: proper handling of two independent forms using hidden input fields
    # if request.values.get('repo_profile_form',False):
    if request.values.get('repository_software', False):
        acc.data['repository']['software'] = request.values['repository_software']
    else:
        acc.data['repository']['software'] = ''
    if request.values.get('repository_url', False):
        acc.data['repository']['url'] = request.values['repository_url'].strip()
    else:
        acc.data['repository']['url'] = ''
    if request.values.get('repository_name', False):
        acc.data['repository']['name'] = request.values['repository_name']
    else:
        acc.data['repository']['name'] = ''
    if request.values.get('repository_sigel', False):
        acc.data['repository']['sigel'] = request.values['repository_sigel'].split(',')
    else:
        acc.data['repository']['sigel'] = []
    if request.values.get('repository_bibid', False):
        acc.data['repository']['bibid'] = request.values['repository_bibid'].strip().upper()
    else:
        acc.data['repository']['bibid'] = ''

    if 'sword' not in acc.data:
        acc.data['sword'] = {}
    # 2016-10-04 TD: proper handling of two independent forms using hidden input fields
    # if request.values.get('repo_sword_form',False):
    if request.values.get('sword_username', False):
        acc.data['sword']['username'] = request.values['sword_username']
    else:
        acc.data['sword']['username'] = ''
    if request.values.get('sword_password', False):
        acc.data['sword']['password'] = request.values['sword_password']
    else:
        acc.data['sword']['password'] = ''
    if request.values.get('sword_collection', False):
        acc.data['sword']['collection'] = request.values['sword_collection'].strip()
    else:
        acc.data['sword']['collection'] = ''

    if request.values.get('packaging', False):
        acc.data['packaging'] = [s.strip() for s in request.values['packaging'].split(',')]
    else:
        acc.data['packaging'] = []

    acc.save()
    time.sleep(2)
    flash('Thank you. Your repository details have been updated.', "success")
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/api_key', methods=['POST'])
def apikey(username):
    if current_user.id != username and not current_user.is_super:
        abort(401)
    acc = models.Account.pull(username)
    acc.api_key = str(uuid.uuid4())
    acc.save()
    time.sleep(2)
    flash('Thank you. Your API key has been updated.', "success")
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/config', methods=["GET", "POST"])
def config(username):
    if current_user.id != username and not current_user.is_super:
        abort(401)
    rec = models.RepositoryConfig().pull_by_repo(username)
    if rec is None:
        rec = models.RepositoryConfig()
        rec.repository = username
    if request.method == "GET":
        fprefix = "repoconfig"
        xtable = ctable
        res = {"repoconfig": [json.loads(rec.json())]}

        rows = []
        for hdr in xtable["header"]:
            rows.append((m.value for m in parse(xtable[hdr]).find(res)), )

        rows = list(zip_longest(*rows, fillvalue=''))

        # Python 3 you need to use StringIO with csv.write and send_file requires BytesIO, so you have to do both.
        strm = StringIO()
        writer = csv.writer(strm, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(xtable["header"])
        writer.writerows(rows)
        mem = BytesIO()
        mem.write(strm.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        strm.close()
        fname = "{z}_{y}_{x}.csv".format(z=fprefix, y=username, x=dates.now())
        return send_file(mem, as_attachment=True, attachment_filename=fname, mimetype='text/csv')

    elif request.method == "POST":
        try:
            saved = False
            if len(request.values.get('url', '')) > 1:
                url = request.values['url']
                fn = url.split('?')[0].split('#')[0].split('/')[-1]
                r = requests.get(url)
                try:
                    saved = rec.set_repo_config(jsoncontent=r.json(), repository=username)
                except:
                    strm = StringIO(r.text)
                    if fn.endswith('.csv'):
                        saved = rec.set_repo_config(csvfile=strm, repository=username)
                    elif fn.endswith('.txt'):
                        saved = rec.set_repo_config(textfile=strm, repository=username)
            else:
                if request.files['file'].filename.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=TextIOWrapper(request.files['file'], encoding='utf-8'),
                                                repository=username)
                elif request.files['file'].filename.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=TextIOWrapper(request.files['file'], encoding='utf-8'),
                                                repository=username)
            if saved:
                flash('Thank you. Your match config has been updated.', "success")
            else:
                flash('Sorry, there was an error with your config upload. Please try again.', "error")
        except Exception as e:
            flash('Sorry, there was an exception detected while your config upload was processed. Please try again.',
                  "error")
            app.logger.error(str(e))
        time.sleep(1)

    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/become/<role>', methods=['POST'])
@blueprint.route('/<username>/cease/<role>', methods=['POST'])
def changerole(username, role):
    acc = models.Account.pull(username)
    if acc is None:
        abort(404)
    elif request.method == 'POST' and current_user.is_super:
        if 'become' in request.path:
            if role == 'publisher':
                acc.become_publisher()
            elif role == 'active' and acc.has_role('repository'):
                acc.set_active()
                acc.save()
            elif role == 'passive' and acc.has_role('repository'):
                acc.set_passive()
                acc.save()
            else:
                acc.add_role(role)
                acc.save()
        elif 'cease' in request.path:
            if role == 'publisher':
                acc.cease_publisher()
            else:
                acc.remove_role(role)
                acc.save()
        time.sleep(1)
        flash("Record updated", "success")
        return redirect(url_for('.username', username=username))
    else:
        abort(401)


@blueprint.route('/<username>/matches')
def matches():
    return redirect(url_for('.username/match.html', username=username))


@blueprint.route('/<username>/excluded_license', methods=["POST"])
def excluded_license(username):
    if current_user.id != username and not current_user.is_super:
        abort(401)
    if request.method == "POST":
        included_licenses = request.form.getlist('excluded_license')
        license_ids = json.loads(request.form.get('license_ids'))
        excluded_licenses = [id for id in license_ids if id not in included_licenses]
        # acc = models.Account.pull(username)
        rec = models.RepositoryConfig.pull_by_repo(username)
        rec.excluded_license = excluded_licenses
        rec.save()
        time.sleep(1)
    return redirect(url_for('.username', username=username))


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('account/login.html')
    elif request.method == 'POST':
        password = request.values['password']
        username = request.values['username']
        user = models.Account.pull(username)
        if user is None:
            user = models.Account.pull_by_email(username)
        if user is not None and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back.', 'success')
            return redirect(url_for('.username', username=user.id))
        else:
            flash('Incorrect username/password, for reset please contact: info-deepgreen@zib.de', 'error')
            return render_template('account/login.html')


@blueprint.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect('/')


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if not current_user.is_super:
        abort(401)

    form = AdduserForm(request.form)
    vals = request.json if request.json else request.values

    if request.method == 'POST' and form.validate():
        role = vals.get('radio', None)
        account = models.Account()
        account.add_account(vals)
        account.save()
        if role == 'publisher':
            account.become_publisher()
        time.sleep(1)
        flash('Account created for ' + account.id, 'success')
        return redirect('/account')

    return render_template('account/register.html', vals=vals, form=form)
