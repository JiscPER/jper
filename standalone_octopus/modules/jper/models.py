from standalone_octopus.lib import dataobj

class NotificationMetadata(dataobj.DataObj):
    """
    {
        "metadata" : {
            "title" : "<publication title>",
            "journal" : "<journal title>",
            "volume" : "<volume (number) of the journal>",
            "issue" : "<issue (number) of the journal>",
            "fpage" : "<first page number of article>",
            "lpage" : "<last page number of article>",
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
    def __init__(self, raw=None, **kwargs):
        struct = {
            "objects" : [
                "metadata"
            ],
            "structs" : {
                "metadata" : {
                    "fields" : {
                        "title" : {"coerce" :"unicode"},
                        # 2020-02-11 TD : additional bibliographic items (to be in sync with jper)
                        "journal" : {"coerce" :"unicode"},
                        "volume" : {"coerce" :"unicode"},
                        "issue" : {"coerce" :"unicode"},
                        "fpage" : {"coerce" :"unicode"},
                        "lpage" : {"coerce" :"unicode"},
                        # 2020-02-11 TD : end of additional bibliographic items
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
                        "subject" : {"contains": "field", "coerce" : "unicode"}
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
                                "url" : {"coerce" : "unicode"},
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
        super(NotificationMetadata, self).__init__(raw, **kwargs)

    @property
    def title(self):
        return self._get_single("metadata.title", coerce=dataobj.to_unicode())

    @title.setter
    def title(self, val):
        self._set_single("metadata.title", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)

    #
    # 2020-02-10 TD : additional bibliographic fields ("@property" as well as "@...setter")
    #
    @property
    def journal(self):
        return self._get_single("metadata.journal", coerce=dataobj.to_unicode())

    @journal.setter
    def journal(self, val):
        self._set_single("metadata.journal", val, coerce=dataobj.to_unicode())

    @property
    def volume(self):
        return self._get_single("metadata.volume", coerce=dataobj.to_unicode())

    @volume.setter
    def volume(self, val):
        self._set_single("metadata.volume", val, coerce=dataobj.to_unicode())

    @property
    def issue(self):
        return self._get_single("metadata.issue", coerce=dataobj.to_unicode())

    @issue.setter
    def issue(self, val):
        self._set_single("metadata.issue", val, coerce=dataobj.to_unicode())

    @property
    def fpage(self):
        return self._get_single("metadata.fpage", coerce=dataobj.to_unicode())

    @fpage.setter
    def fpage(self, val):
        self._set_single("metadata.fpage", val, coerce=dataobj.to_unicode())

    @property
    def lpage(self):
        return self._get_single("metadata.lpage", coerce=dataobj.to_unicode())

    @lpage.setter
    def lpage(self, val):
        self._set_single("metadata.lpage", val, coerce=dataobj.to_unicode())
    #
    # 2020-02-11 TD : end of additional bibliographic fields
    #

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
    def source_name(self):
        return self._get_single("metadata.source.name", coerce=dataobj.to_unicode())

    @source_name.setter
    def source_name(self, val):
        self._set_single("metadata.source.name", val, coerce=dataobj.to_unicode())

    @property
    def source_identifiers(self):
        return self._get_list("metadata.source.identifier")

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
            for k in list(obj.keys()):
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
            for k in list(obj.keys()):
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
        for k in list(obj.keys()):
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

class IncomingNotification(NotificationMetadata):
    """
    {
        "event" : "<keyword for the kind of notification: acceptance, publication, etc.>",

        "provider" : {
            "agent" : "<string defining the software/process which put the content here, provided by provider - is this useful?>",
            "ref" : "<provider's globally unique reference for this research object>"
        },

        "content" : {
            "packaging_format" : "<identifier for packaging format used>"
        },

        "links" : [
            {
                "type" : "<link type: splash|fulltext>",
                "format" : "<text/html|application/pdf|application/xml|application/zip|...>",
                "url" : "<provider's splash, fulltext or machine readable page>"
            }
        ],

        "embargo" : {
            "end" : "<date embargo expires>",
            "start" : "<date embargo starts>",
            "duration" : "<number of months for embargo to run>"
        },

        "metadata" : {"<INHERITED from NotificationMetadata}
    }
    """

    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "event" : {"coerce" : "unicode"},
            },
            "objects" : [
                "provider", "content", "embargo"
            ],
            "lists" : {
                "links" : {"contains" : "object"}
            },
            "reqired" : [],

            "structs" : {
                "provider" : {
                    "fields" : {
                        "agent" : {"coerce" :"unicode"},
                        "ref" : {"coerce" :"unicode"}
                    },
                    "required" : []
                },
                "content" : {
                    "fields" : {
                        "packaging_format" : {"coerce" :"unicode"}
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
                        "url" : {"coerce" :"url"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(IncomingNotification, self).__init__(raw=raw)

    @property
    def packaging_format(self):
        return self._get_single("content.packaging_format", coerce=dataobj.to_unicode())

    @packaging_format.setter
    def packaging_format(self, val):
        self._set_single("content.packaging_format", val, coerce=dataobj.to_unicode())

class OutgoingNotification(NotificationMetadata):
    """
    {
        "id" : "<opaque identifier for this notification>",
        "created_date" : "<date this notification was received>",
        "analysis_date" : "<date the routing analysis was carried out>",

        "event" : "<keyword for the kind of notification: acceptance, publication, etc.>",

        "content" : {
            "packaging_format" : "<identifier for packaging format used>",
        },

        "links" : [
            {
                "type" : "<link type: splash|fulltext>",
                "format" : "<text/html|application/pdf|application/xml|application/zip|...>",
                "url" : "<provider's splash, fulltext or machine readable page>",
                "packaging" : "<package format identifier>"
            }
        ],

        "embargo" : {
            "end" : "<date embargo expires>",
            "start" : "<date embargo starts>",
            "duration" : "<number of months for embargo to run>"
        },

        "metadata" : {"<INHERITED from NotificationMetadata}
    }
    """
    def __init__(self, raw=None):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "utcdatetime"},
                "analysis_date" : {"coerce" : "utcdatetime"},
                "event" : {"coerce" : "unicode"},
            },
            "objects" : [
                "content", "embargo"
            ],
            "lists" : {
                "links" : {"contains" : "object"}
            },
            "reqired" : [],

            "structs" : {
                "content" : {
                    "fields" : {
                        "packaging_format" : {"coerce" :"unicode"}
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
                        "url" : {"coerce" :"url"},
                        "packaging" : {"coerce" : "unicode"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(OutgoingNotification, self).__init__(raw=raw, construct_silent_prune=True)

    @property
    def id(self):
        return self._get_single("id", coerce=dataobj.to_unicode())

    @property
    def created_datestamp(self):
        return self._get_single("created_date", coerce=dataobj.to_datestamp())

    @property
    def links(self):
        return self._get_list("links")

    def get_package_link(self, packaging):
        for l in self.links:
            if l.get("packaging") is not None and packaging == l.get("packaging"):
                return l
        return None

    def get_urls(self, type=None, format=None):
        urls = []
        for l in self.links:
            if type is not None and l.get("type") != type:
                continue
            if format is not None and l.get("format") != format:
                continue
            urls.append(l.get("url"))
        return urls

    @property
    def packaging_format(self):
        return self._get_single("content.packaging_format", dataobj.to_unicode())

    @property
    def analysis_date(self):
        return self._get_single("analysis_date", dataobj.date_str())

    @property
    def embargo_end(self):
        return self._get_single("embargo.end", dataobj.date_str())

class ProviderOutgoingNotification(OutgoingNotification):
    """
    In addition to OutgoingNotification...
    {
        "provider" : {
            "id" : "<user account id of the provider>",
            "agent" : "<string defining the software/process which put the content here, provided by provider - is this useful?>",
            "ref" : "<provider's globally unique reference for this research object>",
            "route" : "<method by which notification was received: native api, sword, ftp>"
        },
    }
    """
    def __init__(self, raw=None):
        struct = {
            "objects" : [
                "provider"
            ],
            "structs" : {
                "provider" : {
                    "fields" : {
                        "id" : {"coerce" :"unicode"},
                        "agent" : {"coerce" :"unicode"},
                        "ref" : {"coerce" :"unicode"},
                        "route" : {"coerce" :"unicode"}
                    },
                    "required" : []
                }
            }
        }

        self._add_struct(struct)
        super(ProviderOutgoingNotification, self).__init__(raw=raw)

class NotificationList(dataobj.DataObj):
    """
    {
        "since" : "<date from which results start in the form YYYY-MM-DDThh:mm:ssZ>",
        "page" : "<page number of results>,
        "pageSize" : "<number of results per page>,
        "timestamp" : "<timestamp of this request in the form YYYY-MM-DDThh:mm:ssZ>",
        "total" : "<total number of results at this time>",
        "notifications" : [
            "<ordered list of Outgoing Data Model JSON objects>"
        ]
    }
    """

    @property
    def since(self):
        return self._get_single("since", coerce=self._date_str())

    @since.setter
    def since(self, val):
        self._set_single("since", val, coerce=self._date_str())

    @property
    def page(self):
        return self._get_single("page", coerce=self._int())

    @page.setter
    def page(self, val):
        self._set_single("page", val, coerce=self._int())

    @property
    def page_size(self):
        return self._get_single("pageSize", coerce=self._int())

    @page_size.setter
    def page_size(self, val):
        self._set_single("pageSize", val, coerce=self._int())

    @property
    def timestamp(self):
        return self._get_single("timestamp", coerce=self._date_str())

    @timestamp.setter
    def timestamp(self, val):
        self._set_single("timestamp", val, coerce=self._date_str())

    @property
    def total(self):
        return self._get_single("total", coerce=self._int())

    @total.setter
    def total(self, val):
        self._set_single("total", val, coerce=self._int())

    @property
    def notifications(self):
        notes = self._get_list("notifications")
        if len(notes) > 0:
            if "provider" in notes[0]:
                return [ProviderOutgoingNotification(n) for n in self._get_list("notifications")]
            return [OutgoingNotification(n) for n in self._get_list("notifications")]
        return []

    @notifications.setter
    def notifications(self, val):
        self._set_list("notifications", val)
