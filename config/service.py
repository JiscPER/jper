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

ACCOUNT_ENABLE = True
SECRET_KEY = "super-secret-key"


############################################
# Service-specific config

DEFAULT_LIST_PAGE_START = 1
DEFAULT_LIST_PAGE_SIZE = 25
MAX_LIST_PAGE_SIZE = 100

PACKAGE_HANDLERS = {
    "http://router.jisc.ac.uk/packages/FilesAndJATS" : "service.packages.FilesAndJATS"
}

STORE_IMPL = "service.store.StoreLocal"
STORE_TMP_IMPL = "service.store.TempStore"

from octopus.lib import paths
STORE_LOCAL_DIR = paths.rel2abs(__file__, "..", "service", "tests", "local_store")
STORE_TMP_DIR = paths.rel2abs(__file__, "..", "service", "tests", "local_store")