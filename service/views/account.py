"""
Blueprint for providing account management
"""
from __future__ import division
import uuid, json, time, requests, re

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from service.forms.adduser import AdduserForm
from flask.ext.login import login_user, logout_user, current_user
from octopus.core import app
from octopus.lib import webapp, dates
from service.api import JPER, ValidationException, ParameterException, UnauthorisedException
import pprint
import math


from service import models

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

blueprint = Blueprint('account', __name__)

# def _list_request(repo_id=None):
# 2016-09-07 TD : trial to include some kind of reporting for publishers here!
def _list_request(repo_id=None, provider=False):
    """
    Process a list request, either against the full dataset or the specific repo_id supplied
    This function will pull the arguments it requires out of the Flask request object.  See the API documentation
    for the parameters of these kinds of requests.

    :param repo_id: the repo id to limit the request to
    :param provider: (boolean) whether the repo_id belongs to a publisher or not
    :return: Flask response containing the list of notifications that are appropriate to the parameters
    """
    since = request.values.get("since")
    page = request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1))
    page_size = request.values.get("pageSize", app.config.get("DEFAULT_LIST_PAGE_SIZE", 25))

    if since is None or since == "":
        return _bad_request("Missing required parameter 'since'")

    try:
        since = dates.reformat(since)
    except ValueError as e:
        return _bad_request("Unable to understand since date '{x}'".format(x=since))

    try:
        page = int(page)
    except:
        return _bad_request("'page' parameter is not an integer")

    try:
        page_size = int(page_size)
    except:
        return _bad_request("'pageSize' parameter is not an integer")

    try:
        # nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id)
        # 2016-09-07 TD : trial to include some kind of reporting for publishers here!
        nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id, provider=provider)
    except ParameterException as e:
        return _bad_request(e.message)

    resp = make_response(nlist.json())
    resp.mimetype = "application/json"
    resp.status_code = 200
    return resp

@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        if not request.path.endswith('login'):
            return redirect(request.path.rsplit('/',1)[0] + '/login')


@blueprint.route('/')
def index():
    if not current_user.is_super:
        abort(401)
    ## users = [[i['_source']['id'],i['_source']['email'],i['_source'].get('role',[])] for i in models.Account().query(q='*',size=1000000).get('hits',{}).get('hits',[])]
    users = [[i['_source']['id'],i['_source']['email'],i['_source'].get('role',[])] for i in models.Account().query(q='*',size=1000).get('hits',{}).get('hits',[])]
    return render_template('account/users.html', users=users)

@blueprint.route('/details/<repo_id>', methods=["GET", "POST"])
def details(repo_id):
    # data = _list_request(repo_id)
    # 2016-09-07 TD : trial to include some kind of reporting for publishers here!
    acc = models.Account.pull(repo_id)
    #
    provider = acc.has_role('publisher')
    data = _list_request(repo_id=repo_id, provider=provider)
    #
    link = '/account/details'
    date = request.args.get('since')
    if date == '':
        date = '01/08/2015'
    if current_user.has_role('admin'): 
        link +='/' + acc.id + '?since='+date+'&api_key='+current_user.data['api_key']
    else:
        link += '?since=01/08/2015&api_key='+acc.data['api_key']
             
    results = json.loads(data.response[0])      
                        
    page_num =  int(request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1)))
    num_of_pages = int(math.ceil(results['total']/results['pageSize']))
    return render_template('account/details.html',repo=data.response, num_of_pages = num_of_pages, page_num = page_num, link = link,date=date)

@blueprint.route("/configview", methods=["GET","POST"])
@blueprint.route("/configview/<repoid>", methods=["GET","POST"])
def configView(repoid=None):
    app.logger.debug(current_user.id + " " + request.method + " to config route")
    if repoid is None:
        if current_user.has_role('repository'):
            repoid = current_user.id
        elif current_user.has_role('admin'):
            return '' # the admin cannot do anything at /config, but gets a 200 so it is clear they are allowed
        else:
            abort(400)
    elif not current_user.has_role('admin'): # only the superuser can set a repo id directly
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
        resp = make_response(json.dumps(rec.data))
        resp.mimetype = "application/json"
        return render_template('account/configview.html',repo=resp.response)
    elif request.method == 'POST':
        if request.json:
            saved = rec.set_repo_config(jsoncontent=request.json,repository=repoid)
        else:
            try:
                if request.files['file'].filename.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=request.files['file'],repository=repoid)
                elif request.files['file'].filename.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=request.files['file'],repository=repoid)
            except:
                saved = False
        if saved:
            return ''
        else:
            abort(400)


