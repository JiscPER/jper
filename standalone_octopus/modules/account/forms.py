from wtforms import Form, validators
from wtforms.fields import StringField, HiddenField, PasswordField
# from octopus.modules.form.validate import
from standalone_octopus.modules.form.context import FormContext, Renderer
from standalone_octopus.modules.account.factory import AccountFactory
from standalone_octopus.modules.account import exceptions
from flask_login import current_user
from flask import url_for, request
from standalone_octopus.core import app
from standalone_octopus.lib import mail

#####################################################################
## Login
#####################################################################

class LoginForm(Form):
    next = HiddenField()
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class LoginFormContext(FormContext):
    def set_template(self):
        self.template = "account/login.html"

    def make_renderer(self):
        self.renderer = LoginFormRenderer()

    def blank_form(self):
        self.form = LoginForm(csrf_enabled=False)

    def data2form(self):
        self.form = LoginForm(formdata=self.form_data, csrf_enabled=False)

    def finalise(self):
        super(LoginFormContext, self).finalise()

class LoginFormRenderer(Renderer):
    def __init__(self):
        super(LoginFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "login" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "next" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "email" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "password" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }

###########################################################

class BasicUserFormXwalk(object):
    @classmethod
    def obj2form(cls, acc):
        data = {}
        data["email"] = acc.email
        # Note that we don't crosswalk the password, as this is meaningless
        return data

    @classmethod
    def form2obj(cls, form, acc=None):
        if acc is None:
            klazz = AccountFactory.get_model()
            acc = klazz()
        else:
            acc = acc.clone()

        # update the email address
        if form.email.data:
            acc.email = form.email.data

        # if a new password has been provided, update it
        if form.new_password.data:
            acc.set_password(form.new_password.data)

        return acc

class BasicUserForm(Form):
    email = StringField("Email", [validators.DataRequired(), validators.Email()])

    new_password = PasswordField('New Password', [
        validators.Optional(),
        validators.EqualTo('confirm_new_password', message='Passwords must match')
    ])
    confirm_new_password = PasswordField('Repeat Password', [validators.Optional()])

    password = PasswordField("Current Password", [validators.DataRequired()])

class BasicUserFormContext(FormContext):
    def set_template(self):
        self.template = "account/user.html"

    def make_renderer(self):
        self.renderer = BasicUserFormRenderer()

    def blank_form(self):
        self.form = BasicUserForm()

    def data2form(self):
        self.form = BasicUserForm(formdata=self.form_data)

    def source2form(self):
        data = BasicUserFormXwalk.obj2form(self.source)
        self.form = BasicUserForm(data=data)

    def form2target(self):
        self.target = BasicUserFormXwalk.form2obj(self.form, self.source)

    def finalise(self):
        super(BasicUserFormContext, self).finalise()
        self.target.save(blocking=True)

    def render_template(self, template=None, **kwargs):
        return super(BasicUserFormContext, self).render_template(template=template, account=self.source, **kwargs)

    #####################################################
    ## user form extension to context

    def legal(self):
        # check the password and that the email is not already in use
        if not self._check_password():
            raise exceptions.IncorrectPasswordException("The password you provided was incorrect")

        if not self._check_email():
            raise exceptions.EmailInUseException("The email address you provided is in use by another user")

        return True

    def _check_password(self):
        # we check the password of the logged in user, not the account (this allows for admins to set user passwords)
        return current_user.check_password(self.form.password.data)

    def _check_email(self):
        suggested = self.form.email.data
        provided = self.source.email

        # if they have not changed their email, no need to look any further
        if suggested == provided:
            return True

        # otherwise we need to see if there's an email of this type already
        try:
            existing = AccountFactory.get_model().pull_by_email(suggested)
            return existing is None
        except exceptions.NonUniqueAccountException:
            return False

class BasicUserFormRenderer(Renderer):
    def __init__(self):
        super(BasicUserFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "details" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "email" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "new_password" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "confirm_new_password" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "password" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }

###################################################

class ForgotForm(Form):
    email = StringField("Email", [validators.DataRequired(), validators.Email()])

class ForgotFormContext(FormContext):
    def set_template(self):
        self.template = "account/forgot.html"

    def make_renderer(self):
        self.renderer = ForgotFormRenderer()

    def blank_form(self):
        self.form = ForgotForm()

    def data2form(self):
        self.form = ForgotForm(formdata=self.form_data)

    def finalise(self):
        super(ForgotFormContext, self).finalise()

        Account = AccountFactory.get_model()
        acc = Account.pull_by_email(self.form.email.data)
        if acc is None:
            raise exceptions.AccountNotFoundException("There is no user account with that email address")

        acc.activate_reset_mode()
        acc.save()

        self._send_reset_email(acc)

    def _send_reset_email(self, acc):
        base = request.url_root
        if base.endswith("/"):
            base = base[:-1]
        reset_url = base + url_for("account.reset", reset_token=acc.reset_token)

        to = [acc.email]
        fro = app.config.get('MAIL_FROM_ADDRESS')
        subject = app.config.get("ACCOUNT_RESET_EMAIL_SUBJECT", "(no subject)")

        try:
            mail.send_mail(to=to, fro=fro, subject=subject, template_name="account/emails/password_reset.txt", reset_url=reset_url, account=acc)
        except Exception as e:
            raise exceptions.EmailFailedException("Unable to send email to the address provided", e)

