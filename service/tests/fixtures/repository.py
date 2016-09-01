"""
Fixtures for testing repository features
"""

from copy import deepcopy

class RepositoryFactory(object):
    """
    Class for providing access to fixtures for testing repository features
    """

    @classmethod
    def repo_config(cls):
        """
        Example repository config

        :return: repository config
        """
        return deepcopy(REPO_CONFIG)

    @classmethod
    def match_provenance(cls):
        """
        Example match provenance

        :return: match provenance
        """
        return deepcopy(MATCH_PROV)

    @classmethod
    def retrieval_record(cls):
        """
        Example retrieval record

        :return: retrieval record
        """
        return deepcopy(RETRIEVAL)

    @classmethod
    def useless_repo_config(cls):
        """
        Repository config which doesn't contain any useful data (but does contain data)

        :return: repo config
        """
        return deepcopy(USELESS_REPO_CONFIG)

RETRIEVAL = {
    # "repository" : "abcdefg",
    "repo" : "abcdefg",
    "notification" : "1234567890",
    "payload" : "http://example.com/file",
    "retrieval_date" : "2015-05-04T00:00:00Z",
    "scope" : "notification"
}
"""Example retrieval record"""

USELESS_REPO_CONFIG = {
    # "repository" : "abcdefg",
    "repo" : "abcdefg",
    "domains" : ["someunknowndomain.withsubdomain.com"],
    "name_variants" : ["The Amazing University of Science, the Arts and Business (not to mention Medicine)"],
    "author_ids" : [],
    "postcodes" : [],
    "grants" : ["alkjsdfoiwqefwqefw"],
    "strings": []
}
"""repository config with no useful data"""

REPO_CONFIG = {
    # "repository" : "abcdefg",
    "repo" : "abcdefg",
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
"""Example repository config"""

MATCH_PROV = {
    # "repository" : "abcdefg",
    "repo" : "abcdefg",
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
"""Example match provenance"""