@blueprint.route('/<username>', methods=['GET','POST', 'DELETE'])
def username(username):
    acc = models.Account.pull(username)

    if acc is None:
        abort(404)
    elif ( request.method == 'DELETE' or 
            ( request.method == 'POST' and 
            request.values.get('submit','').split(' ')[0].lower() == 'delete' ) ):
        if not current_user.is_super:
            abort(401)
        else:
            acc.remove()
            time.sleep(1)
            flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))
    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
            
        if request.values.get('email',False):
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
            repoconfig = models.RepositoryConfig().pull_by_repo(acc.id)
        else:
            repoconfig = None
        return render_template('account/user.html', account=acc, repoconfig=repoconfig)
    else:
        abort(404)


@blueprint.route('/<username>/pubinfo', methods=['POST'])
def pubinfo(username):
    acc = models.Account.pull(username)
    if current_user.id != acc.id and not current_user.is_super:
        abort(401)

    if 'embargo' not in acc.data: acc.data['embargo'] = {}
    # 2016-07-12 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('embargo_form',False):
        if request.values.get('embargo_duration',False):
            acc.data['embargo']['duration'] = request.values['embargo_duration']
        else:
            acc.data['embargo']['duration'] = 0
             
    if 'license' not in acc.data: acc.data['license'] = {}
    # 2016-07-12 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('license_form',False):
        if request.values.get('license_title',False):
            acc.data['license']['title'] = request.values['license_title']
        else:
            acc.data['license']['title'] = ""
        if request.values.get('license_type',False):
            acc.data['license']['type'] = request.values['license_type']
        else:
            acc.data['license']['type'] = ""
        if request.values.get('license_url',False):
            acc.data['license']['url'] = request.values['license_url']
        else:
            acc.data['license']['url'] = ""
        if request.values.get('license_version',False):
            acc.data['license']['version'] = request.values['license_version']
        else:
            acc.data['license']['version'] = ""
        
    acc.save()
    time.sleep(2);
    flash('Thank you. Your publisher details have been updated.', "success")
    return redirect(url_for('.username', username=username))

        
@blueprint.route('/<username>/repoinfo', methods=['POST'])
def repoinfo(username):
    acc = models.Account.pull(username)
    if current_user.id != acc.id and not current_user.is_super:
        abort(401)

    if 'repository' not in acc.data: acc.data['repository'] = {}
    # 2016-10-04 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('repo_profile_form',False):
        if request.values.get('repository_software',False):
            acc.data['repository']['software'] = request.values['repository_software']
        else:
            acc.data['repository']['software'] = ''
        if request.values.get('repository_url',False):
            acc.data['repository']['url'] = request.values['repository_url']
        else:
            acc.data['repository']['url'] = ''
        if request.values.get('repository_name',False):
            acc.data['repository']['name'] = request.values['repository_name']
        else:
            acc.data['repository']['name'] = ''
        if request.values.get('repository_sigel',False):
            acc.data['repository']['sigel'] = request.values['repository_sigel'].split(',')
        else:
            acc.data['repository']['sigel'] = []
        if request.values.get('repository_bibid',False):
            acc.data['repository']['bibid'] = request.values['repository_bibid'].upper()
        else:
            acc.data['repository']['bibid'] = ''
        
    if 'sword' not in acc.data: acc.data['sword'] = {}
    # 2016-10-04 TD: proper handling of two independent forms using hidden input fields
    if request.values.get('repo_sword_form',False):
        if request.values.get('sword_username',False):
            acc.data['sword']['username'] = request.values['sword_username']
        else:
            acc.data['sword']['username'] = ''
        if request.values.get('sword_password',False):
            acc.data['sword']['password'] = request.values['sword_password']
        else:
            acc.data['sword']['password'] = ''
        if request.values.get('sword_collection',False):
            acc.data['sword']['collection'] = request.values['sword_collection']
        else:
            acc.data['sword']['collection'] = ''
        
        if request.values.get('packaging',False):
            acc.data['packaging'] = request.values['packaging'].split(',')
        else:
            acc.data['packaging'] = []

    acc.save()
    time.sleep(2);
    flash('Thank you. Your repository details have been updated.', "success")
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/api_key', methods=['POST'])
def apikey(username):
    if current_user.id != username and not current_user.is_super:
        abort(401)
    acc = models.Account.pull(username)
    acc.data['api_key'] = str(uuid.uuid4())
    acc.save()
    time.sleep(2);
    flash('Thank you. Your API key has been updated.', "success")
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/config', methods=['POST'])
def config(username):
    if current_user.id != username and not current_user.is_super:
        abort(401)
    rec = models.RepositoryConfig().pull_by_repo(username)
    if rec is None:
        rec = models.RepositoryConfig()
        rec.repository = username
    try:
        if len(request.values.get('url','')) > 1:
            url = request.values['url']
            fn = url.split('?')[0].split('#')[0].split('/')[-1]
            r = requests.get(url)
            try:
                saved = rec.set_repo_config(jsoncontent=r.json(),repository=username)
            except:
                strm = StringIO(r.content)
                if fn.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=strm,repository=username)
                elif fn.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=strm,repository=username)
        else:
            if request.files['file'].filename.endswith('.csv'):
                saved = rec.set_repo_config(csvfile=request.files['file'],repository=username)
            elif request.files['file'].filename.endswith('.txt'):
                saved = rec.set_repo_config(textfile=request.files['file'],repository=username)
        if saved:
            flash('Thank you. Your match config has been updated.', "success")        
        else:
            flash('Sorry, there was an error with your config upload. Please try again.', "error")        
    except:
        flash('Sorry, there was an error with your config upload. Please try again.', "error")
    time.sleep(1)
    return redirect(url_for('.username', username=username))


