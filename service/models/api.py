from octopus.lib import dataobj
from service.models.notifications import NotificationMetadata, UnroutedNotification
from copy import deepcopy

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
            "required" : [],

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
                    },
                    "required" : []
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

    def make_unrouted(self):
        return UnroutedNotification(deepcopy(self.data))

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
                "packaging" : "<package format identifier, if required>"
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
        super(OutgoingNotification, self).__init__(raw=raw)

    @property
    def links(self):
        return self._get_list("links")

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
        return self._get_list("notifications")

    @notifications.setter
    def notifications(self, val):
        self._set_list("notifications", val)
