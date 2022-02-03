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
    """ The base index type to use to store these objects - 
    this will be appended by the time-boxing features of the DAO with the creation timestamp """

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
            "query": {
                "term": {"notification.exact": self.notification_id}
            },
            "size": self.size
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


class RepositoryStatusDAO(dao.ESDAO):
    """
    DAO for RepositoryStatus
    """
    __type__ = "sword_repository_status"


class DepositRecordDAO(dao.ESDAO):
    """
    DAO for DepositRecord
    """
    __type__ = "sword_deposit_record"

    @classmethod
    def pull_by_ids(cls, notification_id, repository_id, size=None):
        """
        Get exactly one deposit record back associated with the notification_id and the repository_id

        :param notification_id:
        :param repository_id:
        :param size:
        :return:
        """
        q = DepositRecordQuery(notification_id, repository_id, size)
        obs = cls.object_query(q=q.query())
        if len(obs) > 0:
            return obs[0]

    @classmethod
    def pull_by_ids_raw(cls, notification_id, repository_id, size=None):
        """
        Get exactly one deposit record back associated with the notification_id and the repository_id

        :param notification_id:
        :param repository_id:
        :param size:
        :return:
        """
        q = DepositRecordQuery(notification_id, repository_id, size)
        obs = cls.query(q=q.query())
        return obs


class DepositRecordQuery(object):
    """
    Query generator for retrieving deposit records by notification id and repository id
    """

    def __init__(self, notification_id, repository_id, size=None):
        self.notification_id = notification_id
        self.repository_id = repository_id
        self.size = size

    def query(self):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        q = {
            "query": {
                "bool": {
                    "must": [
                        # {"term" : {"repository.exact" : self.repository_id}},
                        # 2018-03-07 TD : as of fix 2016-08-26 in models/sword.py
                        #                 this has to match 'repo.exact' instead!
                        #                 What a bug, good grief!
                        {"term": {"repo.exact": self.repository_id}},
                        {"term": {"notification.exact": self.notification_id}}
                    ]
                }
            },
            "sort": {"last_updated": {"order": "desc"}}
        }
        if self.size:
            q['size'] = self.size
        return q


class RequestNotification(dao.ESDAO):
    """
    DAO for RequestNotification
    """

    __type__ = 'request'
    """ The index type to use to store these objects """

    @classmethod
    def pull_by_ids(cls, notification_id, repository_id, size=None):
        """
        Get exactly one deposit record back associated with the notification_id and the repository_id

        :param notification_id:
        :param repository_id:
        :param size:
        :return:
        """
        q = RequestNotificationQuery(notification_id, repository_id, size)
        obs = cls.object_query(q=q.query())
        if len(obs) > 0:
            return obs[0]


class RequestNotificationQuery(object):
    """
    Query generator for retrieving deposit records by notification id and repository id
    """

    def __init__(self, notification_id, repository_id, size=None):
        self.notification_id = notification_id
        self.repository_id = repository_id
        self.size = size

    def query(self):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        q = {
            "query": {
                "bool": {
                    "must": [
                        # {"term" : {"repository.exact" : self.repository_id}},
                        # 2018-03-07 TD : as of fix 2016-08-26 in models/sword.py
                        #                 this has to match 'repo.exact' instead!
                        #                 What a bug, good grief!
                        {"term": {"account_id.exact": self.repository_id}},
                        {"term": {"notification_id.exact": self.notification_id}}
                    ]
                }
            },
            "sort": {"last_updated": {"order": "desc"}}
        }
        if self.size:
            q['size'] = self.size
        return q


class SwordAccountQuery(object):
    """
    Query generator for accounts which have sword activated
    """

    def __init__(self):
        pass

    def query(self):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        return {
            "query": {
                "query_string": {
                    "query": "_exists_:sword.collection AND sword.collection:/.+/"
                }
            }
        }


