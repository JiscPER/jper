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


INCOMING = {
    "event" : "acceptance",

    "provider" : {
        "agent" : "pub/0.1",
        "ref" : "asdfasdf"
    },

    "content" : {
        "packaging_format" : "http://router.jisc.ac.uk/package/RouterNative"
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