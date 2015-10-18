from octopus.lib import dataobj
from service import dao
from copy import deepcopy
from octopus.modules.identifiers import postcode
import requests, json
from octopus.core import app

class NotificationMetadata(dataobj.DataObj):
    """
    {
        "metadata" : {
            "title" : "<publication title>",
            "version" : "<version of the record, e.g. AAM>",
            "publisher" : "<publisher of the content>",
            "source" : {
                "name" : "<name of the journal or other source (e.g. book)>",
                "identifier" : [
                    {"type" : "issn", "id" : "<issn of the journal (could be print or electronic)>" },
                    {"type" : "eissn", "id" : "<electronic issn of the journal>" },
                    {"type" : "pissn", "id" : "<print issn of the journal>" },
                    {"type" : "doi", "id" : "<doi for the journal or series>" }
                ]
            },
            "identifier" : [
                {"type" : "doi", "id" : "<doi for the record>" }
            ],
            "type" : "publication/content type",
            "author" : [
                {
                    "name" : "<author name>",
                    "identifier" : [
                        {"type" : "orcid", "id" : "<author's orcid>"},
                        {"type" : "email", "id" : "<author's email address>"},
                    ],
                    "affiliation" : "<author affiliation>"
                }
            ],
            "language" : "<iso language code>",
            "publication_date" : "<publication date>",
            "date_accepted" : "<date accepted for publication>",
            "date_submitted" : "<date submitted for publication>",
            "license_ref" : {
                "title" : "<name of licence>",
                "type" : "<type>",
                "url" : "<url>",
                "version" : "<version>",
            },
            "project" : [
                {
                    "name" : "<name of funder>",
                    "identifier" : [
                        {"type" : "<identifier type>", "id" : "<funder identifier>"}
                    ],
                    "grant_number" : "<funder's grant number>"
                }
            ],
            "subject" : ["<subject keywords/classifications>"]
        }
    }
    """
    def __init__(self, raw=None):
        struct = {
            "objects" : [
                "metadata"
            ],
            "structs" : {
                "metadata" : {
                    "fields" : {
                        "title" : {"coerce" :"unicode"},
                        "version" : {"coerce" :"unicode"},
                        "publisher" : {"coerce" :"unicode"},
                        "type" : {"coerce" :"unicode"},
                        "language" : {"coerce" :"isolang"},
                        "publication_date" : {"coerce" :"utcdatetime"},
                        "date_accepted" : {"coerce" :"utcdatetime"},
                        "date_submitted" : {"coerce" :"utcdatetime"}
                    },
                    "objects" : [
                        "source", "license_ref"
                    ],
                    "lists" : {
                        "identifier" : {"contains" : "object"},
                        "author" : {"contains" : "object"},
                        "project" : {"contains" : "object"},
                        "subject" : {"contains" : "field", "coerce" : "unicode"}
                    },
                    "required" : [],

                    "structs" : {
                        "source" : {
                            "fields" : {
                                "name" : {"coerce" : "unicode"},
                            },
                            "lists" : {
                                "identifier" : {"contains" : "object"}
                            },
                            "structs" : {
                                "identifier" : {
                                    "fields" : {
                                        "type" : {"coerce" : "unicode"},
                                        "id" : {"coerce" : "unicode"}
                                    }
                                }
                            }
                        },
                        "license_ref" : {
                            "fields" : {
                                "title" : {"coerce" : "unicode"},
                                "type" : {"coerce" : "unicode"},
                                "url" : {"coerce" : "url"},
                                "version" : {"coerce" : "unicode"}
                            }
                        },
                        "identifier" : {
                            "fields" : {
                                "type" : {"coerce" : "unicode"},
                                "id" : {"coerce" : "unicode"}
                            }
                        },
                        "author" : {
                            "fields" : {
                                "name" : {"coerce" : "unicode"},
                                "affiliation" : {"coerce" : "unicode"},
                            },
                            "lists" : {
                                "identifier" : {"contains" : "object"}
                            },
                            "structs" : {
                                "identifier" : {
                                    "fields" : {
                                        "type" : {"coerce" : "unicode"},
                                        "id" : {"coerce" : "unicode"}
                                    }
                                }
                            }
                        },
                        "project" : {
                            "fields" : {
                                "name" : {"coerce" : "unicode"},
                                "grant_number" : {"coerce" : "unicode"},
                            },
                            "lists" : {
                                "identifier" : {"contains" : "object"}
                            },
                            "structs" : {
                                "identifier" : {
                                    "fields" : {
                                        "type" : {"coerce" : "unicode"},
                                        "id" : {"coerce" : "unicode"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        self._add_struct(struct)
        super(NotificationMetadata, self).__init__(raw)

    @property
    def title(self):
        return self._get_single("metadata.title", coerce=dataobj.to_unicode())

    @title.setter
    def title(self, val):
        self._set_single("metadata.title", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)

    @property
    def version(self):
        return self._get_single("metadata.version", coerce=dataobj.to_unicode())

    @version.setter
    def version(self, val):
        self._set_single("metadata.version", val, coerce=dataobj.to_unicode())

    @property
    def type(self):
        return self._get_single("metadata.type", coerce=dataobj.to_unicode())

    @type.setter
    def type(self, val):
        self._set_single("metadata.type", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)

    @property
    def publisher(self):
        return self._get_single("metadata.publisher", coerce=dataobj.to_unicode())

    @publisher.setter
    def publisher(self, val):
        self._set_single("metadata.publisher", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)

    @property
    def language(self):
        # Note that in this case we don't coerce to iso language, as it's a slightly costly operation, and all incoming
        # data should already be coerced
        return self._get_single("metadata.language", coerce=dataobj.to_unicode())

    @language.setter
    def language(self, val):
        self._set_single("metadata.language", val, coerce=dataobj.to_isolang(), allow_coerce_failure=True, allow_none=False, ignore_none=True)

    @property
    def publication_date(self):
        return self._get_single("metadata.publication_date", coerce=dataobj.date_str())

    @publication_date.setter
    def publication_date(self, val):
        self._set_single("metadata.publication_date", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)

    @property
    def date_accepted(self):
        return self._get_single("metadata.date_accepted", coerce=dataobj.date_str())

    @date_accepted.setter
    def date_accepted(self, val):
        self._set_single("metadata.date_accepted", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)

    @property
    def date_submitted(self):
        return self._get_single("metadata.date_submitted", coerce=dataobj.date_str())

    @date_submitted.setter
    def date_submitted(self, val):
        self._set_single("metadata.date_submitted", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)

    @property
    def identifiers(self):
        return self._get_list("metadata.identifier")

    def get_identifiers(self, type):
        ids = self._get_list("metadata.identifier")
        res = []
        for i in ids:
            if i.get("type") == type:
                res.append(i.get("id"))
        return res

    def add_identifier(self, id, type):
        if id is None or type is None:
            return
        uc = dataobj.to_unicode()
        obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
        self._delete_from_list("metadata.identifier", matchsub=obj, prune=False)
        self._add_to_list("metadata.identifier", obj)

    @property
    def authors(self):
        return self._get_list("metadata.author")

    @authors.setter
    def authors(self, objlist):
        # validate the object structure quickly
        allowed = ["name", "affiliation", "identifier"]
        for obj in objlist:
            for k in obj.keys():
                if k not in allowed:
                    raise dataobj.DataSchemaException("Author object must only contain the following keys: {x}".format(x=", ".join(allowed)))

            # coerce the values of some of the keys
            uc = dataobj.to_unicode()
            for k in ["name", "affiliation"]:
                if k in obj:
                    obj[k] = self._coerce(obj[k], uc)

        # finally write it
        self._set_list("metadata.author", objlist)

    def add_author(self, author_object):
        self._delete_from_list("metadata.author", matchsub=author_object)
        self._add_to_list("metadata.author", author_object)

    @property
    def projects(self):
        return self._get_list("metadata.project")

    @projects.setter
    def projects(self, objlist):
        # validate the object structure quickly
        allowed = ["name", "grant_number", "identifier"]
        for obj in objlist:
            for k in obj.keys():
                if k not in allowed:
                    raise dataobj.DataSchemaException("Project object must only contain the following keys: {x}".format(x=", ".join(allowed)))

            # coerce the values of some of the keys
            uc = dataobj.to_unicode()
            for k in ["name", "grant_number"]:
                if k in obj:
                    obj[k] = self._coerce(obj[k], uc)

        # finally write it
        self._set_list("metadata.project", objlist)

    def add_project(self, project_obj):
        self._delete_from_list("metadata.project", matchsub=project_obj)
        self._add_to_list("metadata.project", project_obj)

    @property
    def subjects(self):
        return self._get_list("metadata.subject")

    def add_subject(self, kw):
        self._add_to_list("metadata.subject", kw, coerce=dataobj.to_unicode(), unique=True)

    @property
    def license(self):
        return self._get_single("metadata.license_ref")

    @license.setter
    def license(self, obj):
        # validate the object structure quickly
        allowed = ["title", "type", "url", "version"]
        for k in obj.keys():
            if k not in allowed:
                raise dataobj.DataSchemaException("License object must only contain the following keys: {x}".format(x=", ".join(allowed)))

        # coerce the values of the keys
        uc = dataobj.to_unicode()
        for k in allowed:
            if k in obj:
                obj[k] = self._coerce(obj[k], uc)

        # finally write it
        self._set_single("metadata.license_ref", obj)

    def set_license(self, type, url):
        uc = dataobj.to_unicode()
        type = self._coerce(type, uc)
        url = self._coerce(url, uc)
        obj = {"title" : type, "type" : type, "url" : url}
        self._set_single("metadata.license_ref", obj)

    @property
    def source_name(self):
        return self._get_single("metadata.source.name", coerce=dataobj.to_unicode())

    @source_name.setter
    def source_name(self, val):
        self._set_single("metadata.source.name", val, coerce=dataobj.to_unicode())

    @property
    def source_identifiers(self):
        return self._get_list("metadata.source.identifier")

    def add_source_identifier(self, type, id):
        if id is None or type is None:
            return
        uc = dataobj.to_unicode()
        obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
        self._delete_from_list("metadata.source.identifier", matchsub=obj, prune=False)
        self._add_to_list("metadata.source.identifier", obj)


class BaseNotification(NotificationMetadata):
    """
    {
        "id" : "<opaque identifier for this notification>",
        "created_date" : "<date this notification was received>",
        "last_updated" : "<last modification time - required by storage layer>",

        "event" : "<keyword for the kind of notification: acceptance, publication, etc.>",

        "provider" : {
            "id" : "<user account id of the provider>",
            "agent" : "<string defining the software/process which put the content here, provided by provider - is this useful?>",
            "ref" : "<provider's globally unique reference for this research object>",
            "route" : "<method by which notification was received: native api, sword, ftp>"
        },

        "content" : {
            "packaging_format" : "<identifier for packaging format used>",
            "store_id" : "<information for retrieving the content from local store (tbc)>"
        },

        "links" : [
            {
                "type" : "<link type: splash|fulltext>",
                "format" : "<text/html|application/pdf|application/xml|application/zip|...>",
                "access" : "<type of access control on the resource: 'router' (reuqires router auth) or 'public' (no auth)>",
                "url" : "<provider's splash, fulltext or machine readable page>",
                "packaging" : "<packaging format identifier>",
                "proxy": "<the ID of the proxy link>"
            }
        ],

        "embargo" : {
            "end" : "<date embargo expires>",
            "start" : "<date embargo starts>",
            "duration" : "<number of months for embargo to run>"
        },

        "metadata" : {<INHERITED from NotificationMetadata>}
    }

    """

    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" :"unicode"},
                "created_date" : {"coerce" : "utcdatetime"},
                "last_updated" : {"coerce" : "utcdatetime"},
                "event" : {"coerce" : "unicode"}
            },
            "objects" : [
                "provider", "content", "embargo"
            ],
            "lists" : {
                "targets" : {"contains" : "object"},
                "links" : {"contains" : "object"}
            },
            "reqired" : [],

            "structs" : {
                "provider" : {
                    "fields" : {
                        "id" : {"coerce" :"unicode"},
                        "agent" : {"coerce" :"unicode"},
                        "ref" : {"coerce" :"unicode"},
                        "route" : {"coerce" :"unicode"}
                    },
                    "required" : []
                },
                "content" : {
                    "fields" : {
                        "packaging_format" : {"coerce" :"unicode"},
                        "store_id" : {"coerce" :"unicode"}
                    },
                    "required" : []
                },
                "embargo" : {
                    "fields" : {
                        "end" : {"coerce" : "utcdatetime"},
                        "start" : {"coerce" : "utcdatetime"},
                        "duration" : {"coerce" : "integer"}
                    }
                },
                "links" : {
                    "fields" : {
                        "type" : {"coerce" :"unicode"},
                        "format" : {"coerce" :"unicode"},
                        "access" : {"coerce" :"unicode", "allowed_values" : ["router", "public"]},
                        "url" : {"coerce" :"url"},
                        "packaging" : {"coerce" : "unicode"},
                        "proxy" : {"coerce" : "unicode"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(BaseNotification, self).__init__(raw)

    @property
    def packaging_format(self):
        return self._get_single("content.packaging_format", coerce=dataobj.to_unicode())

    @property
    def links(self):
        return self._get_list("links")

    def add_link(self, url, type, format, access, packaging=None):
        if access not in ["router", "public"]:
            raise dataobj.DataSchemaException("link access must be 'router' or 'public'")

        uc = dataobj.to_unicode()
        obj = {
            "url" : self._coerce(url, uc),
            "type" : self._coerce(type, uc),
            "format" : self._coerce(format, uc),
            "access" : self._coerce(access, uc)
        }
        if packaging is not None:
            obj["packaging"] = self._coerce(packaging, uc)
        self._add_to_list("links", obj)

    @property
    def provider_id(self):
        return self._get_single("provider.id", coerce=dataobj.to_unicode())

    @provider_id.setter
    def provider_id(self, val):
        self._set_single("provider.id", val, coerce=dataobj.to_unicode())

    def match_data(self):
        md = RoutingMetadata()

        # urls - we don't have a specific place to look for these, so we may choose to mine the
        # metadata for them later

        # authors, and all their various properties
        for a in self.authors:
            # name
            if "name" in a:
                md.add_author_id(a.get("name"), "name")

            # affiliation (and postcode)
            if "affiliation" in a:
                aff = a.get("affiliation")
                md.add_affiliation(aff)
                codes = postcode.extract_all(aff)
                for code in codes:
                    md.add_postcode(code)

            # other author ids
            for id in a.get("identifier", []):
                md.add_author_id(id.get("id"), id.get("type"))
                if id.get("type") == "email":
                    md.add_email(id.get("id"))

        # subjects
        for s in self.subjects:
            md.add_keyword(s)

        # grants
        for p in self.projects:
            if "grant_number" in p:
                md.add_grant_id(p.get("grant_number"))

        # content type
        if self.type is not None:
            md.add_content_type(self.type)

        return md

class RoutingInformation(dataobj.DataObj):
    """
    {
        "analysis_date" : "<date the routing analysis was carried out>",
        "repositories" : ["<ids of repository user accounts whcih match this notification>"]
    }
    """

    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "analysis_date" : {"coerce" : "utcdatetime"}
            },
            "lists" : {
                "repositories" : {"contains" : "field", "coerce" : "unicode"}
            }
        }

        self._add_struct(struct)
        super(RoutingInformation, self).__init__(raw)

    @property
    def analysis_date(self):
        return self._get_single("analysis_date", coerce=dataobj.date_str())

    @analysis_date.setter
    def analysis_date(self, val):
        self._set_single("analysis_date", val, coerce=dataobj.date_str())

    @property
    def analysis_datestamp(self):
        return self._get_single("analysis_date", coerce=dataobj.to_datestamp())

    @property
    def repositories(self):
        return self._get_list("repositories", coerce=dataobj.to_unicode())

    @repositories.setter
    def repositories(self, val):
        self._set_list("repositories", val, coerce=dataobj.to_unicode())


class UnroutedNotification(BaseNotification, dao.UnroutedNotificationDAO):
    def __init__(self, raw=None):
        super(UnroutedNotification, self).__init__(raw=raw)

    @classmethod
    def bulk_delete(cls,ids):
        data = ''
        for i in ids:
            data += json.dumps( {'delete':{'_id':i}} ) + '\n'
        r = requests.post(app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/unrouted/_bulk', data=data)
        return r.json()
        
    def make_routed(self):
        d = deepcopy(self.data)
        if "targets" in d:
            del d["targets"]
        routed = RoutedNotification(d)
        return routed

    def make_failed(self):
        d = deepcopy(self.data)
        routed = FailedNotification(d)
        return routed

    def make_outgoing(self, provider=False):
        d = deepcopy(self.data)
        if "last_updated" in d:
            del d["last_updated"]
        if not provider:
            if "provider" in d:
                del d["provider"]
        if "content" in d and "store_id" in d.get("content", {}):
            del d["content"]["store_id"]

        # filter out all non-router links if the request is not for the provider copy
        if "links" in d:
            keep = []
            for link in d.get("links", []):
                if provider:        # if you're the provider keep all the links
                    if "access" in link:
                        del link["access"]
                    keep.append(link)
                elif link.get("access") == "router":    # otherwise, only share router links
                    del link["access"]
                    keep.append(link)
            if len(keep) > 0:
                d["links"] = keep
            else:
                if "links" in d:
                    del d["links"]

        # delayed import required because of circular dependencies
        from service.models import OutgoingNotification, ProviderOutgoingNotification
        if not provider:
            return OutgoingNotification(d)
        else:
            return ProviderOutgoingNotification(d)

class RoutedNotification(BaseNotification, RoutingInformation, dao.RoutedNotificationDAO):
    def __init__(self, raw=None):
        super(RoutedNotification, self).__init__(raw=raw)

    def make_outgoing(self, provider=False):
        d = deepcopy(self.data)
        if "last_updated" in d:
            del d["last_updated"]
        if not provider:
            if "provider" in d:
                del d["provider"]
        if "content" in d and "store_id" in d.get("content", {}):
            del d["content"]["store_id"]
        if "repositories" in d:
            del d["repositories"]

        # filter out all non-router links if the request is not for the provider copy
        if "links" in d:
            keep = []
            for link in d.get("links", []):
                if provider:        # if you're the provider keep all the links
                    if "access" in link:
                        del link["access"]
                    keep.append(link)
                elif link.get("access") == "router":    # otherwise, only share router links
                    del link["access"]
                    keep.append(link)
            if len(keep) > 0:
                d["links"] = keep
            else:
                if "links" in d:
                    del d["links"]

        # delayed import required because of circular dependencies
        from service.models import OutgoingNotification, ProviderOutgoingNotification
        if not provider:
            return OutgoingNotification(d)
        else:
            return ProviderOutgoingNotification(d)

class FailedNotification(BaseNotification, RoutingInformation, dao.FailedNotificationDAO):
    def __init__(self, raw=None):
        super(FailedNotification, self).__init__(raw=raw)

class RoutingMetadata(dataobj.DataObj):
    """
    {
        "urls" : ["<list of affiliation urls found in the data>"],
        "emails" : ["<list of contact emails found in the data>"],
        "affiliations" : ["<names of organisations found in the data>"],
        "author_ids" : [
            {
                "id" : "<author id string>",
                "type" : "<author id type (e.g. orcid, or name)>"
            }
        ],
        "postcodes" : ["<organisation addresses found in the data>"],
        "keywords" : ["<keywords and subject classifications found in the data>"],
        "grants" : ["<grant names or numbers found in the data>"],
        "content_types" : ["<list of content types of the object (probably just one)>"]
    }
    """
    def __init__(self, raw=None):
        struct = {
            "lists" : {
                "urls" : {"contains" : "field", "coerce" : "unicode"},
                "emails" : {"contains" : "field", "coerce" : "unicode"},
                "affiliations" : {"contains" : "field", "coerce" : "unicode"},
                "author_ids" : {"contains" : "object"},
                "postcodes" : {"contains" : "field", "coerce" : "unicode"},
                "keywords" : {"contains" : "field", "coerce" : "unicode"},
                "grants" : {"contains" : "field", "coerce" : "unicode"},
                "content_types" : {"contains" : "field", "coerce" : "unicode"}
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
        super(RoutingMetadata, self).__init__(raw=raw)

    @property
    def urls(self):
        return self._get_list("urls", coerce=dataobj.to_unicode())

    @urls.setter
    def urls(self, val):
        self._set_list("urls", val, coerce=dataobj.to_unicode())

    def add_url(self, val):
        self._add_to_list("urls", val, coerce=dataobj.to_unicode(), unique=True)

    @property
    def author_ids(self):
        return self._get_list("author_ids")

    def add_author_id(self, id, type):
        uc = dataobj.to_unicode()
        obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
        self._delete_from_list("author_ids", matchsub=obj, prune=False)
        self._add_to_list("author_ids", obj)

    def get_author_ids(self, type=None):
        if type is None:
            return self.author_ids
        else:
            return [aid for aid in self._get_list("author_ids") if aid.get("type") == type]

    @property
    def affiliations(self):
        return self._get_list("affiliations", coerce=dataobj.to_unicode())

    def add_affiliation(self, aff):
        self._add_to_list("affiliations", aff, coerce=dataobj.to_unicode(), unique=True)

    @property
    def grants(self):
        return self._get_list("grants", coerce=dataobj.to_unicode())

    def add_grant_id(self, gid):
        self._add_to_list("grants", gid, coerce=dataobj.to_unicode(), unique=True)

    @property
    def keywords(self):
        return self._get_list("keywords", coerce=dataobj.to_unicode())

    @keywords.setter
    def keywords(self, val):
        self._set_list("keywords", val, coerce=dataobj.to_unicode())

    def add_keyword(self, kw):
        self._add_to_list("keywords", kw, coerce=dataobj.to_unicode(), unique=True)

    @property
    def emails(self):
        return self._get_list("emails", coerce=dataobj.to_unicode())

    def add_email(self, email):
        self._add_to_list("emails", email, coerce=dataobj.to_unicode(), unique=True)

    @property
    def content_types(self):
        return self._get_list("content_types", coerce=dataobj.to_unicode())

    def add_content_type(self, val):
        self._add_to_list("content_types", val, coerce=dataobj.to_unicode(), unique=True)

    @property
    def postcodes(self):
        return self._get_list("postcodes", coerce=dataobj.to_unicode())

    def add_postcode(self, val):
        self._add_to_list("postcodes", val, coerce=dataobj.to_unicode(), unique=True)

    def has_data(self):
        if len(self.data.keys()) == 0:
            return False
        for k, v in self.data.iteritems():
            if v is not None and len(v) > 0:
                return True
        return False

    def merge(self, other):
        for u in other.urls:
            self.add_url(u)
        for e in other.emails:
            self.add_email(e)
        for a in other.affiliations:
            self.add_affiliation(a)
        for aid in other.get_author_ids():
            self.add_author_id(aid.get("id"), aid.get("type"))
        for p in other.postcodes:
            self.add_postcode(p)
        for k in other.keywords:
            self.add_keyword(k)
        for g in other.grants:
            self.add_grant_id(g)
        for c in other.content_types:
            self.add_content_type(c)
