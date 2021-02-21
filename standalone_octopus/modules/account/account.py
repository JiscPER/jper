from flask import Blueprint, request, url_for, flash, redirect
from flask import render_template, abort
from flask_login import login_user, logout_user, current_user, login_required

from standalone_octopus.core import app
from standalone_octopus.lib.webapp import ssl_required, is_safe_url
from standalone_octopus.modules.account.factory import AccountFactory
from standalone_octopus.modules.account import exceptions

blueprint = Blueprint('account', __name__)

@app.login_manager.user_loader
def load_account_for_login_manager(userid):
    from standalone_octopus.modules.account.factory import AccountFactory
    acc = AccountFactory.get_model().pull(userid)
    return acc

def get_redirect_target(form=None):
    form_target = ''
    if form and hasattr(form, 'next') and getattr(form, 'next'):
        form_target = form.next.data

    for target in form_target, request.args.get('next', []):
        if not target:
            continue
        if target == is_safe_url(target):
            return target
    return url_for(app.config.get("ACCOUNT_LOGIN_REDIRECT_ROUTE", "index"))


def _do_login(user):
    return login_user(user, remember=True)

def _do_logout():
    logout_user()

@blueprint.route('/login', methods=['GET', 'POST'])
@ssl_required
def login():
    # current_info = {'next': request.args.get('next', '')}
    fc = AccountFactory.get_login_formcontext(request.form)

    if request.method == 'POST':
        if fc.validate():
            password = fc.form.password.data
            email = fc.form.email.data

            Account = AccountFactory.get_model()
            try:
                user = Account.pull_by_email(email)
            except exceptions.NonUniqueAccountException:
                flash("Permanent Error: unable to log you in with these credentials - please contact an administrator", "error")
                return fc.render_template()

            if user is not None:
                if not user.can_log_in():
                    flash('Invalid credentials', 'error')
                    return fc.render_template()

                if user.check_password(password):
                    inlog = _do_login(user)
                    if not inlog:
                        flash("Problem logging in", "error")
                        return fc.render_template()
                    else:
                        flash('Welcome back.', 'success')
                        return redirect(get_redirect_target(form=fc.form))
                else:
                    flash('Incorrect username/password', 'error')
                    return fc.render_template()
            else:
                flash('Incorrect username/password', 'error')
                return fc.render_template()
        else:
            flash('Invalid credentials', 'error')

    return fc.render_template()

@blueprint.route('/logout')
@ssl_required
def logout():
    _do_logout()
    flash('You are now logged out', 'success')
    return redirect(url_for(app.config.get("ACCOUNT_LOGOUT_REDIRECT_ROUTE", "index")))

@blueprint.route('/<username>', methods=['GET', 'POST', 'DELETE'])
@login_required
@ssl_required
def username(username):
    Account = AccountFactory.get_model()
    acc = Account.pull(username)
    if acc is None:
        try:
            acc = Account.pull_by_email(username)
        except exceptions.NonUniqueAccountException:
            flash("Permanent Error: these user credentials are invalid - please contact an administrator", "error")
            return redirect(url_for(("logut")))

    if acc is None:
        abort(404)

    # actions on this page are only availble to the actual user, or a user with the edit-users role
    if current_user.id != acc.id or not current_user.has_role(app.config.get("ACCOUNT_EDIT_USERS_ROLE")):
        abort(401)

    # if this is a request for the user page, just render it
    if request.method == "GET":
        fc = AccountFactory.get_user_formcontext(acc)
        return fc.render_template()


    is_delete = request.method == "DELETE" or (request.method == "POST" and request.values.get("submit", False) == "Delete")
    if is_delete:
        # validate the delete
        if not current_user.check_password(request.values.get("password")):
            flash("Incorrect password", "error")
            fc = AccountFactory.get_user_formcontext(acc=acc)
            return fc.render_template()

        # if the password validates, go ahead and do it
        acc.remove()    # Note we don't use the DAO's delete method - this allows the model to decide the delete behaviour
        _do_logout()
        flash('Account {x} deleted'.format(x=username), "success")
        return redirect(url_for(app.config.get("ACCOUNT_LOGOUT_REDIRECT_ROUTE", "index")))

    if request.method == "POST":
        fc = AccountFactory.get_user_formcontext(acc=acc, form_data=request.form)

        # attempt to validate the form
        if not fc.validate():
            flash("There was a problem when submitting the form", "error")
            return fc.render_template()

        # if the form validates, then check the legality of the submission
        try:
            fc.legal()
        except exceptions.AccountException as e:
            flash(str(e), "error")
            return fc.render_template()

        # if we get to here, then update the user record
        fc.finalise()

        # tell the user that everything is good
        flash("Account updated", "success")

        # end with a redirect because some details have changed
        return redirect(url_for("account.username", username=fc.target.email))

