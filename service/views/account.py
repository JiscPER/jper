import uuid, json, time, requests

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user

from service import models

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

blueprint = Blueprint('account', __name__)


@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        if not request.path.endswith('login'):
            return redirect(request.path.rsplit('/',1)[0] + '/login')


@blueprint.route('/')
def index():
    if not current_user.is_super:
        abort(401)
    users = [[i['_source']['id'],i['_source']['email'],i['_source'].get('role',[])] for i in models.Account().query(q='*',size=1000000).get('hits',{}).get('hits',[])]
    return render_template('account/users.html', users=users)


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
            
        if request.values.get('repository_software',False):
            acc.data['repository'] = {
                'software': request.values['repository_software']
            }
            if request.values.get('repository_url',False): acc.data['repository']['url'] = request.values['repository_url']
            if request.values.get('repository_name',False): acc.data['repository']['name'] = request.values['repository_name']
            
        if request.values.get('sword_username',False):
            acc.data['sword'] = {
                'username': request.values['sword_username']
            }
            if request.values.get('sword_password',False): acc.data['sword']['password'] = request.values['sword_password']
            if request.values.get('sword_collection',False): acc.data['sword']['collection'] = request.values['sword_collection']

        if request.values.get('packaging',False):
            acc.data['packaging'] = request.values['packaging'].split(',')

        if request.values.get('embargo_duration',False):
            acc.data['embargo'] = {'duration': request.values['embargo_duration']}

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
    if 1==1:
        if len(request.values.get('url','')) > 1:
            url = request.values['url']
            fn = url.split('?')[0].split('#')[0].split('/')[-1]
            r = requests.get(url)
            if fn.endswith('.json'):
                saved = rec.set_repo_config(jsoncontent=r.json())
            else:
                strm = StringIO(r.content)
                if fn.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=strm)
                elif fn.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=strm)
        else:
            if request.files['file'].filename.endswith('.csv'):
                saved = rec.set_repo_config(csvfile=request.files['file'])
            elif request.files['file'].filename.endswith('.txt'):
                saved = rec.set_repo_config(textfile=request.files['file'])
        if saved:
            flash('Thank you. Your match config has been updated.', "success")        
        else:
            flash('Sorry, there was an error with your config upload. Please try again.', "error")        
    else:
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
            return redirect(url_for('.username', username=username))
        else:
            flash('Incorrect username/password', 'error')
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
    elif request.method == 'GET':
        return render_template('account/register.html')
    elif request.method == 'POST':
        vals = request.json if request.json else request.values
        if 'email' not in vals:
            flash('You must provide an email address','error')
            return render_template('account/register.html')
        elif models.Account.pull_by_email(vals['email']) is not None:
            flash('An account already exists for that email address')
            return render_template('account/register.html')
        else:
            api_key = str(uuid.uuid4())
            account = models.Account()
            account.data['email'] = vals['email']
            account.data['api_key'] = api_key
            account.data['role'] = []

            if vals.get('repository_software',False):
                account.data['repository'] = {
                    'software': vals['repository_software']
                }
                if vals.get('repository_url',False): account.data['repository']['url'] = vals['repository_url']
                if vals.get('repository_name',False): account.data['repository']['name'] = vals['repository_name']

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

            account.set_password(vals['password'])
            if vals.get('repository',False):
                account.add_role('repository')
            account.save()
            if vals.get('publisher',False):
                account.become_publisher()
            time.sleep(1)
            flash('Account created for ' + account.id, 'success')
            return redirect('/account')


    