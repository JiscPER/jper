
class ValidationException(Exception):
    pass

class JPER(object):

    @classmethod
    def validate(cls, account, metadata, file_handle=None):
        pass

    @classmethod
    def create_notification(cls, account, metadata, file_handle=None):
        pass

    @classmethod
    def get_notification(cls, account, notitification_id):
        pass

    @classmethod
    def get_content(cls, account, notification_id):
        pass

    @classmethod
    def get_content_url(cls, account, notification_id, content_id):
        pass

    @classmethod
    def list_notifications(cls, account, since, page=1, page_size=25, repository_id=None):
        pass