@blueprint.route('/forgot', methods=['GET', 'POST'])
@ssl_required
def forgot():
    if request.method == "GET":
        fc = AccountFactory.get_forgot_formcontext()
        return fc.render_template()

    if request.method == 'POST':
        fc = AccountFactory.get_forgot_formcontext(form_data=request.form)

        # attempt to validate the form
        if not fc.validate():
            flash("There was a problem when submitting the form", "error")
            return fc.render_template()

        # call finalise on the context, to trigger the reset process
        try:
            fc.finalise()
        except exceptions.NonUniqueAccountException:
            flash("Permanent Error: cannot reset password for this account - please contact an administrator", "error")
            return fc.render_template()
        except exceptions.AccountNotFoundException:
            flash('Your account email address is not recognised.', 'error')
            return fc.render_template()
        except exceptions.AccountException:
            flash("Unable to reset the password for this account", "error")
            return fc.render_template()

        # if we get to here, reset was successful, so we should redirect the user
        return redirect(url_for(app.config.get("ACCOUNT_FORGOT_REDIRECT_ROUTE", "account.forgot_pending")))

@blueprint.route("/forgot-pending", methods=["GET"])
@ssl_required
def forgot_pending():
    return render_template("account/forgot_pending.html")


@blueprint.route("/reset/<reset_token>", methods=["GET", "POST"])
@ssl_required
def reset(reset_token):
    Account = AccountFactory.get_model()
    acc = Account.get_by_reset_token(reset_token)
    if acc is None:
        abort(404)

    if not acc.can_log_in():
        abort(404)

    if request.method == "GET":
        fc = AccountFactory.get_reset_formcontext(acc)
        return fc.render_template()

    elif request.method == "POST":
        fc = AccountFactory.get_reset_formcontext(acc, request.form)
        if not fc.validate():
            flash("There was a problem with your form", "error")
            return fc.render_template()

        # if the form is good, finalise the user's password change
        fc.finalise()

        # log the user in
        _do_login(acc)
        flash("Password has been reset and you have been logged in", "success")
        return redirect(url_for(app.config.get("ACCOUNT_LOGIN_REDIRECT_ROUTE", "index")))

@blueprint.route('/')
@login_required
@ssl_required
def index():
    if not app.config.get("ACCOUNT_LIST_USERS", False):
        abort(404)
    if not current_user.has_role(app.config.get("ACCOUNT_LIST_USERS_ROLE", "list_users")):
        abort(401)
    return render_template('account/users.html')

@blueprint.route('/register', methods=['GET', 'POST'])
@ssl_required
def register():
    # access to registration may not be for the public
    if current_user.is_anonymous and not app.config.get("ACCOUNT_ALLOW_REGISTER", False):
        abort(404)

    if request.method == "GET":
        fc = AccountFactory.get_register_formcontext()
        return fc.render_template()
    elif request.method == "POST":
        fc = AccountFactory.get_register_formcontext(request.form)

        if not fc.validate():
            flash("There was a problem with your form", "error")
            return fc.render_template()

        # if the form validates, then check the legality of the submission
        try:
            fc.legal()
        except exceptions.AccountException as e:
            flash(str(e), "error")
            return fc.render_template()

        # if we get to here, then create the user record
        fc.finalise()

        # tell the user that everything is good
        flash("Account created - activation token sent", "success")

        # redirect to the appropriate next page
        return redirect(url_for(app.config.get("ACCOUNT_REGISTER_REDIECT_ROUTE")))

@blueprint.route("/activate/<activation_token>", methods=["GET", "POST"])
@ssl_required
def activate(activation_token):
    account = AccountFactory.get_model().get_by_activation_token(activation_token)
    if account is None:
        abort(404)

    if not account.can_log_in():
        abort(404)

    if request.method == "GET":
        fc = AccountFactory.get_activate_formcontext(account)
        return fc.render_template()
    elif request.method == "POST":
        fc = AccountFactory.get_activate_formcontext(account, request.form)
        if not fc.validate():
            flash("There was a problem with your form", "error")
            return fc.render_template()

        # if the form is good, finalise the user's password change
        fc.finalise()

        # log the user in
        _do_login(account)
        flash("Your account has been activated and you have been logged in", "success")
        return redirect(url_for(app.config.get("ACCOUNT_LOGIN_REDIRECT_ROUTE", "index")))

