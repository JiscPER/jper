from octopus.modules.es import dao

class UnroutedNotificationDAO(dao.ESDAO):
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

class FailedNotificationDAO(dao.ESDAO):
    __type__ = "failed"

class RepositoryConfigDAO(dao.ESDAO):
    __type__ = 'repo_config'

class MatchProvenanceDAO(dao.ESDAO):
    __type__ = "match_prov"

    @classmethod
    def pull_by_notification(cls, notification_id):
        q = MatchProvNotificationQuery(notification_id)
        return cls.object_query(q=q.query())

class MatchProvNotificationQuery(object):
    def __init__(self, notification_id):
        self.notification_id = notification_id
    def query(self):
        return {
            "query" : {
                "term" : {"notification.exact" : self.notification_id}
            }
        }

class RetrievalRecordDAO(dao.ESDAO):
    __type__ = "retrieval"

class AccountDAO(dao.ESDAO):
    __type__ = "account"