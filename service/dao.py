"""
This module contains all the Data Access Objects for models which are persisted to Elasticsearch
at some point in their lifecycle.

Each DAO is an extension of the octopus ESDAO utility class which provides all of the ES-level heavy lifting,
so these DAOs mostly just provide information on where to persist the data, and some additional storage-layer
query methods as required
"""

from octopus.modules.es import dao

class ContentLogDAO(dao.ESDAO):
    __type__ = 'contentlog'

class UnroutedNotificationDAO(dao.ESDAO):
    """
    DAO for UnroutedNotifications
    """

    __type__ = 'unrouted'
    """ The index type to use to store these objects """

    @classmethod
    def example(cls):
        """
        request a document which acts as an example for this type
        """
        from service.tests import fixtures
        return cls(fixtures.NotificationFactory.unrouted_notification())

class RoutedNotificationDAO(dao.TimeBoxedTypeESDAO):
    """
    DAO for RoutedNotification

    This is an extension of the TimeBoxedTypeESDAO object, which means that a new type is created very
    period (e.g. monthly) for new content.  This enables rapid dropping of old index types without affecting
    Elasticsearch performance, and works here because RoutedNotifications only persiste for a limited time
    """

    __type__ = 'routed'
    """ The base index type to use to store these objects - this will be appended by the time-boxing features of the DAO with the creation timestamp """

    @classmethod
    def example(cls):
        """
        request a document which acts as an example for this type
        """
        from service.tests import fixtures
        return cls(fixtures.NotificationFactory.routed_notification())

# class StalledNotificationDAO(dao.ESDAO):
#     """
#     DAO for StalledNotifications
#     """
# 
#     __type__ = "stalled"
#     """ The index type to use to store these objects """

class FailedNotificationDAO(dao.ESDAO):
    """
    DAO for FailedNotifications
    """

    __type__ = "failed"
    """ The index type to use to store these objects """

class RepositoryConfigDAO(dao.ESDAO):
    """
    DAO for RepositoryConfig
    """

    __type__ = 'repo_config'
    """ The index type to use to store these objects """

class MatchProvenanceDAO(dao.ESDAO):
    """
    DAO for MatchProvenance
    """

    __type__ = "match_prov"
    """ The index type to use to store these objects """

    @classmethod
    def pull_by_notification(cls, notification_id, size=10):
        """
        List all of the match provenance information for the requested notification

        :param notification_id: the id of the notification for which to retrieve match provenance
        :param size: the maximum number to return (defaults to 10)
        """
        q = MatchProvNotificationQuery(notification_id, size=size)
        return cls.object_query(q=q.query())

class MatchProvNotificationQuery(object):
    """
    Query wrapper which generates an ES query for retrieving match provenance objects
    based on the notification to which they are attached
    """
    def __init__(self, notification_id, size=10):
        """
        Set the parameters of the query

        :param notification_id: the id of the notification for which to retrieve match provenance
        :param size: the maximum number to return (defaults to 10)
        """
        self.notification_id = notification_id
        self.size = size

    def query(self):
        """
        generate the query as a python dictionary object

        :return: a python dictionary containing the ES query, ready for JSON serialisation
        """
        return {
            "query" : {
                "term" : {"notification.exact" : self.notification_id}
            },
            "size" : self.size
        }

class RetrievalRecordDAO(dao.ESDAO):
    """
    DAO for RetrievalRecord
    """

    __type__ = "retrieval"
    """ The index type to use to store these objects """

class AccountDAO(dao.ESDAO):
    """
    DAO for Account
    """

    __type__ = "account"
    """ The index type to use to store these objects """


class AllianceDAO(dao.ESDAO):
    """
    DAO for Alliance (DeepGreen add-on)
    """

    __type__ = "alliance"
    """ The index type to use to store these objects """

class LicenseDAO(dao.ESDAO):
    """
    DAO for License (DeepGreen add-on)
    """

    __type__ = "license"
    """ The index type to use to store these objects """

