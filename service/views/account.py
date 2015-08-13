import uuid, json

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user

from service import models


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
            request.values.get('submit',False) == 'Delete' ) ):
        if not current_user.is_super:
            abort(401)
        else:
            acc.delete()
            flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))
    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
            
        if request.values.get('repository_name',False):
            account.data['repository'] = {
                'name': request.values['repository_name']
            }
            if request.values.get('repository_url',False): account.data['repository']['url'] = request.values['repository_url']
            
        if request.values.get('sword_username',False):
            account.data['sword'] = {
                'username': request.values['sword_username']
            }
            if request.values.get('sword_password',False): account.data['sword']['password'] = request.values['sword_password']
            if request.values.get('sword_collection',False): account.data['sword']['collection'] = request.values['sword_collection']

        if request.values.get('packaging',False):
            account.data['packaging'] = request.values['packaging'].split(',')

        if request.values.get('embargo_duration',False):
            account.data['embargo'] = {'duration': request.values['embargo_duration']}

        if 'password' in request.values and not request.values['password'].startswith('sha1'):
            if len(request.values['password']) < 8:
                flash("Sorry. Password must be at least eight characters long")
                return render_template('account/user.html', account=acc)
            else:
                acc.set_password(request.values['password'])
            
        acc.save()
        flash("Record updated")
        return render_template('account/user.html', account=acc)
    elif current_user.id == acc.id or current_user.is_super:
        return render_template('account/user.html', account=acc)
    else:
        abort(404)


@blueprint.route('/<username>/apikey', methods=['POST'])
def apikey(username,role):
    if current_user.id != acc.id and not current_user.is_super:
        abort(401)
    acc = models.Account.pull(username)
    acc.data['api_key'] = str(uuid.uuid4())
    acc.save()
    return acc.data['api_key']


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
        flash("Record updated")
        return render_template('account/user.html', account=acc)
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
			return redirect(url_for('.username', username))
		else:
			flash('Incorrect username/password', 'error')


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
        api_key = str(uuid.uuid4())
        account = models.Account(
            email = request.values['email'],
            api_key = api_key,
            role = []
        )
        
        if request.values.get('repository_name',False):
            account.data['repository'] = {
                'name': request.values['repository_name']
            }
            if request.values.get('repository_url',False): account.data['repository']['url'] = request.values['repository_url']
            
        if request.values.get('sword_username',False):
            account.data['sword'] = {
                'username': request.values['sword_username']
            }
            if request.values.get('sword_password',False): account.data['sword']['password'] = request.values['sword_password']
            if request.values.get('sword_collection',False): account.data['sword']['collection'] = request.values['sword_collection']

        if request.values.get('packaging',False):
            account.data['packaging'] = request.values['packaging'].split(',')

        if request.values.get('embargo_duration',False):
            account.data['embargo'] = {'duration': request.values['embargo_duration']}
        
        account.set_password(request.values['password'])
        if request.values.get('repository',False): role.push('repository')
        account.save()
        if request.values.get('publisher',False):
            account.become_publisher()
        flash('Account created for ' + account.id, 'success')
        return redirect('/account')

    
    