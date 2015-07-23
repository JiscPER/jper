from copy import deepcopy


class RepositoryFactory(object):

    @classmethod
    def repo_config(cls):
        return deepcopy(REPO_CONFIG)

    @classmethod
    def match_provenance(cls):
        return deepcopy(MATCH_PROV)

    @classmethod
    def retreival_record(cls):
        return deepcopy(RETRIEVAL)

    @classmethod
    def useless_repo_config(cls):
        return deepcopy(USELESS_REPO_CONFIG)

RETRIEVAL = {
    "repository" : "abcdefg",
    "notification" : "1234567890",
    "content" : "http://example.com/file",
    "retrieval_date" : "2015-05-04T00:00:00Z",
    "scope" : "notification"
}

USELESS_REPO_CONFIG = {
    "repository" : "abcdefg",
    "domains" : ["someunknowndomain.withsubdomain.com"],
    "name_variants" : ["The Amazing University of Science, the Arts and Business (not to mention Medicine)"],
    "author_ids" : [],
    "postcodes" : [],
    "grants" : ["alkjsdfoiwqefwqefw"],
    "strings": []
}

REPO_CONFIG = {
    "repository" : "abcdefg",
    "domains" : ["ucl.ac.uk", "universitycollegelondon.ac.uk"],
    "name_variants" : ["UCL", "U.C.L", "University College"],
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
            "id" : "someone@sms.ucl.ac.uk",
            "type" : "email"
        }
    ],
    "postcodes" : ["SW1 0AA"],
    "keywords" : ["science", "technology", "medicine"],
    "grants" : ["BB/34/juwef"],
    "content_types" : ["article"],
    "strings" : [
        "https://www.ed.ac.uk/",
        "richard@EXAMPLE.com",
        "cottage labs",
        "AAAA-0000-1111-BBBB",
        "eh235tz",
        "bb/34/juwef"
    ]
}

MATCH_PROV = {
    "repository" : "abcdefg",
    "notification" : "1234567890",
    "provenance" : [
        {
            "source_field" : "postcode",
            "term" : "SW1 0AA",
            "notification_field" : "postcodes",
            "matched" : "SW1 0AA",
            "explanation" : "found matching postcodes"
        },
        {
            "source_field" : "author_ids",
            "term" : "Richard Jones",
            "notification_field" : "author_ids",
            "matched" : "Richard Jones",
            "explanation" : "author found in author list"
        }
    ]
}