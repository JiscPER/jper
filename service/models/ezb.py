
from octopus.core import app
from service import dao
from octopus.lib import dataobj

class Alliance(dataobj.DataObj, dao.AllianceDAO):
    """
    Class to represent the alliance license information as provided by EZB (Regensburg).  The alliance 
    information is needed by the system to ensure correct (and lawful!) routing of notifications.

    See also the core system model documentation for details on the JSON structure of this model.
    """
    '''
    {
        "id" : "<unique persistent item id>",
        "created_date" : "<date item created>",
        "last_updated" : "<date item last modified>",

        "name" : "<(human readable) name of the alliance license>",
        "license_id" : "<the license_id this alliance is connected to>",
        "identifier" : [ { "type" : "<description of id type, e.g. ezb|doi|url|...>", "id" : "string" } ],
        "participant" : [ { "name" : "<name of participating institution>",
                            "identifier" : [ { "type" : "<kind of id, e.g. sigel|ezb|...>", "id" : "string" } ]
                        ]
    }
    '''
    def __init__(self, raw=None)
        """
        Create a new instance of the Alliance object, optionally around the raw python dictionary.

        :param raw: python dict object containing alliance data of participating institutions
        """
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "utcdatetime"},
                "last_updated" : {"coerce" : "utcdatetime"},
                "name" : {"coerce" : "unicode"},
                "license_id" : {"coerce" : "unicode"}
            },
            # not (yet?) needed here
            # "objects" : [ 
            # ],
            "lists" : {
                "identifier" : {"contains" : "object"},
                "participant" : {"contains" : "object"}
            },
            "required" : [],

            "structs" : {
                "identifier" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "id" : {"coerce" : "unicode"}
                    }
                },
                "participant" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"}
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
        self._add_struct(struc)
        super(Alliance, self).__init__(raw=raw)
        
    @property
    def name(self):
        """
        The (human readable) name of this alliance license package.

        :return: The alliace license package name
        """
        return self._get_single("name", coerce=self.to_unicode())

    @name.setter
    def name(self, val):
        """
        Set the (human readable) name of this alliance license package.
  
        :param val: the alliance license package name
        """
        self._set_single("name", val, coerce=self.to_unicode())

    @property
    def license_id(self):
        """
        The license_id of the alliance license. Should correspond to the value in licence record.

        :return: the license_id
        """
        return self._get_single("license_id", coerce=self.to_unicode())

    @license_id.setter
    def license_id(self, val):
        """
        Set the license_id of the alliance license, corresponding to the value in licence record.

        :param val: the license_id
        """
        self._set_single("license_id", val, coerce=self.to_unicode())

    @property
    def identifiers(self):
        """
        The list of identifier objects for the alliance license package.  The returned objects have the form:

        ::

            { "type" : "<identifier type>", "id" : "<actual identifier>" }

        :return: List of python dict objects containing the identifier information
        """
        return self._get_list("identifier")

    def get_identifier(self, type):
        """
        The list of identifiers, as filtered by type.

        Unlike .identifiers, this returns a list of strings of the actual identifiers, rather than the dict representation.

        :return: List of identifiers of the requested type
        """
        ids = self._get_list("identifier")
        res = []
        for i in ids:
            if i.get("type") == type:
                res.append(i.get("id"))
        return res

    def add_identifier(self, id, type):
        """
        Add an identifier for the alliance package, with the given id and type

        :param id: the id for the alliance licence package
        :param type: the type of identifier (e.g. "ezb")
        :return:
        """
        if id is None or type is None:
            return
        uc = dataobj.to_unicode()
        obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
        self._delete_from_list("identifier", matchsub=obj, prune=False)
        self._add_to_list("identifier", obj)

    @property
    def participants(self):
        """
        The list of participant objects for the alliance license package.  The returned objects have the form:

        ::

            {
                "name" : "<participant institution name>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ]
            }

        :return: List of python dict objects containing the participants information
        """
        return self._get_list("participant")

    @participants.setter
    def participants(self, objlist):
        """
        Set the supplied list of participant objects for the alliance license package. 

        The structure of each participant object will be validated, and the values coerced to unicode where necessary.

        Participants objects should have the form:

        ::

            {
                "name" : "<participant institution name>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ]
            }

        :param objlist: list of participant objects
        :return: 
        """
        # validate the object structure on-the-fly
        allowed = [ "name", "identifier" ]
        for obj in objlist:
            for k in obj.keys():
                if k not in allowed:
                    raise dataobj.DataSchemaException("Participant object must only contain the following keys: {x}".format(x=", ".join(allowed)))

            # coerce the values of some of the keys
            uc = dataobj.to_unicode()
            for k in [ "name" ]:
                if k in obj:
                    obj[k] = self._coerce(obj[k], uc)

        # finally write it
        self._set_list("participant", objlist)

    def add_participant(self, part_object)
        """
        Add a single participant object to the existing list of participant objects.

        Additions are not validated or coerced, so use with extreme(!) caution (or not at all).

        Participant objects should be of the form:

        ::

            {
                "name" : "<participant institution name>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ]
            }

        :param part_object: participant object to add
        :return:
        """
        self._delete_from_list("participant", matchsub=part_object)
        self._add_to_list("participant", part_object)



