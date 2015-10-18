##################################################
# overrides for the webapp deployment

DEBUG = True
PORT = 5998
SSL = False
THREADED = False

############################################
# important overrides for the ES module

# elasticsearch back-end connection settings
ELASTIC_SEARCH_HOST = "http://gateway:9200"
ELASTIC_SEARCH_INDEX = "jper"
ELASTIC_SEARCH_VERSION = "1.5.2"

# Classes from which to retrieve ES mappings to be used in this application
# Note: right now this is an empty list, as the ELASTIC_SEARCH_DEFAULT_MAPPING covers us
ELASTIC_SEARCH_MAPPINGS = [
# right now there are no types which require explicit mappings beyond the default
]

# initialise the index with example documents from each of the types
ELASTIC_SEARCH_EXAMPLE_DOCS = [
    "service.dao.UnroutedNotificationDAO",
    "service.dao.RoutedNotificationDAO",
    "service.dao.RepositoryConfigDAO",
    "service.dao.MatchProvenanceDAO",
    "service.dao.RetrievalRecordDAO"
]

# NOTE: this config is no longer relevant, Unrouted Notifications are no longer time-boxed
# time box configuration for unrouted notificatons
#ESDAO_TIME_BOX_UNROUTED = "month"
#ESDAO_TIME_BOX_LOOKBACK_UNROUTED = 3

# time box configuration for routed notificatons
ESDAO_TIME_BOX_ROUTED = "month"
ESDAO_TIME_BOX_LOOKBACK_ROUTED = 3

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

BASE_URL = "https://pubrouter.jisc.ac.uk/"
API_BASE_URL = BASE_URL + "api/v1/"

DEFAULT_LIST_PAGE_START = 1
DEFAULT_LIST_PAGE_SIZE = 25
MAX_LIST_PAGE_SIZE = 100

PACKAGE_HANDLERS = {
    "http://router.jisc.ac.uk/packages/FilesAndJATS" : "service.packages.FilesAndJATS",
    "https://pubrouter.jisc.ac.uk/FilesAndJATS": "service.packages.FilesAndJATS",
    "http://purl.org/net/sword/package/SimpleZip" : "service.packages.SimpleZip"
}


USERDIR = '/home/sftpusers' # this is ASSUMED in ssh config and possibly in shell scripts. So just don't change it
#API_URL = "https://pubrouter.jisc.ac.uk/api/v1/notification"
API_URL = "http://test.cottagelabs.com:5998/api/v1/notification"
TMP_DIR = "/home/mark/ftptmp"
RUN_SCHEDULE = True
MOVEFTP_SCHEDULE = 1
PROCESSFTP_SCHEDULE = 1
CHECKUNROUTED_SCHEDULE = 1
DELETE_UNROUTED = True

LOGLEVEL = 'debug'
LOGFILE = '/home/mark/jperlog'

#STORE_TMP_IMPL = "octopus.modules.store.store.TempStore"

#STORE_IMPL = "octopus.modules.store.store.StoreLocal"
STORE_IMPL = "octopus.modules.store.store.StoreJper"
#STORE_JPER_URL = 'http://store'
STORE_JPER_URL = 'http://localhost:5999'

from octopus.lib import paths
STORE_LOCAL_DIR = paths.rel2abs(__file__, "..", "service", "tests", "local_store", "live")
STORE_TMP_DIR = paths.rel2abs(__file__, "..", "service", "tests", "local_store", "tmp")

############################################
# Configuration for when the app is operated in functional testing mode

FUNCTIONAL_TEST_MODE = False

KEEP_FAILED_NOTIFICATIONS = False