@blueprint.route('/<username>/become/<role>', methods=['POST'])
@blueprint.route('/<username>/cease/<role>', methods=['POST'])
def changerole(username,role):
    acc = models.Account.pull(username)
    if acc is None:
        abort(404)
    elif request.method == 'POST' and current_user.is_super:
        if 'become' in request.path:
            if role == 'publisher':
                acc.become_publisher()
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
            flash('Incorrect username/password, for reset please contact: info@deepgreen.de', 'error')
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
        #From here! 
        api_key = str(uuid.uuid4())
        account = models.Account()
        account.data['email'] = vals['email']
        account.data['api_key'] = api_key
        account.data['role'] = []
    
        if vals.get('repository_name',False):
            account.data['repository'] = {
                'name': vals['repository_name']
            }
            if vals.get('repository_software',False): account.data['repository']['software'] = vals['repository_software']
            if vals.get('repository_url',False): account.data['repository']['url'] = vals['repository_url']
            if vals.get('repository_bibid',False): account.data['repository']['bibid'] = vals['repository_bibid'].upper()
            if vals.get('repository_sigel',False): account.data['repository']['sigel'] = vals['repository_sigel'].split(',')
    
        if vals.get('sword_username',False):
            account.data['sword'] = {
                'username': vals['sword_username']
            }
            if vals.get('sword_password',False): account.data['sword']['password'] = vals['sword_password']
            if vals.get('sword_collection',False): account.data['sword']['collection'] = vals['sword_collection']
    
        if vals.get('packaging',False):
            account.data['packaging'] = vals['packaging'].split(',')
    
        if vals.get('embargo_duration',False):
            account.data['embargo'] = {'duration': vals['embargo_duration']}
    
        if vals.get('license_title',False):
            account.data['license'] = {'title': vals['license_title']}
            if vals.get('license_type',False):
                account.data['license']['type'] = vals['license_type']
            if vals.get('license_url',False):
                account.data['license']['url'] = vals['license_url']
            if vals.get('license_version',False):
                account.data['license']['version'] = vals['license_version']
    
        account.set_password(vals['password'])
        if vals['radio'] != 'publisher':
            account.add_role(vals['radio'])
        account.save()
        if vals['radio'] == 'publisher':
            account.become_publisher()
        #To here! it should be a method in model not part of the controller!
        time.sleep(1)
        flash('Account created for ' + account.id, 'success')
        return redirect('/account')
    
    return render_template('account/register.html', vals = vals, form = form)

    
