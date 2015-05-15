import requests, json, os

from octopus.modules.es.testindex import ESTestCase
from octopus.modules.test.helpers import get_first_free_port, TestServer, make_test_config
from service.tests import fixtures
from octopus.core import app
from service import web
from octopus.lib import paths

API_KEY = "1234567890"

class TestAPI(ESTestCase):
    def setUp(self):
        super(TestAPI, self).setUp()
        self.config = {
            "PORT" : get_first_free_port(),
            "ELASTIC_SEARCH_INDEX" : app.config['ELASTIC_SEARCH_INDEX']
        }
        self.cfg_file = paths.rel2abs(__file__, "..", "resources", "test-server.cfg")

        make_test_config(self.config, self.cfg_file)
        self.test_server = TestServer(port=None, index=None, python_app_module_path=os.path.abspath(web.__file__), cfg_file=self.cfg_file)
        self.test_server.spawn_with_config()

        self.appurl = "http://localhost:{x}".format(x=self.config["PORT"])
        self.api_base = self.appurl + "/api/v1/"

    def tearDown(self):
        super(TestAPI, self).tearDown()
        self.test_server.terminate()
        os.remove(self.cfg_file)

    def test_01_validation_singlepart(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "validate?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 204

    def test_02_validation_multipart(self):
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "validate?api_key=" + API_KEY
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 204

    def test_03_validation_fail(self):
        # ways in which the validation http request can fail
        # 1. invalid/wrong auth credentials
        # 2. incorrect content-type header on metadata/content parts
        # 3. invalid json
        pass

    def test_04_notification_singlepart(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 202

    def test_05_notification_multipart(self):
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = self.api_base + "notification?api_key=" + API_KEY
        files = [
            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
            ("content", ("content.zip", open(example_package, "rb"), "application/zip"))
        ]
        resp = requests.post(url, files=files)
        assert resp.status_code == 202

    def test_06_notification_fail(self):
        # ways in which the notification http request can fail
        # 1. invalid/wrong auth credentials
        # 2. incorrect content-type header on metadata/content parts
        # 3. invalid json
        pass

    def test_07_get_notification(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        url = resp.headers["location"]
        resp2 = requests.get(url)
        assert resp2.status_code == 200

    def test_08_get_notification_fail(self):
        # ways in which the notification http request can fail
        # 1. invalid/wrong auth credentials
        # 2. invalid/not found notification id
        pass

    def test_09_get_store_content(self):
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
        assert resp2.status_code == 303

    def test_10_get_store_content(self):
        # ways in which the content http request can fail
        # 1. invalid/wrong auth credentials
        # 2. invalid/not found notification id
        pass

    def test_11_get_public_content(self):
        notification = fixtures.APIFactory.incoming()
        url = self.api_base + "notification?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        loc = resp.headers["location"]
        resp2 = requests.get(loc + "/content/1?api_key=" + API_KEY, allow_redirects=False)
        assert resp2.status_code == 303

    def test_12_get_public_content(self):
        # ways in which the content http request can fail
        # 1. invalid/wrong auth credentials
        # 2. invalid/not found notification id
        pass

    def test_13_list_all(self):
        url = self.api_base + "routed?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z"
        resp = requests.get(url)
        assert resp.status_code == 200

    def test_14_list_all_fail(self):
        # ways in which the list all http request can fail
        # 1. invalid/wrong auth credentials (if supplied)
        # 2. since parameter not supplied
        # 3. since parameter wrongly formatted
        # 4. page/pageSize parameters wrongly formatted

        pass

    def test_15_list_repository(self):
        url = self.api_base + "routed/repo1?api_key=" + API_KEY + "&since=2001-01-01T00:00:00Z"
        resp = requests.get(url)
        assert resp.status_code == 200

    def test_16_list_repository_fail(self):
        # ways in which the list all http request can fail
        # 1. invalid/wrong auth credentials (if supplied)
        # 2. since parameter not supplied
        # 3. since parameter wrongly formatted
        # 4. page/pageSize parameters wrongly formatted

        pass