from copy import deepcopy


class NotificationFactory(object):

    @classmethod
    def unrouted_notification(cls):
        return deepcopy(BASE_NOTIFICATION)

    @classmethod
    def routed_notification(cls):
        base = deepcopy(BASE_NOTIFICATION)
        base["links"].append(deepcopy(ROUTED_LINK))
        base.update(deepcopy(ROUTING_INFO))
        return base

    @classmethod
    def routing_metadata(cls):
        return deepcopy(ROUTING_METADATA)

    @classmethod
    def notification_metadata(cls):
        return deepcopy(ALT_METADATA)

ROUTING_METADATA = {
    "urls" : ["http://www.ed.ac.uk", "http://www.ucl.ac.uk"],
    "emails" : ["richard@example.com", "mark@example.com", "someone@sms.ucl.ac.uk"],
    "affiliations" : ["Cottage Labs", "Edinburgh Univerisity", "UCL"],
    "author_ids" : [
        {
            "id" : "Richard Jones",
            "type" : "name"
        },
        {
            "id" : "Mark MacGillivray",
            "type" : "name"
        },
        {
            "id" : "aaaa-0000-1111-bbbb",
            "type" : "orcid"
        },
        {
            "id" : "someone@sms.ucl.ac.uk",
            "type" : "email"
        }
    ],
    "postcodes" : ["SW1 0AA", "EH23 5TZ"],
    "keywords" : ["science", "technology", "arts", "medicine"],
    "grants" : ["BB/34/juwef"],
    "content_types" : ["article"]
}

ROUTED_LINK = {
    "type" : "fulltext",
    "format" : "application/zip",
    "access" : "router",
    "url" : "http://router.jisc.ac.uk/api/v1/notification/1234567890/content",
    "packaging" : "http://pubrouter.jisc.ac.uk/packages/FilesAndJATS"
}

ROUTING_INFO = {
    "analysis_date" : "2015-02-02T00:00:00Z",
    "repositories" : [
        "repo1", "repo2", "repo3"
    ]
}

ALT_METADATA = {
    "metadata" : {
        "title" : "Alternative Article",
        "version" : "AAM",
        "publisher" : "Other Publisher",
        "source" : {
            "name" : "Journal of Important Things",
            "identifier" : [
                {"type" : "other", "id" : "over there" }
            ]
        },
        "identifier" : [
            {"type" : "doi", "id" : "10.pp/jit.1" },
            {"type" : "url", "id" : "http://jit.com/1" }
        ],
        "type" : "paper",
        "author" : [
            {
                "name" : "Richard Jones",
                "identifier" : [
                    {"type" : "orcid", "id" : "aaaa-0000-1111-bbbb"},
                    {"type" : "email", "id" : "richard@example.com"},
                    {"type" : "mendeley_id", "id" : "12345"}
                ],
                "affiliation" : "Cottage Labs, HP3 9AA"
            },
            {
                "name" : "Dave Spiegel",
                "identifier" : [
                    {"type" : "email", "id" : "dave@example.com"},
                ],
                "affiliation" : "University of Life"
            }
        ],
        "language" : "eng",
        "publication_date" : "2015-01-01T00:00:00Z",
        "date_accepted" : "2014-09-01T00:00:00Z",
        "date_submitted" : "2014-07-03T00:00:00Z",
        "license_ref" : {
            "title" : "CC BY",
            "type" : "CC BY",
            "url" : "http://creativecommons.org/cc-by",
            "version" : "4.0",
        },
        "project" : [
            {
                "name" : "BBSRC",
                "identifier" : [
                    {"type" : "ringold", "id" : "bbsrcid"},
                    {"type" : "isni", "id" : "asdf-ghtk"}
                ],
                "grant_number" : "BB/34/juwef"
            },
            {
                "name" : "EPSRC",
                "identifier" : [
                    {"type" : "ringold", "id" : "askjdhfasdf"}
                ],
                "grant_number" : "EP/34/juwef"
            }
        ],
        "subject" : ["arts", "medicine", "literature"]
    }
}

BASE_NOTIFICATION = {
    "id" : "1234567890",
    "created_date" : "2015-02-02T00:00:00Z",

    "event" : "publication",

    "provider" : {
        "id" : "pub1",
        "agent" : "test/0.1",
        "ref" : "xyz",
        "route" : "api"
    },

    "content" : {
        "packaging_format" : "http://router.jisc.ac.uk/packages/FilesAndJATS",
        "store_id" : "abc"
    },

    "links" : [
        {
            "type" : "splash",
            "format" : "text/html",
            "access" : "public",
            "url" : "http://example.com/article/1"
        },
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "access" : "public",
            "url" : "http://example.com/article/1/pdf"
        }
    ],

    "embargo" : {
        "end" : "2016-01-01T00:00:00Z",
        "start" : "2015-01-01T00:00:00Z",
        "duration" : 12
    },

    "metadata" : {
        "title" : "Test Article",
        "version" : "AAM",
        "publisher" : "Premier Publisher",
        "source" : {
            "name" : "Journal of Important Things",
            "identifier" : [
                {"type" : "issn", "id" : "1234-5678" },
                {"type" : "eissn", "id" : "1234-5678" },
                {"type" : "pissn", "id" : "9876-5432" },
                {"type" : "doi", "id" : "10.pp/jit" }
            ]
        },
        "identifier" : [
            {"type" : "doi", "id" : "10.pp/jit.1" }
        ],
        "type" : "article",
        "author" : [
            {
                "name" : "Richard Jones",
                "identifier" : [
                    {"type" : "orcid", "id" : "aaaa-0000-1111-bbbb"},
                    {"type" : "email", "id" : "richard@example.com"},
                ],
                "affiliation" : "Cottage Labs, HP3 9AA"
            },
            {
                "name" : "Mark MacGillivray",
                "identifier" : [
                    {"type" : "orcid", "id" : "dddd-2222-3333-cccc"},
                    {"type" : "email", "id" : "mark@example.com"},
                ],
                "affiliation" : "Cottage Labs, EH9 5TP"
            }
        ],
        "language" : "eng",
        "publication_date" : "2015-01-01T00:00:00Z",
        "date_accepted" : "2014-09-01T00:00:00Z",
        "date_submitted" : "2014-07-03T00:00:00Z",
        "license_ref" : {
            "title" : "CC BY",
            "type" : "CC BY",
            "url" : "http://creativecommons.org/cc-by",
            "version" : "4.0",
        },
        "project" : [
            {
                "name" : "BBSRC",
                "identifier" : [
                    {"type" : "ringold", "id" : "bbsrcid"}
                ],
                "grant_number" : "BB/34/juwef"
            }
        ],
        "subject" : ["science", "technology", "arts", "medicine"]
    }
}