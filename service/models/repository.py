from octopus.lib import dataobj
from service import dao

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
        "addresses" : ["<full organisation addresses>"],
        "keywords" : ["<keywords and subject classifications>"],
        "grants" : ["<grant names or numbers>"],
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
                "addresses" : {"contains" : "field", "coerce" : "unicode"},
                "keywords" : {"contains" : "field", "coerce" : "unicode"},
                "grants" : {"contains" : "field", "coerce" : "unicode"},
                "content_types" : {"contains" : "field", "coerce" : "unicode"},
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

class RetrievalRecord(dataobj.DataObj, dao.RetrievalRecordDAO):
    """
    {
        "id" : "<opaque id for repository config record>",
        "created_date" : "<date this notification was received>",
        "last_updated" : "<last modification time - required by storage layer>",

        "repository" : "<user id of repository doing the retrieval>",
        "notification" : "<id of the notification retrieved>",
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
                "retrieval_date" : {"coerce" : "utcdatetime"},
                "scope" : {"coerce" : "unicode", "allowed" : ["notification", "fulltext"]}
            }
        }

        self._add_struct(struct)
        super(RetrievalRecord, self).__init__(raw=raw)