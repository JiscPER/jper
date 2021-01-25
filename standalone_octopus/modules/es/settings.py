##############################################################
# Basic ElasticSearch connectivity settings
##############################################################

# index information to use in live
ELASTIC_SEARCH_HOST = "http://localhost:9200"
ELASTIC_SEARCH_INDEX = "db"

ELASTIC_SEARCH_VERSION = "0.90.13"

# index to use for testing (see testindex.py)
ELASTIC_SEARCH_TEST_INDEX = "test"

##############################################################
# Index setup and mappings
##############################################################

# should the initialise routing initialise the index automatically?
INITIALISE_INDEX = True

# mapping that will be pushed into the _default_ field of the index
# itself, and be applied to all types that are subsequently created
ELASTIC_SEARCH_DEFAULT_MAPPING = {
    'dynamic_templates': [
        {
            'default': {
                'mapping': {
                    'fields': {
                        'exact': {
                            'index': 'not_analyzed',
                            'store': 'yes',
                            'type': '{dynamic_type}'
                        },
                        '{name}': {
                            'index': 'analyzed',
                            'store': 'no',
                            'type': '{dynamic_type}'
                        }
                    },
                    'type': 'multi_field'
                },
                'match': '*',
                'match_mapping_type': 'string'
            }
        }
    ],
    'properties': {
        'location': {'type': 'geo_point'}
    }
}

# an array of DAO classes from which to retrieve the type-specific ES mappings
# to be loaded into the index during initialisation.  You should override this
# in service.py
# If none of your types require mappings different from the ELASTIC_SEARCH_DEFAULT_MAPPING
# above then you can leave this list empty
ELASTIC_SEARCH_MAPPINGS = [
    # service.dao.MyDAO
]

# an array of DAO classes from which to retrieve example documents that will
# be pushed into the index and then deleted during startup in order to initialise
# the type/mappings.  You should override this in service.py
ELASTIC_SEARCH_EXAMPLE_DOCS = [
    # service.dao.MyDAO
]

# an array of DAO classes which initialise themselves by having their self_init()
# method called
ELASTIC_SEARCH_SELF_INIT = [
    # service.dao.MyDAO
]

##############################################################
# Special DAO configuration
##############################################################

# The default time period to use for dynamically set index types
# allowed: second, minute, hour, day, month, year
ESDAO_DEFAULT_TIME_BOX = "month"
# You can also set the time box on a per-type basis with
# ESDAO_TIME_BOX_<UPPER CASE TYPE NAME> = "<period>"

# How many time boxes to look back on during READ operations
ESDAO_DEFAULT_TIME_BOX_LOOKBACK = 0
# You can also set the look back on a per-type basis with
# ESDAO_TIME_BOX_LOOKBACK_<UPPER CASE TYPE NAME> = <number of boxes>

# path to directory where the "next", "prev" and "curr" files for routing
# requests to the correct type are placed
from standalone_octopus.lib import paths
ESDAO_ROLLING_DIR = paths.rel2abs(__file__, "..", "..", "..", "..", "indexdir")

# map of type names to DAOs which will have the publish() or rollback()
# methods called on them
# {"mytype" : "service.dao.MyDAO"}
ESDAO_ROLLING_PLUGINS = {}

##############################################################
# Query Endpoint Configuration
##############################################################

# The query url routes and the types that are available via the query endpoint (see below for an example)
QUERY_ROUTE = {}

# query filters that are used in the above QUERY_ROUTE (see below for an example)
QUERY_FILTERS = {}

"""
e.g.
QUERY_ROUTE = {
    "query" : {                                 # the URL route at which it is mounted
        "index" : {                             # the URL name for the index type being queried
            "auth" : False,                     # whether the route requires authentication
            "role" : None,                      # if authenticated, what role is required to access the query endpoint
            "filters" : ["default"],            # names of the standard filters to apply to the query
            "dao" : "octopus.dao.MyDAO"       # classpath for DAO which accesses the underlying ES index
        }
    }
}

def default_filter(query):
    pass

QUERY_FILTERS = {
    "default" : default_filter
}
"""

##############################################################
# Public Search API Configuration
##############################################################

# maximum results per page to return, irrespective of what the user asks for
SEARCH_MAX_PAGE_SIZE = 100

# DAO through which search requests should pass.  You MUST update this if you are using
# this module, as the one defined here is just a template
SEARCH_DAO = "octopus.modules.es.dao.ESDAO"

# reference for a function to which all search results will be passed for filtering
# before being sent to the user
SEARCH_RESULT_FILTER = None

##############################################################
# Compound Field Auto-Complete Configuration
##############################################################

# Configuration for compound autocomplete url mappings and behaviour.  See below for example.
AUTOCOMPLETE_COMPOUND = {}

"""
AUTOCOMPLETE_COMPOUND = {
    "name" : {                                  # name of the autocomplete, as represented in the URL (have as many of these sections as you need)
        "fields" : ["name", "description"],     # fields to return in the compound result
        "field_name_map" : {                    # map field name to name it will be referred to in the result
            "name" : "my_name",
            "description" : "my_description"
        },
        "filters" : {                           # filters to apply to the result set
            "name.exact" : {                    # field on which to filter
                "start_wildcard" : True,        # apply start wildcard?
                "end_wildcard": True,           # apply end wildcard?
                "boost" : 2.0                   # boost to apply to matches on this field
            },
            "description.exact" : {
                "start_wildcard" : True,
                "end_wildcard": True,
                "boost" : 1.0
            }
        },
        "input_filter" : lambda x : x ,         # function to apply to an incoming string before being applied to the es query
        "default_size" : 10,                    # if no size param is specified, this is how big to make the response
        "max_size" : 25,                        # if a size param is specified, this is the limit above which it won't go
        "dao" : "octopus.dao.MyDAO"             # classpath for DAO which accesses the underlying ES index
    }
}
"""

# configuration option to pass through to the javascript UI
CLIENTJS_ES_COMPOUND_ENDPOINT = "/autocomplete/compound"


##############################################################
# Term Facet Auto-Complete Configuration
##############################################################

# Term autocomplete configuration.  See below for example
AUTOCOMPLETE_TERM = {}

"""
AUTOCOMPLETE_TERM = {
    "name" : {                                  # name of the autocomplete, as represented in the URL (have as many of these sections as you need)
        "filter" : {                            # The filter to apply to the result set
            "name.exact" : {                    # field on which to apply the filter
                "start_wildcard" : True,        # apply start wildcard
                "end_wildcard" : True          # apply end wildcard
            }
        },
        "facet" : "name.exact",                 # facet from which to get our results
        "input_filter" : lambda x : x,          # function to apply to an incoming string before being applied to the es query
        "default_size" : 10,                    # if no size param is specified, this is how big to make the response
        "max_size" : 25,                        # if a size param is specified, this is the limit above which it won't go
        "dao" : "octopus.dao.MyDAO"             # classpath for DAO which accesses the underlying ES index
    }
}
"""

# configuration option to pass through to the javascript UI
CLIENTJS_ES_TERM_ENDPOINT = "/autocomplete/term"