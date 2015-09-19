import requests, json, os

from octopus.modules.es.testindex import ESTestCase
from octopus.modules.test.helpers import get_first_free_port, TestServer, make_config
from service.tests import fixtures
from octopus.core import app
from service import web
from octopus.lib import paths
from octopus.modules.store import store

# FIXME: at this point these don't do anything.  We'll need to create user accounts
# in the remote system and get their api keys.
API_KEY = "admin"   # this is the password for the account, not the api-key, so it won't work
INVALID_API_KEY = "abcdefg"

class TestAPI(ESTestCase):
    def setUp(self):
        super(TestAPI, self).setUp()
        self.config = {
            "PORT" : get_first_free_port(),
            "ELASTIC_SEARCH_INDEX" : app.config['ELASTIC_SEARCH_INDEX'],
            "THREADED" : True,
            "FUNCTIONAL_TEST_MODE" : True,
            "STORE_IMPL" : "octopus.modules.store.store.TempStore",
            "RUN_SCHEDULE": False
        }
        self.cfg_file = paths.rel2abs(__file__, "..", "resources", "test-server.cfg")

        make_config(self.config, self.cfg_file)
        self.test_server = TestServer(port=None, index=None, python_app_module_path=os.path.abspath(web.__file__), cfg_file=self.cfg_file)
        self.test_server.spawn_with_config()

        self.appurl = "http://localhost:{x}".format(x=self.config["PORT"])
        self.api_base = self.appurl + "/api/v1/"

        self.custom_zip_path = paths.rel2abs(__file__, "..", "resources", "custom.zip")

    def tearDown(self):
        super(TestAPI, self).tearDown()
        self.test_server.terminate()
        os.remove(self.cfg_file)
        # this is the temp store where we told the server to put the files
        s = store.StoreFactory.tmp()
        for cid in s.list_container_ids():
            s.delete(cid)
        if os.path.exists(self.custom_zip_path):
            os.remove(self.custom_zip_path)

    def test_01_validation_singlepart(self):
        notification = fixtures.APIFactory.incoming()
        notification["links"][0]["url"] = self.appurl + "/test/download/file.pdf"
        url = self.api_base + "validate?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 204

    def test_02_validation_singlepart_fail(self):
        # ways in which the validation http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't do this test yet

        # 2. incorrect content-type header
        notification = fixtures.APIFactory.incoming()
        notification["links"][0]["url"] = self.appurl + "/test/download/file.pdf"
        url = self.api_base + "validate?api_key=" + API_KEY

        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "text/plain"})
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/json" in j["error"]

        # 3. invalid json
        resp = requests.post(url, data="this is not json", headers={"Content-Type" : "application/json"})
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Unable to parse" in j["error"]

    def test_03_validation_multipart(self):
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "validate?api_key=" + API_KEY
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 204

    def test_04_validation_multipart_fail(self):
        # ways in which the validation http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't do this test yet

        # 2. incorrect content-type header on metadata/content parts
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "validate?api_key=" + API_KEY

        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "text/plain")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/json" in j["error"]

        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "text/plain"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/zip" in j["error"]

        # 3. invalid json
        files = [
            ("metadata", ("metadata.json", "this string is not json", "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "text/plain"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Unable to parse" in j["error"]

    def test_05_notification_singlepart(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 202
        j = resp.json()
        assert "status" in j
        assert j["status"] == "accepted"
        assert "id" in j
        assert "location" in j
        assert "location" in resp.headers
        assert resp.headers["location"] == j["location"], (resp.headers["location"], j["location"])

    def test_06_notification_singlepart_fail(self):
        # ways in which the validation http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't do this test yet

        # 2. incorrect content-type header
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY

        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "text/plain"})
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/json" in j["error"]

        # 3. invalid json
        resp = requests.post(url, data="this is not json", headers={"Content-Type" : "application/json"})
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Unable to parse" in j["error"]

        # 4. incorrectly structured json
        obj = {"random" : "content"}
        resp = requests.post(url, data=json.dumps(obj), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Field 'random' is not permitted at 'root'" in j["error"]

    def test_07_notification_multipart(self):
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "notification?api_key=" + API_KEY
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 202
        j = resp.json()
        assert "status" in j
        assert j["status"] == "accepted"
        assert "id" in j
        assert "location" in j
        assert "location" in resp.headers
        assert resp.headers["location"] == j["location"], (resp.headers["location"], j["location"])

    def test_08_notification_multipart_fail(self):
        # ways in which the notification http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't do this test yet

        # 2. incorrect content-type header on metadata/content parts
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "notification?api_key=" + API_KEY

        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "text/plain")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/json" in j["error"]

        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "text/plain"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "application/zip" in j["error"]

        # 3. invalid json
        files = [
            ("metadata", ("metadata.json", "this string is not json", "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "text/plain"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Unable to parse" in j["error"]

        # 4. validation exception on the content
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, corrupt_zip=True)
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(self.custom_zip_path, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 400
        j = resp.json()
        assert "error" in j
        assert "Zip file is corrupt" in j["error"]

    def test_09_get_notification(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY

        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        url = resp.headers["location"]
        j = resp.json()

        resp2 = requests.get(url + '?api_key=' + API_KEY)
        assert resp2.status_code == 200
        assert resp2.headers["content-type"] == "application/json"
        j2 = resp2.json()
        assert j2["id"] == j["id"]
        assert j2["provider"]["id"] == "admin"  # The default admin account owns this one

        # FIXME: should do additional tests for retrieving routed notifications, but this is
        # difficult to do at this stage

    def test_10_get_notification_fail(self):
        # ways in which the notification http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't test for this yet

        # 2. invalid/not found notification id
        url = self.api_base + "notification/2394120938412098348901275812u?api_key=" + API_KEY
        resp = requests.get(url)
        assert resp.status_code == 404

    def test_11_get_store_content(self):
        """
        FIXME: this test is no longer accurate, as the store does not redirect.  Needs updating.
        :return:
        """
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "notification?api_key=" + API_KEY
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        loc = resp.headers["location"]
        resp2 = requests.get(loc + "/content?api_key=" + API_KEY, allow_redirects=False)
        assert resp2.status_code == 303, resp2.status_code

    def test_12_get_store_content_fail(self):
        # ways in which the content http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't test for this yet

        # 2. invalid/not found notification id
        url = self.api_base + "notification/2394120938412098348901275812u/content?api_key=" + API_KEY
        resp = requests.get(url)
        assert resp.status_code == 404

    def test_13_get_public_content(self):
        """
        FIXME: this test is no longer accurate.  Needs updating.
        :return:
        """
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        loc = resp.headers["location"]
        resp2 = requests.get(loc + "/content/1?api_key=" + API_KEY, allow_redirects=False)
        assert resp2.status_code == 303

    def test_14_get_public_content_fail(self):
        # ways in which the content http request can fail
        # 1. invalid/wrong auth credentials
        # FIXME: we can't test for this yet

        # 2. invalid/not found notification id
        url = self.api_base + "notification/2394120938412098348901275812u/content/1?api_key=" + API_KEY
        resp = requests.get(url)
        assert resp.status_code == 404

    def test_15_list_all(self):
        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z"
        resp = requests.get(url)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert j["since"] == "2001-01-01T00:00:00Z"
        assert j["page"] == 1
        assert j["pageSize"] == 25
        assert "timestamp" in j
        assert "total" in j
        assert "notifications" in j

    def test_16_list_all_fail(self):
        # ways in which the list all http request can fail
        # 1. invalid/wrong auth credentials (if supplied)
        # FIXME: we can't test for this yet

        # 2. since parameter not supplied
        url = self.api_base + "routed?api_key=" + API_KEY
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "since" in j["error"]

        # 3. since parameter wrongly formatted
        url = self.api_base + "routed?api_key=" + API_KEY + "&since=wednesday"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "since" in j["error"]

        # 4. page/pageSize parameters wrongly formatted
        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=0&pageSize=25"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page" in j["error"]

        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=first&pageSize=25"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page" in j["error"]

        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=1&pageSize=10000000"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page size" in j["error"]

        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=1&pageSize=loads"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "pageSize" in j["error"]

    def test_17_list_repository(self):
        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=2&pageSize=67"
        resp = requests.get(url)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert j["since"] == "2001-01-01T00:00:00Z"
        assert j["page"] == 2
        assert j["pageSize"] == 67
        assert "timestamp" in j
        assert "total" in j
        assert "notifications" in j

    def test_18_list_repository_fail(self):
        # ways in which the list repository http request can fail
        # 1. invalid/wrong auth credentials (if supplied)
        # FIXME: we can't test for this yet

        # 2. since parameter not supplied
        url = self.api_base + "routed/repo1?api_key=" + API_KEY
        resp = requests.get(url)
        assert resp.status_code == 400, resp.status_code
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "since" in j["error"]

        # 3. since parameter wrongly formatted
        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=wednesday"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "since" in j["error"]

        # 4. page/pageSize parameters wrongly formatted
        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=0&pageSize=25"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page" in j["error"]

        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=first&pageSize=25"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page" in j["error"]

        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=1&pageSize=10000000"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "page size" in j["error"]

        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z&page=1&pageSize=loads"
        resp = requests.get(url)
        assert resp.status_code == 400
        assert resp.headers["content-type"] == "application/json"
        j = resp.json()
        assert "error" in j
        assert "pageSize" in j["error"]