class License(dataobj.DataObj, dao.LicenseDAO)
    """
    Class to represent the license information as provided, for example, by an regular excerpt
    of data of EZB (Regensburg) on all journals included in a particular license, e.g. alliance 
    license.  The license information is needed by the system to ensure correct (and lawful!) 
    routing of notifications.

    See also the core system model documentation for details on the JSON structure of this model.
    """
    '''
    {
        "id" : "<unique persistent item id>",
        "created_date" : "<date item created>",
        "last_updated" : "<date item last modified>",

        "name" : "<(human readable) name of the (alliance) license>",
        "type" : "<type of license, e.g. 'alliance', 'national', 'open', ...>",
        "identifier" : [ 
            { 
                "type" : "<description of id type, e.g. ezb|doi|url|...>", 
                "id" : "<id-string>" 
            } 
        ],
        "journal" : [ 
            { 
                "title" : "<(full) title of journal>",
                "publisher" : "<name of publisher>", 
                "identifier" : [ 
                    { 
                        "type" : "<kind of journal id, e.g. issn|pissn|zdb|doi|...>", 
                        "id" : "<actual journal identifier>" 
                    } 
                ],
                "link" : [ 
                    { 
                        "type" : "<kind of link, e.g. 'ezb', 'pub', ...>",
                        "url" : "<actual http(s) address string"
                    }
                ],
                "subject" : [ "<keyword or subject of journal>", ... ]
                "embargo" : { "duration" : int }
                "period" : [ 
                    {
                        "type" : "<kind of period of time, e.g. 'year','issue', ...>",
                        "start" : "<first item of period of time>",
                        "end" : <last item of period of time>"
                    }
                ]
            }
        ]
    }
    '''
    def __init__(self, raw=None)
        """
        Create a new instance of the License object, optionally around the raw python dictionary.

        :param raw: python dict object containing all data concering the legal license agreement
        """
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "created_date" : {"coerce" : "utcdatetime"},
                "last_updated" : {"coerce" : "utcdatetime"},
                "name" : {"coerce" : "unicode"},
                "type" : {"coerce" : "unicode", "allowed_values" : ["alliance", "national"]}
            },
            # not (yet?) needed here
            # "objects" : [ 
            # ],
            "lists" : {
                "identifier" : {"contains" : "object"},
                "journal" : {"contains" : "object"}
            },
            "required" : [],

            "structs" : {
                "identifier" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "id" : {"coerce" : "unicode"}
                     },
                     "required" : []
                },
                "journal" : {
                    "fields" : {
                        "title" : {"coerce" : "unicode"},
                        "publisher" : {"coerce" : "unicode"},
                    },
                    "objects" : [
                        "embargo"
                    ]
                    "lists" : {
                        "identifier" : {"contains" : "object"},
                        "link" : {"contains" : "object"},
                        "period" : {"contains" : "object"},
                        "subject" : {"contains" : "field", "coerce" : "unicode"}
                    }
                    "required" : [],

                    "structs" : {
                        "embargo" : {
                            "fields" : {
                                "duration" : {"coerce" : "integer"}
                            }
                        },
                        "identifier" : {
                            "fields" : {
                                "type" : {"coerce" : "unicode"},
                                "id" : {"coerce" : "unicode"}
                            }
                        },
                        "link" : {
                            "fields" : {
                                "type" : {"coerce" : "unicode"},
                                "url" : {"coerce" : "unicode"}
                            }
                        },
                        "period" : {
                            "fields" : {
                                "type" : {"coerce" : "unicode"},
                                "start" : {"coerce" : "unicode"},
                                "end" : {"coerce" : "unicode"}
                            }
                        }
                    }
                }
            }
        }

        self._add_struct(struct)
        super(License, self).__init(raw=raw)

    @property
    def name(self):
        """
        The (human readable) name of this license package.

        :return: The license package name
        """
        return self._get_single("name", coerce=self.to_unicode())

    @name.setter
    def name(self, val):
        """
        Set the (human readable) name of this license package.
  
        :param val: the license package name
        """
        self._set_single("name", val, coerce=self.to_unicode())

    @property
    def type(self):
        """
        The type of this license package.

        :return: The license package type ('alliance', 'national',...)
        """
        return self._get_single("type", coerce=self.to_unicode())

    @type.setter
    def type(self, val):
        """
        Set the type of this license package.
  
        :param val: the license package type
        """
        if val not in ["alliance", "national", "other"]:
            raise dataobj.DataSchemaException("license type must be one of 'alliance', 'national', or 'other'")

        self._set_single("type", val, coerce=self.to_unicode())

    @property
    def identifiers(self):
        """
        The list of identifier objects for the license package.  The returned objects have the form:

        ::

            { "type" : "<identifier type>", "id" : "<actual identifier>" }

        :return: List of python dict objects containing the identifier information
        """
        return self._get_list("identifier")

    def get_identifier(self, type):
        """
        The list of identifiers, as filtered by type.

        Unlike .identifiers, this returns a list of strings of the actual identifiers, rather than the dict representation.

        :return: List of identifiers of the requested type
        """
        ids = self._get_list("identifier")
        res = []
        for i in ids:
            if i.get("type") == type:
                res.append(i.get("id"))
        return res

    def add_identifier(self, id, type):
        """
        Add an identifier for the license package, with the given id and type

        :param id: the id for the licence package
        :param type: the type of identifier (e.g. "ezb")
        :return:
        """
        if id is None or type is None:
            return
        uc = dataobj.to_unicode()
        obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
        self._delete_from_list("identifier", matchsub=obj, prune=False)
        self._add_to_list("identifier", obj)

    @property
    def journal(self):
        """
        The list of journal objects of the license package.  The returned objects have the form:

        ::

            {
                "title" : "<(full) journal title>",
                "publisher" : "<name of publisher>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ],
                "link" : [
                    { "type" : "<link-owner to which is pointed>", "url" : "<actual http(s) address>" }
                ],
                "period" : [
                    { 
                        "type" : "<kind of item of period, e.g. year|issue|...>", 
                        "start" : "<fist item of period>", 
                        "end" : "<last item of time period>"
                    }
                ],
                "embargo" : { "duration" : integer },
                "subject" : [ "keyword or subject", ...]
            }

        :return: List of python dict objects containing the participants information
        """
        return self._get_list("journal")

    @journal.setter
    def journal(self, objlist):
        """
        Set the supplied list of journal objects for the alliance license package. 

        The structure of each journal object will be validated, and the values coerced to unicode where necessary.

        Journal objects should be of the form:

        ::

            {
                "title" : "<(full) journal title>",
                "publisher" : "<name of publisher>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ],
                "link" : [
                    { "type" : "<link-owner to which is pointed>", "url" : "<actual http(s) address>" }
                ],
                "period" : [
                    { 
                        "type" : "<kind of item of period, e.g. year|issue|...>", 
                        "start" : "<fist item of period>", 
                        "end" : "<last item of time period>"
                    }
                ],
                "embargo" : { "duration" : integer },
                "subject" : [ "keyword or subject", ...]
            }

        :param objlist: list of journal objects
        :return: 
        """
        # validate the object structure on-the-fly
        allowed = [ "title", "publisher", "identifier", "link", "period", "embargo", "subject" ]
        for obj in objlist:
            for k in obj.keys():
                if k not in allowed:
                    raise dataobj.DataSchemaException("Journal object must only contain the following keys: {x}".format(x=", ".join(allowed)))

            # coerce the values of some of the keys
            uc = dataobj.to_unicode()
            for k in [ "title", "publisher" ]:
                if k in obj:
                    obj[k] = self._coerce(obj[k], uc)

        # finally write it
        self._set_list("journal", objlist)

    def add_journal(self, journal_object)
        """
        Add a single journal object to the existing list of journal objects.

        Additions are not validated or coerced, so use with extreme(!) caution (or not at all).

        Journal objects should be of the form:

        ::

            {
                "title" : "<(full) journal title>",
                "publisher" : "<name of publisher>",
                "identifier" : [
                    { "type" : "<identifier type>", "id" : "<actual identifier>" }
                ],
                "link" : [
                    { "type" : "<link-owner to which is pointed>", "url" : "<actual http(s) address>" }
                ],
                "period" : [
                    { 
                        "type" : "<kind of item of period, e.g. year|issue|...>", 
                        "start" : "<fist item of period>", 
                        "end" : "<last item of time period>"
                    }
                ],
                "embargo" : { "duration" : integer },
                "subject" : [ "keyword or subject", ...]
            }

        :param part_object: journal object to add
        :return:
        """
        self._delete_from_list("journal", matchsub=journal_object)
        self._add_to_list("journal", journal_object)

