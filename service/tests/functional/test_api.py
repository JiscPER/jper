from unittest import TestCase
import requests, json, os

# from octopus.modules.es.testindex import ESTestCase
from service import models
from service.tests import fixtures

API_BASE = "http://localhost:5024/api/v1/"
API_KEY = "1234567890"

class TestModels(TestCase):
    def setUp(self):
        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()

    def test_01_validation_singlepart(self):
        notification = fixtures.APIFactory.incoming()
        url = API_BASE + "validate?api_key=" + API_KEY
        resp = requests.post(url, data=json.dumps(notification), headers={"Content-Type" : "application/json"})
        assert resp.status_code == 204

    def test_02_validation_multipart(self):
        notification = fixtures.APIFactory.incoming()
        example_package = fixtures.APIFactory.example_package_path()
        url = API_BASE + "validate?api_key=" + API_KEY
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