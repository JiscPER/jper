from octopus.modules.es import dao

class UnroutedNotificationDAO(dao.ESDAO):
    __type__ = 'unrouted'

class RoutedNotificationDAO(dao.ESDAO):
    __type__ = 'routed'

class RepositoryConfigDAO(dao.ESDAO):
    __type__ = 'repo_config'

class MatchProvenanceDAO(dao.ESDAO):
    __type__ = "match_prov"

class RetrievalRecordDAO(dao.ESDAO):
    __type__ = "retrieval"