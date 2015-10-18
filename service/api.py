from flask import url_for
from flask.ext.login import current_user
from service import models, packages
from octopus.lib import dates, dataobj, http
from octopus.core import app
from octopus.modules.store import store
import uuid, json


class ValidationException(Exception):
    pass

class ParameterException(Exception):
    pass

class JPER(object):

    @classmethod
    def validate(cls, account, notification, file_handle=None):
        magic = uuid.uuid4().hex
        app.logger.info("Request:{z} - Validate request received from Account:{x}".format(z=magic, x=account.id))

        # does the metadata parse as valid
        try:
            incoming = models.IncomingNotification(notification)
        except dataobj.DataStructureException as e:
            app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(x=account.id, y=e.message, z=magic))
            raise ValidationException("Problem reading notification metadata: {x}".format(x=e.message))

        # if so, convert it to an unrouted notification
        note = incoming.make_unrouted()

        # extract the package format from the metadata
        format = note.packaging_format
        if format is None and file_handle is not None:
            msg = "If zipped content is provided, metadata must specify packaging format"
            app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
            raise ValidationException(msg)

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
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=e.message))
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
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=e.message))
                raise ValidationException("Problem extracting data from the zip file: {x}".format(x=e.message))

            # ensure that we don't keep copies of the files
            s.delete(local_id)
            s.delete(validated_id)

        # now check that we got some kind of actionable match data from the notification or the package
        if not nma.has_data() and (ma is None or not ma.has_data()):
            msg = "Unable to extract any actionable routing metadata from notification or associated package"
            app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
            raise ValidationException(msg)

        # if we've been given files by reference, check that we can access them
        for l in note.links:
            url = l.get("url")
            if url is None:
                msg = "All supplied links must include a URL"
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
                raise ValidationException(msg)

            # just ensure that we can get the first few bytes, and that the response is the right one
            resp, content, size = http.get_stream(url, cut_off=100, chunk_size=100)

            if resp is None:
                msg = "Unable to connecto to server to retrieve {x}".format(x=url)
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
                raise ValidationException(msg)

            if resp.status_code != 200:
                msg = "Received unexpected status code when downloading from {x} - {y}".format(x=url, y=resp.status_code)
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
                raise ValidationException(msg)

            if content is None or content == "":
                msg = "Received no content when downloading from {x}".format(x=url)
                app.logger.info("Request:{z} - Validate request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=msg))
                raise ValidationException(msg)

        app.logger.info("Request:{z} - Validate request Account:{x} succeeded".format(z=magic, x=account.id))

    @classmethod
    def create_notification(cls, account, notification, file_handle=None):
        if not account.has_role('publisher') and not current_user.is_super:
            return False

        magic = uuid.uuid4().hex
        app.logger.info("Request:{z} - Create request received from Account:{x}".format(z=magic, x=account.id))

        # attempt to serialise the record
        try:
            incoming = models.IncomingNotification(notification)
        except dataobj.DataStructureException as e:
            app.logger.info("Request:{z} - Create request from Account:{x} failed with error '{y}'".format(x=account.id, y=e.message, z=magic))
            raise ValidationException("Problem reading notification metadata: {x}".format(x=e.message))

        # if successful, convert it to an unrouted notification
        note = incoming.make_unrouted()

        # set the id for the record, as we'll use this when we save the notification, and
        # when we store the associated file
        note.id = note.makeid()

        # record the provider's account id against the notification
        note.provider_id = account.id

        # if we've been given a file handle, save it
        if file_handle is not None:
            # get the format of the package
            format = note.packaging_format

            # generate ids for putting it into the store
            local_id = uuid.uuid4().hex

            # get the Temporary Store implementation, and serialise the file handle to the local id
            tmp = store.StoreFactory.tmp()
            tmp.store(local_id, "incoming.zip", source_stream=file_handle)

            # now try ingesting the temporarily stored package, using the note's id to store it
            # in the remote storage
            #
            # If this is unsuccessful, we ensure that the local and note ids are both deleted from
            # the store, then we can raise the exception
            remote = store.StoreFactory.get()
            try:
                packages.PackageManager.ingest(note.id, tmp.path(local_id, "incoming.zip"), format, storage_manager=remote)
            except packages.PackageException as e:
                tmp.delete(local_id)
                remote.delete(note.id)
                app.logger.info("Request:{z} - Create request from Account:{x} failed with error '{y}'".format(z=magic, x=account.id, y=e.message))
                raise ValidationException("Problem reading from the zip file: {x}".format(x=e.message))

            # remove the local copy
            tmp.delete(local_id)

            # if the content was successfully ingested, then annotate the notification with the content url
            url = app.config.get("API_BASE_URL") + "notification/" + note.id + "/content"
            note.add_link(url, "package", "application/zip", "router", note.packaging_format)

        # if we get to here there was either no package, or the package saved successfully, so we can store the
        # note
        note.save()
        app.logger.info("Request:{z} - Create request from Account:{x} succeeded; Notification:{y}".format(z=magic, x=account.id, y=note.id))
        return note

    @classmethod
    def get_notification(cls, account, notification_id):
        try:
            accid = account.id
        except:
            accid = None

        magic = uuid.uuid4().hex

        # notifications may either be in the unrouted or routed indices.
        # start at the routed notification (as they may appear in both)
        rn = models.RoutedNotification.pull(notification_id)
        if rn is not None:
            if accid == rn.provider_id:
                app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y}; returns the provider's version of the routed notification".format(z=magic, x=accid, y=notification_id))
                return rn.make_outgoing(provider=True)
            else:
                app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y}; returns the public version of the routed notification".format(z=magic, x=accid, y=notification_id))
                return rn.make_outgoing()
        if account.has_role('publisher') or current_user.is_super:
            urn = models.UnroutedNotification.pull(notification_id)
            if urn is not None:
                if accid == urn.provider_id:
                    app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y}; returns the provider's version of the unrouted notification".format(z=magic, x=accid, y=notification_id))
                    return urn.make_outgoing(provider=True)
                else:
                    app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y}; returns the public version of the unrouted notification".format(z=magic, x=accid, y=notification_id))
                    return urn.make_outgoing()

        app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y}; no distributable notification of that id found".format(z=magic, x=accid, y=notification_id))
        return None

    @classmethod
    def get_content(cls, account, notification_id, filename=None):
        magic = uuid.uuid4().hex
        urn = models.UnroutedNotification.pull(notification_id)
        if urn is not None and (account.has_role('publisher') or current_user.is_super):
            if filename is not None:
                store_filename = filename
            else:
                pm = packages.PackageFactory.incoming(urn.packaging_format)
                store_filename = pm.zip_name()
            sm = store.StoreFactory.get()
            app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y} Content:{a}; returns unrouted notification stored file {b}".format(z=magic, x=account.id, y=notification_id, a=filename, b=store_filename))
            return sm.get(urn.id, store_filename)
        else:
            rn = models.RoutedNotification.pull(notification_id)
            if rn is not None and account.has_role('publisher') or ( account.has_role('repository') and account.id in rn.repositories) or current_user.is_super:
                if filename is not None:
                    store_filename = filename
                else:
                    pm = packages.PackageFactory.incoming(rn.packaging_format)
                    store_filename = pm.zip_name()
                sm = store.StoreFactory.get()
                app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y} Content:{a}; returns routed notification stored file {b}".format(z=magic, x=account.id, y=notification_id, a=filename, b=store_filename))
                return sm.get(rn.id, store_filename)
            else:
                app.logger.info("Request:{z} - Retrieve request from Account:{x} on Notification:{y} Content:{a}; no suitable content found to return".format(z=magic, x=account.id, y=notification_id, a=filename))
                return None

    @classmethod
    def get_proxy_url(cls, account, notification_id, pid):
        rn = models.RoutedNotification.pull(notification_id)
        if rn is None:
            return None
        else:
            lurl = None
            for link in rn.links:
                if link.get('proxy',False) == pid:
                    lurl = link['url']
            return lurl
        
            
    @classmethod
    def get_public_url(cls, account, notification_id, content_id):
        urn = models.UnroutedNotification.pull(notification_id)
        if urn is not None:
            return "http://example.com/1"
        else:
            rn = models.RoutedNotification.pull(notification_id)
            if rn is not None:
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
        qr = {
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "created_date": {
                                            "gte": nl.since
                                        }
                                    }
                                }                                
                            ]
                        }
                    }
                }
            },
            "sort": [{"analysis_date":{"order":"asc"}}],
            "from": (page - 1) * page_size,
            "size": page_size
        }
        
        if repository_id is not None:
            qr['query']['filtered']['filter']['bool']['must'].append( { "term": { "repositories.exact": repository_id } })
            app.logger.debug(str(repository_id) + ' list notifications for query ' + json.dumps(qr))
        else:
            app.logger.debug('List all notifications for query ' + json.dumps(qr))

        res = models.RoutedNotification.query(q=qr)
        app.logger.debug('List all notifications query resulted ' + json.dumps(res))
        nl.notifications = [i['_source'] for i in res.get('hits',{}).get('hits',[])]
        nl.total = res.get('hits',{}).get('total',0)
        return nl



