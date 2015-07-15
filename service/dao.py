from octopus.modules.es import dao

class UnroutedNotificationDAO(dao.TimeBoxedTypeESDAO):
    __type__ = 'unrouted'

    @classmethod
    def example(cls):
        from service.tests import fixtures
        return cls(fixtures.NotificationFactory.unrouted_notification())

class RoutedNotificationDAO(dao.TimeBoxedTypeESDAO):
    __type__ = 'routed'

    @classmethod
    def example(cls):
        from service.tests import fixtures
        return cls(fixtures.NotificationFactory.routed_notification())

class RepositoryConfigDAO(dao.ESDAO):
    __type__ = 'repo_config'

class MatchProvenanceDAO(dao.ESDAO):
    __type__ = "match_prov"

class RetrievalRecordDAO(dao.ESDAO):
    __type__ = "retrieval"
	
class AccountDAO(dao.ESDAO):
	__type__ = "account"