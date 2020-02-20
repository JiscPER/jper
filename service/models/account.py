
from flask.ext.login import UserMixin
from werkzeug import generate_password_hash, check_password_hash

from octopus.core import app
from service import dao
from octopus.lib import dataobj

class Account(dataobj.DataObj, dao.AccountDAO, UserMixin):
    '''
    {
        "id" : "<unique persistent account id>",
        "created_date" : "<date account created>",
        "last_updated" : "<date account last modified>",

        "email" : "<account contact email>",
        "contact_name" : "<name of key contact>",
        "password" : "<hashed password for ui login>",
        "api_key" : "<api key for api auth>",
        "role" : ["<account role: repository, publisher, admin, passive, active>"],

        "repository" : {
            "name" : "<name of the repository>",
            "url" : "<url for the repository>",
            "software" : "<name of the software>"
        },

        "publisher" : {
            "name" : "<name of the publisher>",
            "url" : "<url for the main publisher weg page>"
        },

        # "sword_repository" : {
        "sword" : {
            "username" : "<username for the router to authenticate with the repository>",
            "password" : "<reversibly encrypted password for the router to authenticate with the repository>",
            "collection" : "<url for deposit collection to receive content from the router>"
        },

        "packaging" : [
            "<identifier - in order of preference - that should be available for this repo.  Esp. via sword interface>"
        ],

        "embargo" : {
            "duration" : "<length of default embargo>",
            "from" : "<reference to field in data to measure embargo from>"
        },
        "license_ref" : {
            "title" : "<license title>",
            "type" : "<license type>",
            "url" : "<license url>",
            "version" : "<license version>"
        }
    }
    '''

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

    def set_api_key(self, key):
        self._set_single("api_key", key, coerce=dataobj.to_unicode())

    @property
    def is_passive(self):
        return self.has_role('passive')

    def set_active(self):
        if self.has_role('passive'):
            self.remove_role('passive') 
        # 2019-06-04 TD : no active support of role 'active' 
        #                 (so 'passive' will be more prominent on screen, for example) 
        # if not self.has_role('active'):
        #     self.add_role('active')

    def set_passive(self):
        if self.has_role('active'):
            self.remove_role('active') 
        if not self.has_role('passive'): 
            self.add_role('passive')

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

    def remove_role(self, role):
        self._delete_from_list("role", role)

    @role.setter
    def role(self, role):
        self._set_list("role", role, coerce=self._utf8_unicode())

    @property
    def packaging(self):
        return self._get_list("packaging", coerce=self._utf8_unicode())

    def add_packaging(self, val):
        self._add_to_list("packaging", val, coerce=self._utf8_unicode(), unique=True)

    # 2017-05-18 TD : fixed an unnoticed inconsistency up to now: change of "sword_repository" to "sword"
    # 
    def add_sword_credentials(self, username, password, collection):
        self._set_single("sword.username", username, coerce=self._utf8_unicode())
        self._set_single("sword.password", password, coerce=self._utf8_unicode())
        self._set_single("sword.collection", collection, coerce=self._utf8_unicode())

    # 2017-05-18 TD : fixed an unnoticed inconsistency up to now: change of "sword_repository" to "sword"
    # 
    @property
    def sword_collection(self):
        return self._get_single("sword.collection", coerce=self._utf8_unicode())

    # 2017-05-18 TD : fixed an unnoticed inconsistency up to now: change of "sword_repository" to "sword"
    # 
    @property
    def sword_username(self):
        return self._get_single("sword.username", coerce=self._utf8_unicode())

    # 2017-05-18 TD : fixed an unnoticed inconsistency up to now: change of "sword_repository" to "sword"
    # 
    @property
    def sword_password(self):
        return self._get_single("sword.password", coerce=self._utf8_unicode())

    @property
    def repository_software(self):
        return self._get_single("repository.software", coerce=self._utf8_unicode())

    @repository_software.setter
    def repository_software(self, val):
        self._set_single("repository.software", val, coerce=self._utf8_unicode())

    @property
    def repository_name(self):
        return self._get_single("repository.name", coerce=self._utf8_unicode())

    @repository_name.setter
    def repository_name(self, val):
        self._set_single("repository.name", val, coerce=self._utf8_unicode())

    # 2020-02-20 TD : add convenience setter and getter for extra pub infos
    @property
    def publisher_name(self):
        return self._get_single("publisher.name", coerce=self._utf8_unicode())

    @publisher_name.setter
    def publisher_name(self, val):
        self._set_single("publisher.name", val, coerce=self._utf8_unicode())

    @property
    def publisher_url(self):
        return self._get_single("publisher.url", coerce=self._utf8_unicode())

    @publisher_url.setter
    def publisher_url(self, val):
        self._set_single("publisher.url", val, coerce=self._utf8_unicode())
    # 2020-02-20 TD : end of convenience setter and getter for extra pub infos

    def can_log_in(self):
        return True

    # 2019-03-21 TD : Sometimes, ALL items of a 'key' are wanted ...
    @classmethod
    def pull_all_by_key(cls,key,value):
        res = cls.query(q={"query":{"query_string":{"query":value,"default_field":key,"default_operator":"AND"}}})
        n = res.get('hits',{}).get('total',0)
        # 2019-06-11 TD : re-query necessary as a precautionary measure because len(res) seems 
        #                 to be restricted to 10 records only per default...
        res = cls.query(q={"query":{"query_string":{"query":value,"default_field":key,"default_operator":"AND"}}},size=n)
        return [ cls.pull( res['hits']['hits'][k]['_source']['id'] ) for k in xrange(n) ]

    @classmethod
    def pull_all_by_email(cls,email):
        return cls.pull_all_by_key('email',email)
    # 2019-03-21 TD : (* end-of-addition *)

    @classmethod
    def pull_by_key(cls,key,value):
        res = cls.query(q={"query":{"query_string":{"query":value,"default_field":key,"default_operator":"AND"}}})
        if res.get('hits',{}).get('total',0) == 1:
            return cls.pull( res['hits']['hits'][0]['_source']['id'] )
        else:
            return None        

    @classmethod
    def pull_by_email(cls,email):
        return cls.pull_by_key('email',email)

    def remove(self):
        if self.has_role('publisher'):
            un = self.id
            try:
                import os, subprocess
                fl = os.path.dirname(os.path.abspath(__file__)) + '/deleteFTPuser.sh'
                subprocess.call(['sudo',fl,un])
                app.logger.info(str(self.id) + ' calling deleteFTPuser subprocess')
            except:
                app.logger.error(str(self.id) + ' failed deleteFTPuser subprocess')
        self.delete()

    def become_publisher(self):
        # create an FTP user for the account, if it is a publisher
        # TODO / NOTE: if the service has to be scaled up to run on multiple machines, 
        # the ftp users should only be created on the machine that the ftp address points to.
        # so the create user scripts should be triggered on that machine. Alternatively the user 
        # accounts could be created on every machine - but that leaves more potential security holes. 
        # Better to restrict the ftp upload to one machine that is configured to accept them. Then 
        # when it runs the schedule, it will check the ftp folder locations and send any to the API 
        # endpoints, so the heavy lifting would still be distributed across machines.
        #un = self.data['email'].replace('@','_')
        un = self.id
        try:
            import os, subprocess
            fl = os.path.dirname(os.path.abspath(__file__)) + '/createFTPuser.sh'
            print "subprocessing " + fl
            subprocess.call( [ 'sudo', fl, un, self.data['api_key'] ] )
            print "creating FTP user for " + un
        except:
            print "could not create an FTP user for " + un
        self.add_role('publisher')
        self.save()

    def cease_publisher(self):
        un = self.id
        try:
            import os, subprocess
            fl = os.path.dirname(os.path.abspath(__file__)) + '/deleteFTPuser.sh'
            print "subprocessing " + fl
            subprocess.call(['sudo',fl,un])
            print "deleting FTP user for " + un
        except:
            print "could not delete an FTP user for " + un
        self.remove_role('publisher')
        self.save()
        
        
