##################################################
# overrides for the webapp deployment

DEBUG = True
PORT = 5000
SSL = False
THREADED = True

############################################
# important overrides for the ES module

# elasticsearch back-end connection settings
ELASTIC_SEARCH_HOST = "http://localhost:9200"
ELASTIC_SEARCH_INDEX = "jper"
ELASTIC_SEARCH_VERSION = "1.4.4"

# Classes from which to retrieve ES mappings to be used in this application
ELASTIC_SEARCH_MAPPINGS = [
    "service.dao.UnroutedNotificationDAO",
    "service.dao.RoutedNotificationDAO",
    "service.dao.RepositoryConfigDAO",
    "service.dao.MatchProvenanceDAO",
    "service.dao.RetrievalRecordDAO"
]

###########################################
# Email configuration
MAIL_FROM_ADDRESS = "us@cottagelabs.com"    # FIXME: actual from address
MAIL_SUBJECT_PREFIX = "[router] "

############################################
# important overrides for account module

ACCOUNT_ENABLE = False
SECRET_KEY = "super-secret-key"