from octopus.modules.es.testindex import ESTestCase
from octopus.lib import http, paths
from octopus.core import app
from service.tests import fixtures
from service import api, models
from octopus.modules.store import store
import os

class MockResponse(object):
    def __init__(self, status_code):
        self.status_code = status_code

def mock_get_stream(*args, **kwargs):
    # http://example.com/pub/1/file.pdf
    # resp, content, size = http.get_stream(url, cut_off=100, chunk_size=100)
    if args[0] == "http://example.com/pub/1/file.pdf":
        return MockResponse(200), "a bunch of text", 5000

def get_stream_fail(*args, **kwargs):
    return None, "", 0

def get_stream_status(*args, **kwargs):
    return MockResponse(401), "", 6000

def get_stream_empty(*args, **kwargs):
    return MockResponse(200), "", 0

class TestAPI(ESTestCase):
    def setUp(self):
        super(TestAPI, self).setUp()
        self.old_get_stream = http.get_stream
        self.custom_zip_path = paths.rel2abs(__file__, "..", "resources", "custom.zip")
        self.store_impl = app.config.get("STORE_IMPL")
        app.config["STORE_IMPL"] = "octopus.modules.store.store.TempStore"
        self.stored_ids = []

    def tearDown(self):
        super(TestAPI, self).tearDown()
        http.get_stream = self.old_get_stream
        app.config["STORE_IMPL"] = self.store_impl
        if os.path.exists(self.custom_zip_path):
            os.remove(self.custom_zip_path)
        s = store.StoreFactory.get()
        for id in self.stored_ids:
            s.delete(id)

    def test_01_validate(self):
        # 3 different kinds of validation required

        # 1. Validation of plain metadata-only notification
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        api.JPER.validate(None, notification)

        # 2. Validation of metadata-only notification with external file links
        http.get_stream = mock_get_stream
        notification = fixtures.APIFactory.incoming()
        api.JPER.validate(None, notification)

        # 3. Validation of metadata + zip content
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        filepath = fixtures.PackageFactory.example_package_path()
        with open(filepath) as f:
            api.JPER.validate(None, notification, f)

    def test_02_validate_md_only_fail(self):
        # 1. JSON is invalid structure
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, {"random" : "content"})

        # 2. No match data present
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, {})

    def test_03_validate_md_links_fail(self):
        # 3. No url provided
        notification = fixtures.APIFactory.incoming()
        del notification["links"][0]["url"]
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, notification)

        # 4. HTTP connection failure
        notification = fixtures.APIFactory.incoming()
        http.get_stream = get_stream_fail
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, notification)

        # 5. Incorrect status code
        notification = fixtures.APIFactory.incoming()
        http.get_stream = get_stream_status
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, notification)

        # 6. Empty content
        notification = fixtures.APIFactory.incoming()
        http.get_stream = get_stream_empty
        with self.assertRaises(api.ValidationException):
            api.JPER.validate(None, notification)

    def test_04_validate_md_content_fail(self):
        # 7. No format supplied
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        del notification["content"]
        path = fixtures.PackageFactory.example_package_path()
        with open(path) as f:
            with self.assertRaises(api.ValidationException):
                api.JPER.validate(None, notification, f)

        # 8. Incorrect format supplied
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        notification["content"]["packaging_format"] = "http://some.random.url"
        path = fixtures.PackageFactory.example_package_path()
        with open(path) as f:
            with self.assertRaises(api.ValidationException):
                api.JPER.validate(None, notification, f)

        # 9. Package invald/corrupt
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, corrupt_zip=True)
        with open(self.custom_zip_path) as f:
            with self.assertRaises(api.ValidationException):
                api.JPER.validate(None, notification, f)

        # 10. No match data in either md or package
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, no_jats=True, no_epmc=True)
        with open(self.custom_zip_path) as f:
            with self.assertRaises(api.ValidationException):
                api.JPER.validate(None, {}, f)

    def test_01_create(self):
        # 2 different kinds of create mechanism

        # 1. Validation of plain metadata-only notification (with links that aren't checked)
        notification = fixtures.APIFactory.incoming()
        note = api.JPER.create_notification(None, notification)
        assert note is not None
        assert note.id is not None
        check = models.UnroutedNotification.pull(note.id)
        assert check is not None

        # 2. Validation of metadata + zip content
        notification = fixtures.APIFactory.incoming()
        del notification["links"]
        filepath = fixtures.PackageFactory.example_package_path()
        with open(filepath) as f:
            note = api.JPER.create_notification(None, notification, f)

        self.stored_ids.append(note.id)

        assert note is not None
        assert note.id is not None
        check = models.UnroutedNotification.pull(note.id)
        assert check is not None

        s = store.StoreFactory.get()
        stored = s.list(note.id)
        assert len(stored) == 3

    def test_05_create_fail(self):
        # There are only 2 circumstances under which the notification will fail

        # 1. Invalid notification metadata
        with self.assertRaises(api.ValidationException):
            note = api.JPER.create_notification(None, {"random" : "content"})

        # 2. Corrupt zip file
        notification = fixtures.APIFactory.incoming()
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, corrupt_zip=True)
        with open(self.custom_zip_path) as f:
            with self.assertRaises(api.ValidationException):
                api.JPER.validate(None, notification, f)