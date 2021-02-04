from standalone_octopus.core import app
from standalone_octopus.modules.jper import models
from standalone_octopus.lib import http, dates
import json

class JPERException(Exception):
    pass

class JPERConnectionException(JPERException):
    pass

class JPERAuthException(JPERException):
    pass

class ValidationException(JPERException):
    pass

class JPER(object):

    # FilesAndJATS = "http://router.jisc.ac.uk/packages/FilesAndJATS"
    #FilesAndJATS = "https://pubrouter.jisc.ac.uk/FilesAndJATS"
    FilesAndJATS = "https://datahub.deepgreen.org/FilesAndJATS"

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key if api_key is not None else app.config.get("JPER_API_KEY")
        self.base_url = base_url if base_url is not None else app.config.get("JPER_BASE_URL")

        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    def _url(self, endpoint=None, id=None, auth=True, params=None, url=None):
        if url is None:
            url = self.base_url

        if url.endswith("/"):
            url += url[:-1]

        if endpoint is not None:
            url += "/" + endpoint

        if id is not None:
            url += "/" + http.quote(id)

        if auth:
            if params is None:
                params = {}
            if self.api_key is not None and self.api_key != "":
                params["api_key"] = self.api_key

        args = []
        for k, v in params.items():
            args.append(k + "=" + http.quote(str(v)))
        if len(args) > 0:
            if "?" not in url:
                url += "?"
            else:
                url += "&"
            qs = "&".join(args)
            url += qs

        return url

    def validate(self, notification, file_handle=None):
        # turn the notification into a json string
        data = None
        if isinstance(notification, models.IncomingNotification):
            data = notification.json()
        else:
            data = json.dumps(notification)

        # get the url that we are going to send to
        url = self._url("validate")

        # 2016-06-20 TD : switch SSL verification off
        verify = False
        
        resp = None
        if file_handle is None:
            # if there is no file handle supplied, send the metadata-only notification
            resp = http.post(url, data=data, headers={"Content-Type" : "application/json"}, verify=verify)
        else:
            # otherwise send both parts as a multipart message
            files = [
                ("metadata", ("metadata.json", data, "application/json")),
                ("content", ("content.zip", file_handle, "application/zip"))
            ]
            resp = http.post(url, files=files, verify=verify)

        if resp is None:
            raise JPERConnectionException("Unable to communicate with the JPER API")

        if resp.status_code == 401:
            raise JPERAuthException("Could not authenticate with JPER with your API key")

        if resp.status_code == 400:
            raise ValidationException(resp.json().get("error"))

        return True

    def create_notification(self, notification, file_handle=None):
        # turn the notification into a json string
        data = None
        if isinstance(notification, models.IncomingNotification):
            data = notification.json()
        else:
            data = json.dumps(notification)

        # get the url that we are going to send to
        url = self._url("notification")

        # 2016-06-20 TD : switch SSL verification off
        verify = False
        
        resp = None
        if file_handle is None:
            # if there is no file handle supplied, send the metadata-only notification
            resp = http.post(url, data=data, headers={"Content-Type" : "application/json"}, verify=verify)
        else:
            # otherwise send both parts as a multipart message
            files = [
                ("metadata", ("metadata.json", data, "application/json")),
                ("content", ("content.zip", file_handle, "application/zip"))
            ]
            resp = http.post(url, files=files, verify=verify)

        if resp is None:
            raise JPERConnectionException("Unable to communicate with the JPER API")

        if resp.status_code == 401:
            raise JPERAuthException("Could not authenticate with JPER with your API key")

        if resp.status_code == 400:
            raise ValidationException(resp.json().get("error"))

        # extract the useful information from the acceptance response
        acc = resp.json()
        id = acc.get("id")
        loc = acc.get("location")

        return id, loc

    def get_notification(self, notification_id=None, location=None):
        # get the url that we are going to send to
        if notification_id is not None:
            url = self._url("notification", id=notification_id)
        elif location is not None:
            url = location
        else:
            raise JPERException("You must supply either the notification_id or the location")

        # 2016-06-20 TD : switch SSL verification off
        verify = False

        # get the response object
        resp = http.get(url, verify=verify)

        if resp is None:
            raise JPERConnectionException("Unable to communicate with the JPER API")

        if resp.status_code == 404:
            return None

        if resp.status_code != 200:
            raise JPERException("Received unexpected status code from {y}: {x}".format(x=resp.status_code, y=url))

        j = resp.json()
        if "provider" in j:
            return models.ProviderOutgoingNotification(j)
        else:
            return models.OutgoingNotification(j)

    def get_content(self, url, chunk_size=8096):
        # just sort out the api_key
        url = self._url(url=url)

        # 2016-06-20 TD : switch SSL verification off
        verify = False
        
        # get the response object
        resp, content, downloaded_bytes = http.get_stream(url, read_stream=False, verify=verify)

        # check for errors or problems with the response
        if resp is None:
            raise JPERConnectionException("Unable to communicate with the JPER API")

        if resp.status_code == 401:
            raise JPERAuthException("Could not authenticate with JPER with your API key")

        if resp.status_code != 200:
            raise JPERException("Received unexpected status code from {y}: {x}".format(x=resp.status_code, y=url))

        # return the response object, in case the caller wants access to headers, etc.
        return resp.iter_content(chunk_size=chunk_size), resp.headers

    def list_notifications(self, since, page=None, page_size=None, repository_id=None):
        # check that the since date is valid, and get it into the right format
        if not hasattr(since, "strftime"):
            since = dates.parse(since)
        since = since.strftime("%Y-%m-%dT%H:%M:%SZ")

        # make the url params into an object
        params = {"since" : since}
        if page is not None:
            try:
                params["page"] = str(page)
            except:
                raise JPERException("Unable to convert page argument to string")
        if page_size is not None:
            try:
                params["pageSize"] = str(page_size)
            except:
                raise JPERException("Unable to convert page_size argument to string")

        # get the url, which may contain the repository id if it is not None
        url = self._url("routed", id=repository_id, params=params)

        # 2016-06-20 TD : switch SSL verification off
        verify = False
        
        # get the response object
        resp = http.get(url, verify=verify)

        # check for errors or problems with the response
        if resp is None:
            raise JPERConnectionException("Unable to communicate with the JPER API")

        if resp.status_code == 401:
            raise JPERAuthException("Could not authenticate with JPER with your API key")

        if resp.status_code == 400:
            raise JPERException(resp.json().get("error"))

        if resp.status_code != 200:
            raise JPERException("Received unexpected status code from {y}: {x} ".format(x=resp.status_code, y=url))

        # create the notification list object
        j = resp.json()
        return models.NotificationList(j)

    def iterate_notifications(self, since, repository_id=None, page_size=100):
        page = 1

        while True:
            nl = self.list_notifications(since, page=page, page_size=page_size, repository_id=repository_id)
            if len(nl.notifications) == 0:
                break
            for n in nl.notifications:
                yield n
            if page * page_size >= nl.total:
                break
            page += 1

    def record_retrieval(self, notification_id, content_id=None):
        # FIXME: not yet implemented, while waiting to see how retrieval finally
        # works
        pass
