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
	return render_template('account/users.html')


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
        newdata = request.json if request.json else request.values
        if newdata.get('id',False):
            if newdata['id'] != username:
                acc = models.Account.pull(newdata['id'])
            else:
                newdata['api_key'] = acc.data['api_key']
        for k, v in newdata.items():
            if k in ['publisher','repository']:
                if not current_user.is_super:
                    abort(401)
                else:
                    if v in [True,"yes",1,"1","True","true"]:
                        acc.data[k] = True
                    else:
                        acc.data[k] = False
            elif k not in ['submit','password']:
                acc.data[k] = v
        if 'password' in newdata and not newdata['password'].startswith('sha1'):
            acc.set_password(newdata['password'])
        acc.save()
        flash("Record updated")
        return render_template('account/user.html', account=acc)
    else:
        return render_template('account/user.html', account=acc)



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
			return render_template('account/login.html')
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
            publisher = True if request.values.get('publisher',False) else False,
            repository = True if request.values.get('repository',False) else False
        )
        account.set_password(request.values.password)
        if request.values.get('publisher',False):
            account.become_publisher()
        account.save()
        flash('Account created for ' + account.id, 'success')
        return redirect('/account')

    
    