
from flask.ext.login import UserMixin
from werkzeug import generate_password_hash, check_password_hash

from octopus.core import app
from service import dao
from octopus.lib import dataobj

'''
{
    "id" : "<unique persistent account id>",
    "created_date" : "<date account created>",
    "last_updated" : "<date account last modified>",
    
    "email" : "<account contact email>",
    "contact_name" : "<name of key contact>",
    "password" : "<hashed password for ui login>",
    "api_key" : "<api key for api auth>",
    "role" : ["<account role: repository, provider, admin>"],
    
    "repository" : {
        "name" : "<name of the repository>",
        "url" : "<url for the repository>"
    },
    
    "sword_repository" : {
        "username" : "<username for the router to authenticate with the repository>",
        "password" : "<reversibly encrypted password for the router to authenticate with the repository>"
    },
    
    "embargo" : {
        "duration" : "<length of default embargo>",
        "from" : "<reference to field in data to measure embargo from>"
    }
}
'''

class Account(dataobj.DataObj, dao.AccountDAO, UserMixin):
	"""
	Most basic possible account, from which all other account objects must extend
	{
		"id" : "<unique user id>",
		"email" : "<user email address (which they will use to login)>",
		"password" : "<hashed password>",
		"role" : ["<user role>"],
		"created_date" : "<date account was created>",
		"last_updated" : "<date account was last modified>"
	}
	"""
	
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
	def is_super(self):
		return self.has_role(app.config["ACCOUNT_SUPER_USER_ROLE"])

	def has_role(self, role):
		return role in self.role

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