class ForgotFormRenderer(Renderer):
    def __init__(self):
        super(ForgotFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "email" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "email" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }

######################################################

class ResetForm(Form):
    new_password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_new_password', message='Passwords must match')
    ])
    confirm_new_password = PasswordField('Repeat Password', [validators.DataRequired()])

class ResetFormContext(FormContext):
    def set_template(self):
        self.template = "account/reset.html"

    def make_renderer(self):
        self.renderer = ResetFormRenderer()

    def blank_form(self):
        self.form = ResetForm()

    def data2form(self):
        self.form = ResetForm(formdata=self.form_data)

    def source2form(self):
        self.form = ResetForm()

    def finalise(self):
        super(ResetFormContext, self).finalise()

        password = self.form.new_password.data
        self.source.set_password(password)
        self.source.remove_reset_token()
        self.source.save(blocking=True)

    def render_template(self, template=None, **kwargs):
        return super(ResetFormContext, self).render_template(template=template, account=self.source, **kwargs)

class ResetFormRenderer(Renderer):
    def __init__(self):
        super(ResetFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "reset" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "new_password" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "confirm_new_password" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }

##############################################

class BasicRegisterFormXwalk(object):
    @classmethod
    def obj2form(cls, acc):
        data = {}
        data["email"] = acc.email
        # Note that we don't crosswalk the password, as this is meaningless
        return data

    @classmethod
    def form2obj(cls, form, acc=None):
        if acc is None:
            klazz = AccountFactory.get_model()
            acc = klazz()
        else:
            acc = acc.clone()

        # update the email address
        if form.email.data:
            acc.email = form.email.data

        # if a new password has been provided, update it
        if form.new_password.data:
            acc.set_password(form.new_password.data)

        return acc

class BasicRegisterForm(Form):
    email = StringField("Email", [validators.DataRequired(), validators.Email()])

class BasicRegisterFormContext(FormContext):
    def set_template(self):
        self.template = "account/register.html"

    def make_renderer(self):
        self.renderer = BasicRegisterFormRenderer()

    def blank_form(self):
        self.form = BasicRegisterForm()

    def data2form(self):
        self.form = BasicRegisterForm(formdata=self.form_data)

    def finalise(self):
        super(BasicRegisterFormContext, self).finalise()

        # handle the possibility that the account already exists
        existing = AccountFactory.get_model().pull_by_email(self.form.email.data)
        if existing is not None:
            if not existing.can_log_in():
                raise exceptions.CannotLoginException("This email address is currently not allowed to log in to the system")
        else:
            existing = AccountFactory.get_model()()

        # populate the account with the email address, and set the activation mode
        existing.email = self.form.email.data
        existing.role = app.config.get("ACCOUNT_DEFAULT_ROLES", [])
        existing.activate_activation_mode()
        existing.save(blocking=True)

        self._send_activation_email(existing)

    def _send_activation_email(self, acc):
        base = request.url_root
        if base.endswith("/"):
            base = base[:-1]
        activate_url = base + url_for("account.activate", activation_token=acc.activation_token)

        to = [acc.email]
        fro = app.config.get('MAIL_FROM_ADDRESS')
        subject = app.config.get("ACCOUNT_ACTIVATE_EMAIL_SUBJECT", "(no subject)")

        try:
            mail.send_mail(to=to, fro=fro, subject=subject, template_name="account/emails/activate.txt", activate_url=activate_url, account=acc)
        except Exception as e:
            raise exceptions.EmailFailedException("Unable to send email to the address provided", e)

    #####################################################
    ## register form extension to context

    def legal(self):
        if not self._check_email():
            raise exceptions.EmailInUseException("The email address you provided is in use by another user")

        return True

    def _check_email(self):
        suggested = self.form.email.data
        try:
            existing = AccountFactory.get_model().pull_by_email(suggested)
            return existing is None
        except exceptions.NonUniqueAccountException:
            return False

class BasicRegisterFormRenderer(Renderer):
    def __init__(self):
        super(BasicRegisterFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "register" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "email" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }

######################################################

class ActivateForm(Form):
    new_password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_new_password', message='Passwords must match')
    ])
    confirm_new_password = PasswordField('Repeat Password', [validators.DataRequired()])

class ActivateFormContext(FormContext):
    def set_template(self):
        self.template = "account/activate.html"

    def make_renderer(self):
        self.renderer = ActivateFormRenderer()

    def blank_form(self):
        self.form = ActivateForm()

    def data2form(self):
        self.form = ActivateForm(formdata=self.form_data)

    def source2form(self):
        self.form = ActivateForm()

    def finalise(self):
        super(ActivateFormContext, self).finalise()

        password = self.form.new_password.data
        self.source.set_password(password)
        self.source.remove_activation_token()
        self.source.save(blocking=True)

    def render_template(self, template=None, **kwargs):
        return super(ActivateFormContext, self).render_template(template=template, account=self.source, **kwargs)

class ActivateFormRenderer(Renderer):
    def __init__(self):
        super(ActivateFormRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "activate" : {
                "helper" : "bs3_horizontal",
                "wrappers" : ["first_error", "container"],
                "label_width" : 4,
                "control_width" : 8,
                "fields" : [
                    {
                        "new_password" : {
                            "attributes" : {}
                        }
                    },
                    {
                        "confirm_new_password" : {
                            "attributes" : {}
                        }
                    }
                ]
            }
        }