from standalone_octopus.core import app
from standalone_octopus.lib import plugin

class AccountFactory(object):

    @classmethod
    def get_model(cls):
        path = app.config.get("ACCOUNT_MODEL")
        klazz = plugin.load_class(path)
        return klazz

    @classmethod
    def get_user_formcontext(cls, acc=None, form_data=None):
        path = app.config.get("ACCOUNT_USER_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data, acc)
        return fc

    @classmethod
    def get_login_formcontext(cls, form_data=None):
        path = app.config.get("ACCOUNT_LOGIN_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data)
        return fc

    @classmethod
    def get_forgot_formcontext(cls, form_data=None):
        path = app.config.get("ACCOUNT_FORGOT_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data)
        return fc

    @classmethod
    def get_reset_formcontext(cls, acc=None, form_data=None):
        path = app.config.get("ACCOUNT_RESET_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data, acc)
        return fc

    @classmethod
    def get_register_formcontext(cls, form_data=None):
        path = app.config.get("ACCOUNT_REGISTER_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data)
        return fc

    @classmethod
    def get_activate_formcontext(cls, acc=None, form_data=None):
        path = app.config.get("ACCOUNT_ACTIVATE_FORM_CONTEXT")
        klazz = plugin.load_class(path)
        fc = klazz(form_data, acc)
        return fc