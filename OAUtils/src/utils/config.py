'''
Created on 26 Oct 2015

@author: Ruben.Alonso
'''
import json

ROUTER_ADDR = 'http://127.0.0.1'
ROUTER_PORT = '5998'
PROVIDER_ID = 'f23a75e9-09e3-4ed1-a313-b46e4a70ef12'
NOTIFICATION_URL = ROUTER_ADDR + ':' + ROUTER_PORT + "/api/v1/notification?api_key=" + PROVIDER_ID

FREQUENCY_MONTHLY = 'monthly'
FREQUENCY_DAILY = 'daily'
FREQUENCY_WEEKLY = 'weekly'

DB_NAME = 'elastic_search_v1'

MULTI_PAGE = 'multi_page'

#Number of days to keep in the history of the DB
HISTORY_FILE_LIMIT = 90

# Router return codes
ACCEPTED = 202
BAD_REQUEST = 400
AUTHETICATION_FAILUER = 401
URL_NOT_FOUND = 404

ACTIVE_WS_PROVIDER_QUERY = {
    "query": {
        "match": {
            "active": True
        }
    }
}

MATCH_ALL = {
    "query": {
        "match_all": {}
    }
}

WEBSERVICES_INDEX_NAME = "h_webservices"
WEBSERVICES_DOCTYPE_NAME = "webservice"
WEBSERVICES_MAPPING = {
    "webservice": {
        "properties": {
            "name": {"type": "string"},
            "url": {"type": "string"},
            "query": {"type": "string"},
            "frequency": {"type": "string"},
            "active": {"type": "boolean"},
            "email": {"type": "string"},
            "end_date": {"type": "date"},
            "engine": {"type": "string"},
            "wait_window": {"type": "integer"}
        }
    }
}

TEMPORARY_INDEX_NAME = "h_temporary"
TEMPORARY_DOCTYPE_NAME = "document"
TEMPORARY_MAPPING = ""

HISTORY_INDEX_NAME = "h_history"
HISTORY_DOCTYPE_NAME = "historic"
HISTORY_MAPPING = {
    "historic": {
        "properties": {
            "date": {"type": "date"},
            "name_ws": {"type": "string"},
            "url": {"type": "string"},
            "query": {"type": "string"},
            "start_date": {"type": "date"},
            "end_date": {"type": "date"},
            "num_files_received": {"type": "integer"},
            "num_files_sent": {"type": "integer"},
            "error": {"type": "string"}
        }
    }
}

WEBSERVICES_DATA = {}
WEBSERVICES_DATA['name'] = "EPMC"
WEBSERVICES_DATA['url'] = "http://www.ebi.ac.uk/europepmc/webservices/rest/search/resulttype=core&format=json&query=%20CREATION_DATE%3A%5B{start_date}%20TO%20{end_date}%5D"
WEBSERVICES_DATA['query'] = json.dumps({
                            "query": {
                                "filtered": {
                                    "filter": {
                                        "exists": { "field" : "authorList.author.affiliation" }
                                    }
                                }
                            }
                        })
DAYS_TO_START_FROM = 35
WEBSERVICES_DATA['frequency'] = "daily"
WEBSERVICES_DATA['active'] = True
WEBSERVICES_DATA['email'] = "pubrouter@jisc.ac.uk"
WEBSERVICES_DATA['engine'] = MULTI_PAGE
WEBSERVICES_DATA['wait_window'] = 30


configMySQL = {
               'user': 'my',
               'password': 'sql',
               'host': '127.0.0.1',
               'database': 'articles',
               'raise_on_warnings': True,
               }

#configES = [{'host': 'gateway', 'port': 9200, 'timeout': 300}]
# TODO: SE 2021-03-17 - has this always been misconfigured and never used?
configES = [{'host': 'localhost', 'port': 9200, 'timeout': 300}]