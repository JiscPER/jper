"""
Model objects used to represent interactions with repositories
"""

from octopus.lib import dataobj
from service import dao
from octopus.core import app
import csv

class RepositoryConfig(dataobj.DataObj, dao.RepositoryConfigDAO):
    """
    Class to represent the configuration information that repositories provide to the system
    to enable routing based on RoutingMetadata extracted from notifications

    See the core system model documentation for details on the JSON structure used by this model.
    """

    def __init__(self, raw=None):
        """
        Create a new instance of the RepositoryConfig object, optionally around the
        raw python dictionary.

        If supplied, the raw dictionary will be validated against the allowed structure of this
        object, and an exception will be raised if it does not validate

        :param raw: python dict object containing the data
        """
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repo" : {"coerce" : "unicode"}
                # "repository" : {"coerce" : "unicode"}
                # 2016-06-29 TD : index mapping exception fix for ES 2.3.3
            },
            "lists" : {
                "domains" : {"contains" : "field", "coerce" : "unicode"},
                "name_variants" : {"contains" : "field", "coerce" : "unicode"},
                "author_ids" : {"contains" : "object"},
                "postcodes" : {"contains" : "field", "coerce" : "unicode"},
                "keywords" : {"contains" : "field", "coerce" : "unicode"},
                "grants" : {"contains" : "field", "coerce" : "unicode"},
                "content_types" : {"contains" : "field", "coerce" : "unicode"},
                "strings" : {"contains" : "field", "coerce" : "unicode"}
            },
            "structs" : {
                "author_ids" : {
                    "fields" : {
                        "id" : {"coerce" : "unicode"},
                        "type" : {"coerce" : "unicode"}
                    }
                }
            }
        }
        self._add_struct(struct)
        super(RepositoryConfig, self).__init__(raw=raw)

    @property
    def repository(self):
        """
        Get the id of the repository this config represents

        :return: repository id
        """
        return self._get_single("repo", coerce=dataobj.to_unicode())
        # return self._get_single("repository", coerce=dataobj.to_unicode())
        # 2016-06-29 TD : index mapping exception fix for ES 2.3.3

    @repository.setter
    def repository(self, val):
        """
        Set the id of the repository this config represents

        :param val: the repository id
        """
        self._set_single("repo", val, coerce=dataobj.to_unicode())
        # self._set_single("repository", val, coerce=dataobj.to_unicode())
        # 2016-06-29 TD : index mapping exception fix for ES 2.3.3

    @property
    def domains(self):
        """
        List of domains that this repository is associated with

        :return: list of domains
        """
        return self._get_list("domains", coerce=dataobj.to_unicode())

    @property
    def name_variants(self):
        """
        List of name variants this repository/institution is known by

        :return: list of name variants
        """
        return self._get_list("name_variants", coerce=dataobj.to_unicode())

    @property
    def author_ids(self):
        """
        List of author id objects associated with this repository

        Author id objects are of the form:

        ::

            {
                "id" : "<author id string>",
                "type" : "<author id type (e.g. orcid, or name)>"
            }
        """
        return self._get_list("author_ids")

    @property
    def author_emails(self):
        """
        Get a list of email addresses for authors associated with the repository

        Short cut for self.get_author_ids("email")

        :return: list of email addresses
        """
        # special function just to return the email type from the author ids
        return self.get_author_ids("email")

    def get_author_ids(self, type):
        """
        List of author identifiers of the specified type

        :return: list of author identifiers as plain strings
        """
        aids = []
        for aid in self.author_ids:
            if aid.get("type") == type:
                aids.append(aid.get("id"))
        return aids

    @property
    def postcodes(self):
        """
        List of postcodes associated with this repository/institution

        :return: postcodes
        """
        return self._get_list("postcodes", coerce=dataobj.to_unicode())

    @property
    def keywords(self):
        """
        List of keywords associated with this repository

        :return: keywords
        """
        return self._get_list("keywords", coerce=dataobj.to_unicode())

    @property
    def grants(self):
        """
        List of grant codes associated with this repository/institution

        :return: grant codes
        """
        return self._get_list("grants", coerce=dataobj.to_unicode())

    @property
    def content_types(self):
        """
        List of content types associated with this repository

        :return: content types
        """
        return self._get_list("content_types", coerce=dataobj.to_unicode())

    @property
    def strings(self):
        """
        List of arbitrary strings which may be used to match against this repository

        :return: list of match strings
        """
        return self._get_list("strings", coerce=dataobj.to_unicode())

    @classmethod
    def pull_by_key(cls,key,value):
        res = cls.query(q={"query":{"term":{key+'.exact':value}}})
        if res.get('hits',{}).get('total',0) == 1:
            return cls.pull( res['hits']['hits'][0]['_source']['id'] )
        else:
            return None        

    @classmethod
    def pull_by_repo(cls,repoid):
        return cls.pull_by_key('repo',repoid)
        # return cls.pull_by_key('repository',repoid)
        # 2016-06-29 TD : index mapping exception fix for ES 2.3.3
        

    def set_repo_config(self,repository,csvfile=None,textfile=None,jsoncontent=None):
        repoid = repository
        # human readable fields are 'Domains','Name Variants','Author Emails','Postcodes','Grant Numbers','ORCIDs'
        fields = ['domains','name_variants','author_ids','postcodes','grants','keywords','content_types','strings']
        for f in fields:
            if f in self.data: del self.data[f]
        if csvfile is not None:
            # could do some checking of the obj
            lines = False
            inp = csv.DictReader(csvfile)
            for row in inp:
                for x in row.keys():
                    if x.strip().lower().replace(' ','').replace('s','').replace('number','') == 'grant' and len(row[x].strip()) > 1:
                        self.data['grants'] = self.data.get('grants',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').strip('s') == 'postcode' and len(row[x].strip()) > 1:
                        self.data['postcodes'] = self.data.get('postcodes',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'namevariant' and len(row[x].strip()) > 1:
                        self.data['name_variants'] = self.data.get('name_variants',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'domain' and len(row[x].strip()) > 1:
                        self.data['domains'] = self.data.get('domains',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','').replace('email','') == 'author' and len(row[x].strip()) > 1:
                        self.data['author_ids'] = self.data.get('author_ids',[]) + [{"type":"email","id":row[x].strip()}]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'orcid' and len(row[x].strip()) > 1:
                        self.data['author_ids'] = self.data.get('author_ids',[]) + [{"type":"orcid","id":row[x].strip()}]
            app.logger.debug("Extracted complex config from .csv file for repo: {x}".format(x=repoid))
            # app.logger.debug("Extracted complex config from .csv file for repo: {x}".format(x=self.id))
            self.data['repo'] = repoid
            # self.data['repository'] = repository
            # 2016-06-29 TD : index mapping exception fix for ES 2.3.3
            self.save()
            return True
        elif textfile is not None:
            app.logger.debug("Extracted simple config from .txt file for repo: {x}".format(x=repoid))
            # app.logger.debug("Extracted simple config from .txt file for repo: {x}".format(x=self.id))
            self.data['strings'] = [line.rstrip('\n').rstrip('\r').strip() for line in textfile if len(line.rstrip('\n').rstrip('\r').strip()) > 1]
            self.data['repo'] = repoid
            # self.data['repository'] = repository
            # 2016-06-29 TD : index mapping exception fix for ES 2.3.3
            self.save()
            return True
        elif jsoncontent is not None:
            # save the lines into the repo config
            for k in jsoncontent.keys():
                self.data[k] = jsoncontent[k]
            self.data['repo'] = repoid
            # self.data['repository'] = repository
            # 2016-06-29 TD : index mapping exception fix for ES 2.3.3
            self.save()
            app.logger.debug("Saved config for repo: {x}".format(x=repoid))
            # app.logger.debug("Saved config for repo: {x}".format(x=self.id))
            return True
        else:
            app.logger.error("Could not save config for repo: {x}".format(x=repoid))            
            # app.logger.error("Could not save config for repo: {x}".format(x=self.id))            
            return False
        


class MatchProvenance(dataobj.DataObj, dao.MatchProvenanceDAO):
    """
    Class to represent a record of a match between a RepositoryConfig and a RoutingMetadata object

    See the core system model documentation for details on the JSON structure used by this model.
    """

    def __init__(self, raw=None):
        """
        Create a new instance of the MatchProvenance object, optionally around the
        raw python dictionary.

        If supplied, the raw dictionary will be validated against the allowed structure of this
        object, and an exception will be raised if it does not validate

        :param raw: python dict object containing the metadata
        """
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repo" : {"coerce" : "unicode"},
                # "repository" : {"coerce" : "unicode"},
                # 2016-06-29 TD : index type 'match_prov' mapping exception fix for ES 2.3.3
                "notification" : {"coerce" : "unicode"}
            },
            "lists" : {
                "provenance" : {"contains" : "object"}
            },
            "structs" : {
                "provenance" : {
                    "fields" : {
                        "source_field" : {"coerce" : "unicode"},
                        "term" : {"coerce" : "unicode"},
                        "notification_field" : {"coerce" : "unicode"},
                        "matched" : {"coerce" : "unicode"},
                        "explanation" : {"coerce" : "unicode"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(MatchProvenance, self).__init__(raw=raw)

    @property
    def repository(self):
        """
        Repository id to which the match pertains

        :return: repository id
        """
        return self._get_single("repo", coerce=dataobj.to_unicode())
        # return self._get_single("repository", coerce=dataobj.to_unicode())
        # 2016-06-29 TD : index type 'match_prov' mapping exception fix for ES 2.3.3

    @repository.setter
    def repository(self, val):
        """
        Set the repository id to which the match pertains

        :param val: repository id
        """
        self._set_single("repo", val, coerce=dataobj.to_unicode())
        # self._set_single("repository", val, coerce=dataobj.to_unicode())
        # 2016-06-29 TD : index type 'match_prov' mapping exception fix for ES 2.3.3

    @property
    def notification(self):
        """
        Notification id to which the match pertains

        :return: notification id
        """
        return self._get_single("notification", coerce=dataobj.to_unicode())

    @notification.setter
    def notification(self, val):
        """
        Set the notification id to which the match pertains

        :param val: notification id
        """
        self._set_single("notification", val, coerce=dataobj.to_unicode())

    @property
    def provenance(self):
        """
        List of match provenance events for the combination of the repository id and notification id
        represented by this object

        Provenance records are of the following structure:

        ::

            {
                "source_field" : "<field from the configuration that matched>",
                "term" : "<term from the configuration that matched>",
                "notification_field" : "<field from the notification that matched>"
                "matched" : "<text from the notification routing metadata that matched>",
                "explanation" : "<any additional explanatory text to go with this match (e.g. description of levenstein criteria)>"
            }

        :return: list of provenance objects
        """
        return self._get_list("provenance")

    def add_provenance(self, source_field, term, notification_field, matched, explanation):
        """
        add a provenance record to the existing list of provenances

        :param source_field: the field from the repository configuration from which a match was drawn
        :param term: the text from the repository configuration which matched
        :param notification_field: the field from the notification that matched
        :param matched: the text from the notification that matched
        :param explanation: human readable description of the nature of the match
        """
        uc = dataobj.to_unicode()
        obj = {
            "source_field" : self._coerce(source_field, uc),
            "term" : self._coerce(term, uc),
            "notification_field" : self._coerce(notification_field, uc),
            "matched" : self._coerce(matched, uc),
            "explanation" : self._coerce(explanation, uc)
        }
        self._add_to_list("provenance", obj)

class RetrievalRecord(dataobj.DataObj, dao.RetrievalRecordDAO):
    """
    Class to allow us to record a retrieval of a file for the purposes of later reporting

    DO NOT USE.

    This class is not currently in use in the system, but may be activated later.  In the mean time,
    you should ignore it!
    """
    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repo" : {"coerce" : "unicode"},
                # "repository" : {"coerce" : "unicode"},
                # 2016-06-29 TD : index type 'retrieval'(???) mapping exception fix for ES 2.3.3
                "notification" : {"coerce" : "unicode"},
                "content" : {"coerce" : "unicode"},
                "retrieval_date" : {"coerce" : "utcdatetime"},
                "scope" : {"coerce" : "unicode", "allowed_values" : ["notification", "fulltext"]}
            }
        }

        self._add_struct(struct)
        super(RetrievalRecord, self).__init__(raw=raw)
