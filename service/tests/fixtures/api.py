from copy import deepcopy
from octopus.lib import paths
import os

RESOURCES = paths.rel2abs(__file__, "..", "resources")



class APIFactory(object):

    @classmethod
    def incoming(cls):
        return deepcopy(INCOMING)

    @classmethod
    def example_package_path(cls):
        return os.path.join(RESOURCES, "example.zip")

    @classmethod
    def outgoing(cls, provider=False):
        if provider:
            return deepcopy(PROVIDER_OUTGOING)
        else:
            return deepcopy(OUTGOING)

    @classmethod
    def notification_list_set_get(cls):
        return deepcopy(NOTIFICATION_LIST_GET_SET)

NOTIFICATION_LIST_GET_SET = {
    "since" : ("2015-01-01", "2015-01-01T00:00:00Z"),
    "page" : ("2", 2),
    "page_size" : ("100", 100),
    "timestamp" : "2015-01-01T04:00:00Z",
    "total" : 3000,
    "notifications" : ["not a notification"]
}

OUTGOING = {

    "id" : "1234567890",
    "created_date" : "2015-02-02T00:00:00Z",
    "analysis_date" : "2015-02-02T00:00:00Z",

    "event" : "submission",

    "content" : {
        "packaging_format" : "http://router.jisc.ac.uk/packages/FilesAndJATS",
    },

    "links" : [
        {
            "type" : "splash",
            "format" : "text/html",
            "url" : "http://router.jisc.ac.uk/api/v1/notification/1234567890/content/1"
        },
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "url" : "http://router.jisc.ac.uk/api/v1/notification/1234567890/content/2"
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
                "affiliation" : "Cottage Labs"
            },
            {
                "name" : "Mark MacGillivray",
                "identifier" : [
                    {"type" : "orcid", "id" : "dddd-2222-3333-cccc"},
                    {"type" : "email", "id" : "mark@example.com"},
                ],
                "affiliation" : "Cottage Labs"
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

PROVIDER_OUTGOING = deepcopy(OUTGOING)
PROVIDER_OUTGOING.update({
    "provider" : {
        "id" : "pub1",
        "agent" : "test/0.1",
        "ref" : "xyz",
        "route" : "api"
    },
})

INCOMING = {
    "event" : "acceptance",

    "provider" : {
        "agent" : "pub/0.1",
        "ref" : "asdfasdf"
    },

    "content" : {
        "packaging_format" : "http://router.jisc.ac.uk/packages/FilesAndJATS"
    },

    "links" : [
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "url" : "http://example.com/pub/1/file.pdf"
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
                "affiliation" : "Cottage Labs"
            },
            {
                "name" : "Mark MacGillivray",
                "identifier" : [
                    {"type" : "orcid", "id" : "dddd-2222-3333-cccc"},
                    {"type" : "email", "id" : "mark@example.com"},
                ],
                "affiliation" : "Cottage Labs"
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