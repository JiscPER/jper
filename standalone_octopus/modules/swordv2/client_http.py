from sword2 import HttpLayer, HttpResponse
from standalone_octopus.lib import http
import json
from requests.auth import HTTPBasicAuth

class OctopusHttpResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        self.resp = None
        if len(args) > 0:
            self.resp = args[0]

    def __getitem__(self, att):
        return self.get(att)

    def __repr__(self):
        return self.resp.__repr__()

    @property
    def status(self):
        if self.resp is None:
            return 408  # timeout
        return self.resp.status_code

    def get(self, att, default=None):
        if att == "status":
            return self.status
        if self.resp is None:
            return default
        return self.resp.headers.get(att, default)

    def keys(self):
        return list(self.resp.headers.keys())

class OctopusHttpLayer(HttpLayer):
    def __init__(self, *args, **kwargs):
        self.username = None
        self.password = None
        self.auth = None

    def add_credentials(self, username, password):
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)

    def request(self, uri, method, headers=None, payload=None):    # Note that body can be file-like
        resp = None
        if method == "GET":
            resp = http.get(uri, headers=headers, auth=self.auth)
        elif method == "POST":
            resp = http.post(uri, headers=headers, data=payload, auth=self.auth)
        elif method == "PUT":
            resp = http.put(uri, headers=headers, data=payload, auth=self.auth)
        elif method == "DELETE":
            resp = http.delete(uri, headers=headers, auth=self.auth)

        if resp is None:
            return OctopusHttpResponse(), ""

        return OctopusHttpResponse(resp), resp.text

