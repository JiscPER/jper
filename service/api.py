from service import models, store, packages
from octopus.lib import dates, dataobj, http
from octopus.core import app
import uuid


class ValidationException(Exception):
    pass

class ParameterException(Exception):
    pass

class JPER(object):

    @classmethod
    def validate(cls, account, notification, file_handle=None):
        # does the metadata parse as valid
        try:
            note = models.UnroutedNotification(notification)
        except dataobj.DataStructureException as e:
            raise ValidationException("Problem reading notification metadata: {x}".format(x=e.message))

        # extract the package format from the metadata
        format = note.packaging_format
        if format is None and file_handle is not None:
            raise ValidationException("If zipped content is provided, metadata must specify packaging format")

        # extract the match data from the metadata
        nma = note.match_data()

        # placeholder for the extracted match data
        ma = None

        # if we've been given a file handle, validate it
        if file_handle is not None:
            # generate ids for putting it into the store
            local_id = uuid.uuid4().hex
            validated_id = uuid.uuid4().hex

            # get the Temporary Store implementation, and serialise the file handle to the local id
            s = store.StoreFactory.tmp()
            s.store(local_id, "validate.zip", source_stream=file_handle)

            # now try ingesting the temporarily stored package, using the validated_id to store it
            # also in the Temporary Store implementation.
            #
            # If this is unsuccessful, we ensure that the local and validated ids are both deleted from
            # the store, then we can raise the exception
            try:
                packages.PackageManager.ingest(validated_id, s.path(local_id, "validate.zip"), format, storage_manager=s)
            except packages.PackageException as e:
                s.delete(local_id)
                s.delete(validated_id)
                raise ValidationException("Problem reading from the zip file: {x}".format(x=e.message))

            # If successful, we should extract the metadata from the package, using the validated id and the
            # Temporary Store implementation again
            #
            # If this is unsuccessful, we ensure that the local and validated ids are both deleted from
            # the store, then we can raise the exception
            try:
                md, ma = packages.PackageManager.extract(validated_id, format, storage_manager=s)
            except packages.PackageException as e:
                s.delete(local_id)
                s.delete(validated_id)
                raise ValidationException("Problem extracting data from the zip file: {x}".format(x=e.message))

        # now check that we got some kind of actionable match data from the notification or the package
        if not nma.has_data() and (ma is None or not ma.has_data()):
            raise ValidationException("Unable to extract any actionable routing metadata from notification or associated package")

        # if we've been given files by reference, check that we can access them
        for l in note.links:
            url = l.get("url")
            if url is None:
                raise ValidationException("All supplied links must include a URL")

            # just ensure that we can get the first few bytes, and that the response is the right one
            resp, content, size = http.get_stream(url, cut_off=100, chunk_size=100)

            if resp is None:
                raise ValidationException("Unable to connecto to server to retrieve {x}".format(x=url))

            if resp.status_code != 200:
                raise ValidationException("Received unexpected status code when downloading from {x} - {y}".format(x=url, y=resp.status_code))

            if content is None or content == "":
                raise ValidationException("Received no content when downloading from {x}".format(x=url))

    @classmethod
    def create_notification(cls, account, metadata, file_handle=None):
        # Note, this is just for testing
        urn = models.UnroutedNotification()
        urn.save(blocking=True)
        return urn

    @classmethod
    def get_notification(cls, account, notification_id):
        urn = models.UnroutedNotification.pull(notification_id)
        return urn

    @classmethod
    def get_store_url(cls, account, notification_id):
        urn = models.UnroutedNotification.pull(notification_id)
        if urn is not None:
            return "http://store.router.jisc.ac.uk/1"
        else:
            return None

    @classmethod
    def get_public_url(cls, account, notification_id, content_id):
        urn = models.UnroutedNotification.pull(notification_id)
        if urn is not None:
            return "http://example.com/1"
        else:
            return None

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
        nl.timestamp = dates.now()
        nl.total = 1000         # Testing
        nl.notifications = ["not a notification"]   # Testing
        return nl

    @classmethod
    def record_retrieval(cls, account, notification_id, content_id=None):
        pass



