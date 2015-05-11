from octopus.lib import dataobj
from service import dao

class BaseNotification(dataobj.DataObj):
    """
    {
        "id" : "<opaque identifier for this notification>",
        "created_date" : "<date this notification was received>",

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
                "format" : "<html|pdf|xml>",
                "access" : "<type of access control on the resource: 'router' (reuqires router auth) or 'public' (no auth)>",
                "url" : "<provider's splash, fulltext or machine readable page>"
            }
        ],

        "embargo" : {
            "end" : "<date embargo expires>",
            "start" : "<date embargo starts>",
            "duration" : "<number of months for embargo to run>"
        },

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

    def __init__(self, raw):
        struct = {
            "fields" : {
                "id" : {"coerce" :"unicode"},
                "created_date" : {"coerce" : "utcdatetime"},
                "event" : {"coerce" : "unicode"},

            },
            "objects" : [
                "provider", "content", "embargo", "metadata"
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
                    "end" : {"coerce" : "utcdatetime"},
                    "start" : {"coerce" : "utcdatetime"},
                    "duration" : {"coerce" : "integer"}
                },
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
                        "subject" : {"coerce" : "unicode"}
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
                },
                "targets" : {
                    "fields" : {
                        "repository" : {"coerce" :"unicode"},
                        "requirement" : {"coerce" :"unicode"}
                    }
                },
                "links" : {
                    "fields" : {
                        "type" : {"coerce" :"unicode"},
                        "format" : {"coerce" :"unicode"},
                        "access" : {"coerce" :"unicode", "allowed" : ["router", "public"]},
                        "url" : {"coerce" :"url"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(BaseNotification, self).__init__(raw)

class RoutingInformation(dataobj.DataObj):
    """
    {
        "analysis_date" : "<date the routing analysis was carried out>",
        "repositories" : ["<ids of repository user accounts whcih match this notification>"]
    }
    """

    def __init__(self, raw):
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


class UnroutedNotification(BaseNotification, dao.UnroutedNotificationDAO):
    def __init__(self, raw=None):
        super(UnroutedNotification, self).__init__(raw=raw)

class RoutedNotification(BaseNotification, RoutingInformation, dao.RoutedNotificationDAO):
    def __init__(self, raw=None):
        super(RoutedNotification, self).__init__(raw=raw)

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
        "addresses" : ["<organisation addresses found in the data>"],
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
                "addresses" : {"contains" : "field", "coerce" : "unicode"},
                "keywords" : {"contains" : "field", "coerce" : "unicode"},
                "grants" : {"contains" : "field", "coerce" : "unicode"},
                "content_types" : {"contains" : "field", "coerce" : "unicode"}
            },
            "structs" : {
                "author_ids" : {
                    "fields" : {
                        "id" : {"coerce" : "unicode"},
                        "type" : {"coerce", "unicode"}
                    }
                }
            }
        }

        self._add_struct(struct)
        super(RoutingMetadata, self).__init__(raw=raw)