class RepositoryDepositLogDAO(dao.ESDAO):
    """
    DAO for RepositoryDepositLog
    """
    __type__ = "sword_repository_deposit_log"

    @classmethod
    def pull_by_repo(cls, repository_id):
        """
        Get exactly one repository log associated with the repository_id

        :param repository_id:
        :return:
        """
        q = RepositoryDepositLogQuery()
        obs = cls.object_query(q=q.query(repository_id))
        if obs and len(obs) > 0:
            return obs[0]

    @classmethod
    def pull_by_id(cls, id):
        """
        Get exactly one repository log matching the id

        :param id:
        :return:
        """
        q = RepositoryDepositLogQuery()
        obs = cls.object_query(q=q.get_record_query(id))
        if obs and len(obs) > 0:
            return obs[0]

    @classmethod
    def get_pagination_records(cls, repository_id, page=1, records_per_page=10):
        """
        Get repository logs for the page - a list, with each containing id and last_updated date of the repository log

        :param repository_id:
        :param page
        :param records_per_page
        :return:
        """
        q = RepositoryDepositLogQuery()
        obs = cls.query(q=q.get_pagination_records_query(repository_id, page=page,
                                                                records_per_page=records_per_page))
        return obs

    @classmethod
    def pull_by_date_range(cls, repo_id, from_date, to_date):
        """
        Get repository logs with last_updated date in the range

        :param repo_id:
        :param from_date:
        :param to_date:
        :return:
        """
        q = RepositoryDepositLogQuery()
        obs = cls.query(q=q.get_date_range_query(repo_id, from_date, to_date))
        return obs

    @classmethod
    def pull_deposit_days(cls, repo_id):
        """
        Get days repository logs exist for with latest record

        :param repo_id:
        :return:
        """
        q = RepositoryDepositLogQuery()
        obs = cls.query(q=q.get_deposit_dates_query(repo_id))
        return obs


class RepositoryDepositLogQuery(object):
    """
    Query generator for retrieving deposit records by notification id and repository id
    """

    def __init__(self):
        return

    def query(self, repository_id):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        return {
            "query": {
                "bool": {
                    "must": {
                        "term": {"repo.exact": repository_id}
                    }
                }
            },
            "sort": {"last_updated": {"order": "desc"}},
            "size": 1
        }

    def get_record_query(self, id):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        return {
            "query": {
                "bool": {
                    "must": {
                        "term": {"_id": id}
                    }
                }
            }
        }

    def get_pagination_records_query(self, repository_id, page=1, records_per_page=10):
        """
        Return the query as a python dict suitable for json serialisation

        :return: elasticsearch query
        """
        num_from = (page * records_per_page) - 10
        return {
            "query": {
                "bool": {
                    "must": {
                        "term": { "repo.exact": repository_id }
                    }
                }
            },
            "sort": {"last_updated": {"order": "desc"}},
            "size": records_per_page,
            "from": num_from,
            "fields" : ["id", "last_updated"],
            "_source": False
        }

    def get_date_range_query(self, repo_id, from_dt, to_date):
        return {
            "query": {
                "bool": {
                    "must": [{
                        "term": { "repo.exact": repo_id }
                    }, {
                        "range": {
                            "last_updated": {
                                "gte": from_dt,
                                "lt": to_date
                            }
                        }
                    }]

                }
            },
            "sort": {"last_updated": {"order": "desc"}},
            "size": 100
        }

    def get_deposit_dates_query(self, repo_id):
        return {
            "query": {
                "bool": {
                    "must": {
                        "term": { "repo.exact": repo_id }
                    }
                }
            },
            "aggs": {
                "deposits_by_day": {
                    "date_histogram": {
                        "field": "last_updated",
                        "calendar_interval": "day",
                        "order": { "_key": "desc" },
                        "min_doc_count": 1
                    }
                }
            },
            "size": 1,
            "sort": {"last_updated": {"order": "desc"}}
        }