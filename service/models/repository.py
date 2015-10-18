from octopus.lib import dataobj
from service import dao
from octopus.core import app
import csv

class RepositoryConfig(dataobj.DataObj, dao.RepositoryConfigDAO):
    """
    {
        "id" : "<opaque id for repository config record>",
        "created_date" : "<date this notification was received>",
        "last_updated" : "<last modification time - required by storage layer>",

        "repository" : "<account id of repository that owns this configuration>",
        "domains" : ["<list of all domains that match this repository's institution>"],
        "name_variants" : ["<The names by which this repository's institution is known>"],
        "author_ids" : [
            {
                "id" : "<author id string>",
                "type" : "<author id type (e.g. orcid, or name)>"
            }
        ],
        "postcodes" : ["<list of postcodes that appear in the repository's institution's addresses>"],
        "keywords" : ["<keywords and subject classifications>"],
        "grants" : ["<grant names or numbers>"],
		"strings": ["<list of strings>"],
        "content_types" : ["<list of content types the repository is interested in>"]
    }
    """

    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repository" : {"coerce" : "unicode"}
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
        return self._get_single("repository", coerce=dataobj.to_unicode())

    @repository.setter
    def repository(self, val):
        self._set_single("repository", val, coerce=dataobj.to_unicode())

    @property
    def domains(self):
        return self._get_list("domains", coerce=dataobj.to_unicode())

    @property
    def name_variants(self):
        return self._get_list("name_variants", coerce=dataobj.to_unicode())

    @property
    def author_ids(self):
        return self._get_list("author_ids")

    @property
    def author_emails(self):
        # special function just to return the email type from the author ids
        return self.get_author_ids("email")

    def get_author_ids(self, type):
        aids = []
        for aid in self.author_ids:
            if aid.get("type") == type:
                aids.append(aid.get("id"))
        return aids

    @property
    def postcodes(self):
        return self._get_list("postcodes", coerce=dataobj.to_unicode())

    @property
    def keywords(self):
        return self._get_list("keywords", coerce=dataobj.to_unicode())

    @property
    def grants(self):
        return self._get_list("grants", coerce=dataobj.to_unicode())

    @property
    def content_types(self):
        return self._get_list("content_types", coerce=dataobj.to_unicode())

    @property
    def strings(self):
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
        return cls.pull_by_key('repository',repoid)
        
    def set_repo_config(self,csvfile=None,textfile=None,jsoncontent=None):
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
                    elif x.strip().lower().replace(' ','').replace('s','') == 'postcode' and len(row[x].strip()) > 1:
                        self.data['postcodes'] = self.data.get('postcodes',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'namevariant' and len(row[x].strip()) > 1:
                        self.data['name_variants'] = self.data.get('name_variants',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'domain' and len(row[x].strip()) > 1:
                        self.data['domains'] = self.data.get('domains',[]) + [row[x].strip()]
                    elif x.strip().lower().replace(' ','').replace('s','').replace('email','') == 'author' and len(row[x].strip()) > 1:
                        self.data['author_ids'] = self.data.get('author_ids',[]) + [{"type":"email","id":row[x].strip()}]
                    elif x.strip().lower().replace(' ','').replace('s','') == 'orcid' and len(row[x].strip()) > 1:
                        self.data['author_ids'] = self.data.get('author_ids',[]) + [{"type":"orcid","id":row[x].strip()}]
            app.logger.info("Extracted complex config from .csv file for repo: {x}".format(x=self.id))
            self.save()
            return True
        elif textfile is not None:
            app.logger.info("Extracted simple config from .txt file for repo: {x}".format(x=self.id))
            self.data['strings'] = [line.rstrip('\n').rstrip('\r').strip() for line in textfile if len(line.rstrip('\n').rstrip('\r').strip()) > 1]
            self.save()
            return True
        elif jsoncontent is not None:
            # save the lines into the repo config
            for k in jsoncontent.keys():
                self.data[k] = jsoncontent[k]
            self.save()
            app.logger.info("Saved config for repo: {x}".format(x=self.id))
            return True
        else:
            app.logger.info("Could not save config for repo: {x}".format(x=self.id))            
            return False
        


class MatchProvenance(dataobj.DataObj, dao.MatchProvenanceDAO):
    """
    {
        "id" : "<opaque id for repository config record>",
        "created_date" : "<date this notification was received>",
        "last_updated" : "<last modification time - required by storage layer>",

        "repository" : "<account id of repository to which the match pertains>",
        "notification" : "<id of the notification to which the match pertains>",
        "provenance" : [
            {
                "source_field" : "<field from the configuration that matched>",
                "term" : "<term from the configuration that matched>",
                "notification_field" : "<field from the notification that matched>"
                "matched" : "<text from the notification routing metadata that matched>",
                "explanation" : "<any additional explanatory text to go with this match (e.g. description of levenstein criteria)>"
            }
        ]
    }
    """

    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repository" : {"coerce" : "unicode"},
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
        return self._get_single("repository", coerce=dataobj.to_unicode())

    @repository.setter
    def repository(self, val):
        self._set_single("repository", val, coerce=dataobj.to_unicode())

    @property
    def notification(self):
        return self._get_single("notification", coerce=dataobj.to_unicode())

    @notification.setter
    def notification(self, val):
        self._set_single("notification", val, coerce=dataobj.to_unicode())

    @property
    def provenance(self):
        return self._get_list("provenance")

    def add_provenance(self, source_field, term, notification_field, matched, explanation):
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
    {
        "id" : "<opaque id for repository config record>",
        "created_date" : "<date this notification was received>",
        "last_updated" : "<last modification time - required by storage layer>",

        "repository" : "<user id of repository doing the retrieval>",
        "notification" : "<id of the notification retrieved>",
        "content" : "<the url or internal identifier of the content retrieved>",
        "retrieval_date" : "<date the repository retrieved the record>",
        "scope" : "<what the repository actually retrieved: notification, fulltext>"
    }
    """
    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "unicode"},
                "repository" : {"coerce" : "unicode"},
                "notification" : {"coerce" : "unicode"},
                "content" : {"coerce" : "unicode"},
                "retrieval_date" : {"coerce" : "utcdatetime"},
                "scope" : {"coerce" : "unicode", "allowed_values" : ["notification", "fulltext"]}
            }
        }

        self._add_struct(struct)
        super(RetrievalRecord, self).__init__(raw=raw)