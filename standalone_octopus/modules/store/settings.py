STORE_IMPL = "standalone_octopus.modules.store.store.StoreLocal"
STORE_TMP_IMPL = "standalone_octopus.modules.store.store.TempStore"

from standalone_octopus.lib import paths
STORE_LOCAL_DIR = paths.rel2abs(__file__, "..", "..", "..", "..", "service", "tests", "local_store", "live")
STORE_TMP_DIR = paths.rel2abs(__file__, "..", "..", "..", "..", "service", "tests", "local_store", "tmp")
STORE_JPER_URL = 'http://store'