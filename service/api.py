from service import models
from octopus.lib import dates
from octopus.core import app


class ValidationException(Exception):
    pass

class ParameterException(Exception):
    pass

class JPER(object):

    @classmethod
    def validate(cls, account, metadata, file_handle=None):
        pass

    @classmethod
    def create_notification(cls, account, metadata, file_handle=None):
        urn = models.UnroutedNotification()
        urn.id = urn.makeid()
        return urn

    @classmethod
    def get_notification(cls, account, notitification_id):
        urn = models.UnroutedNotification()
        urn.id = urn.makeid()
        return urn

    @classmethod
    def get_store_url(cls, account, notification_id):
        return "http://store.router.jisc.ac.uk/1"

    @classmethod
    def get_public_url(cls, account, notification_id, content_id):
        return "http://example.com/1"

    @classmethod
    def list_notifications(cls, account, since, page=None, page_size=None, repository_id=None):
        try:
            since = dates.parse(since)
        except ValueError as e:
            raise ParameterException("Unable to understand since date '{x}'".format(x=since))

        if page == 0:
            raise ParameterException("'page' parameter must be greater than or equal to 1")

        if page_size == 0 or page_size > app.config.get("MAX_LIST_PAGE_SIZE"):
            raise ParameterException("page size must be between 1 and {x}".format(x=app.config.get("MAX_LIST_PAGE_SIZE")))

        nl = models.NotificationList()
        nl.since = dates.format(since)
        nl.page = page
        nl.page_size = page_size
        return nl

    @classmethod
    def record_retrieval(cls, account, notification_id, content_id=None):
        pass



