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

RETRIEVAL = {
    "repository" : "abcdefg",
    "notification" : "1234567890",
    "retrieval_date" : "2015-05-04T00:00:00Z",
    "scope" : "notification"
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
        }
    ],
    "postcodes" : ["SW1 0AA"],
    "addresses" : ["Bloomsbury, London"],
    "keywords" : ["science", "technology", "medicine"],
    "grants" : ["BB/34/juwef"],
    "content_types" : ["article"]
}

MATCH_PROV = {
    "repository" : "abcdefg",
    "notification" : "1234567890",
    "provenance" : [
        {
            "source_field" : "postcode",
            "term" : "SW1 0AA",
            "notification_field" : "address",
            "matched" : "Some Address, SW1 0AA",
            "explanation" : "found postcode in address"
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