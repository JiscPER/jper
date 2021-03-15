from datetime import datetime, timedelta
import uuid

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from standalone_octopus.core import app
from standalone_octopus.modules.account.authorise import Authorise
from standalone_octopus.modules.account import dao
from standalone_octopus.lib import dataobj

class BasicAccount(dataobj.DataObj, dao.BasicAccountDAO, UserMixin):
    """
    Most basic possible account, from which all other account objects must extend
    {
        "id" : "<unique user id>",
        "email" : "<user email address (which they will use to login)>",
        "password" : "<hashed password>",
        "role" : ["<user role>"],
        "reset_token" : "<password reset token>",
        "reset_expires" : "<password reset token expiration timestamp>",
        "activation_token" : "<account activation token>",
        "activation_expires" : "<account activation token expiration timestamp>",
        "created_date" : "<date account was created>",
        "last_updated" : "<date account was last modified>"
    }
    """

    @property
    def email(self):
        return self._get_single("email", coerce=self._utf8_unicode())

    @email.setter
    def email(self, val):
        self._set_single("email", val, coerce=self._utf8_unicode())

    @property
    def hashed_password(self):
        return self._get_single("password", coerce=self._utf8_unicode())

    @hashed_password.setter
    def hashed_password(self, val):
        self._set_single("password", val, coerce=self._utf8_unicode())

    def set_password(self, password):
        coerced = self._utf8_unicode()(password)
        self._set_single("password", generate_password_hash(coerced), coerce=self._utf8_unicode())

    def check_password(self, password):
        coerced = self._utf8_unicode()(password)
        existing = self.hashed_password
        if existing is None:
            return False
        return check_password_hash(existing, coerced)

    def clear_password(self):
        self._delete("password")

    @property
    def reset_token(self):
        return self._get_single("reset_token", coerce=self._utf8_unicode())

    def set_reset_token(self, token, timeout=None, expires=None):
        if expires is None and timeout is None:
            raise dataobj.DataSchemaException("You must provide a timeout or an expiry date for the reset token")
        if expires is None:
            expires = datetime.utcnow() + timedelta(0, timeout)
        if not isinstance(expires, str):
            expires = expires.strftime("%Y-%m-%dT%H:%M:%SZ")

        self._set_single("reset_token", token, coerce=self._utf8_unicode())
        self._set_single("reset_expires", expires, coerce=self._date_str())

    def remove_reset_token(self):
        self._delete("reset_token")
        self._delete("reset_expires")

    @property
    def reset_expires(self):
        return self._get_single("reset_expires", coerce=self._date_str())

    def is_reset_expired(self):
        if self.reset_expires is None:
            return True

        ed = datetime.strptime(self.reset_expires, "%Y-%m-%dT%H:%M:%SZ")
        if ed < datetime.utcnow():
            return True

        return False

    def activate_reset_mode(self):
        reset_token = uuid.uuid4().hex
        self.set_reset_token(reset_token, app.config.get("ACCOUNT_RESET_TIMEOUT", 86400))

    @property
    def activation_token(self):
        return self._get_single("activation_token", coerce=self._utf8_unicode())

    def set_activation_token(self, token, timeout=None, expires=None):
        if expires is None and timeout is None:
            raise dataobj.DataSchemaException("You must provide a timeout or an expiry date for the activation token")
        if expires is None:
            expires = datetime.utcnow() + timedelta(0, timeout)
        if not isinstance(expires, str):
            expires = expires.strftime("%Y-%m-%dT%H:%M:%SZ")

        self._set_single("activation_token", token, coerce=self._utf8_unicode())
        self._set_single("activation_expires", expires, coerce=self._date_str())

    def remove_activation_token(self):
        self._delete("activation_token")
        self._delete("activation_expires")

    @property
    def activation_expires(self):
        return self._get_single("activation_expires", coerce=self._date_str())

    def is_activation_expired(self):
        if self.activation_expires is None:
            return True

        ed = datetime.strptime(self.activation_expires, "%Y-%m-%dT%H:%M:%SZ")
        if ed < datetime.utcnow():
            return True

        return False

    def activate_activation_mode(self):
        activation_token = uuid.uuid4().hex
        self.set_activation_token(activation_token, app.config.get("ACCOUNT_ACTIVATE_TIMEOUT", 86400))

    @property
    def is_super(self):
        return Authorise.has_role(app.config["ACCOUNT_SUPER_USER_ROLE"], self.role)

    def has_role(self, role):
        return Authorise.has_role(role, self.role)

    @property
    def role(self):
        return self._get_list("role", coerce=self._utf8_unicode())

    def add_role(self, role):
        self._add_to_list("role", role, coerce=self._utf8_unicode())

    @role.setter
    def role(self, role):
        self._set_list("role", role, coerce=self._utf8_unicode())

    def can_log_in(self):
        return True

    def remove(self):
        self.delete()


