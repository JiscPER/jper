import uuid, json

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user
from flask_wtf import Form
from wtforms.fields import TextField, TextAreaField, SelectField, HiddenField, PasswordField
from wtforms import validators, ValidationError

from service import models


blueprint = Blueprint('account', __name__)


@blueprint.route('/')
def index():
	if not current_user.is_super:
		abort(401)
	users = models.Account.query() #{"sort":{'id':{'order':'asc'}}},size=1000000
	if users['hits']['total'] != 0:
		accs = [models.Account.pull(i['_source']['id']) for i in users['hits']['hits']]
		# explicitly mapped to ensure no leakage of sensitive data. augment as necessary
		users = []
		for acc in accs:
			user = {'id':acc.id}
			if 'created_date' in acc.data:
				user['created_date'] = acc.data['created_date']
				users.append(user)
	return render_template('account/users.html', users=users)


@blueprint.route('/<username>', methods=['GET','POST', 'DELETE'])
def username(username):
    acc = models.Account.pull(username)

    if acc is None:
        abort(404)
    elif ( request.method == 'DELETE' or 
            ( request.method == 'POST' and 
            request.values.get('submit',False) == 'Delete' ) ):
        if current_user.id != acc.id and not current_user.is_super:
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
            if k not in ['submit','password']:
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
		return render_template('account/login.html', form=form)
	elif request.method == 'POST':
		password = form.password.data
		username = form.username.data
		user = models.Account.pull(username)
		if user is None:
			user = models.Account.pull_by_email(username)
		if user is not None and user.check_password(password):
			login_user(user, remember=True)
			flash('Welcome back.', 'success')
			return form.redirect('index')
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
		return render_template('account/register.html', form=form)
	elif request.method == 'POST':
		api_key = str(uuid.uuid4())
		account = models.Account(
			id=form.w.data, 
			email=form.n.data,
			api_key=api_key
		)
		account.set_password(form.s.data)
		account.save()
		flash('Account created for ' + account.id + '. If not listed below, refresh the page to catch up.', 'success')
		return redirect('/account')