class ContactableAccount(dataobj.DataObj):
    """
    Extension option for the basic account which adds key user contact details
    {
        "id" : "<user email address>",
        "name" : "<user's full name>",
        "loc" : {
            "lat" : <latitude>,
            "lon" : <longitude>
        },
        "phone" : "<user's preferred phone number>",
        "password" : "<hashed password>",
        "role" : ["<user role>"],
        "reset_token" : "<password reset token>",
        "reset_expires" : "<password reset token expiration timestamp>",
        "activation_token" : "<account activation token>",
        "activation_expires" : "<account activation token expiration timestamp>",
        "created_date" : "<date account was created>",
        "last_updated" : "<date account was last modified>"
    }
    """

    @property
    def name(self):
        return self._get_single("name", coerce=self._utf8_unicode())

    @name.setter
    def name(self, val):
        self._set_single("name", val, coerce=self._utf8_unicode(), ignore_none=True)

    @property
    def location(self):
        return (self.lat, self.lon)

    def set_location(self, lat, lon):
        self._set_single("loc.lat", lat, coerce=self._float())
        self._set_single("loc.lon", lon, coerce=self._float())

    @location.setter
    def location(self, val):
        if not isinstance(val, tuple):
            raise dataobj.DataSchemaException("location must be a tuple")
        if len(val) != 2:
            raise dataobj.DataSchemaException("location object must be a tuple of lat/lon only")
        self._set_single("loc.lat", val[0], coerce=self._float())
        self._set_single("loc.lon", val[1], coerce=self._float())

    @location.deleter
    def location(self):
        self._delete("loc.lat")
        self._delete("loc.lon")

    @property
    def lat(self):
        return self._get_single("loc.lat", coerce=self._float())

    @property
    def lon(self):
        return self._get_single("loc.lon", coerce=self._float())

    @property
    def phone(self):
        return self._get_single("phone", coerce=self._utf8_unicode())

    @phone.setter
    def phone(self, val):
        self._set_single("phone", val, coerce=self._utf8_unicode())

    @phone.deleter
    def phone(self):
        self._delete("phone")


class MonitoredAccount(dataobj.DataObj):
    """
    Extension for the basic account that adds delete/ban options
    {
        "id" : "<user email address>",
        "password" : "<hashed password>",
        "role" : ["<user role>"],
        "reset_token" : "<password reset token>",
        "reset_expires" : "<password reset token expiration timestamp>",
        "activation_token" : "<account activation token>",
        "activation_expires" : "<account activation token expiration timestamp>",
        "created_date" : "<date account was created>",
        "last_updated" : "<date account was last modified>",
        "admin" : {
            "deleted" : true|false,
            "banned" : true|false
        }
    }
    """

    @property
    def is_deleted(self):
        return self._get_single("admin.deleted", coerce=bool)

    def remove(self):
        self.set_deleted(True)

    def set_deleted(self, val):
        self._set_single("admin.deleted", val, coerce=bool)

    @property
    def is_banned(self):
        return self._get_single("admin.banned", coerce=bool)

    def set_banned(self, val):
        self._set_single("admin.banned", val, coerce=bool)

    def can_log_in(self):
        return not (self.is_deleted or self.is_banned)

