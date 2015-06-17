from octopus.modules.es.testindex import ESTestCase
from octopus.lib import http
from service.tests import fixtures
from service import api

class MockResponse(object):
    def __init__(self, status_code):
        self.status_code = status_code

def mock_get_stream(*args, **kwargs):
    # http://example.com/pub/1/file.pdf
    # resp, content, size = http.get_stream(url, cut_off=100, chunk_size=100)
    if args[0] == "http://example.com/pub/1/file.pdf":
        return MockResponse(200), "a bunch of text", 5000

class TestAPI(ESTestCase):
    def setUp(self):
        super(TestAPI, self).setUp()
        self.old_get_stream = http.get_stream

    def tearDown(self):
        super(TestAPI, self).tearDown()
        http.get_stream = self.old_get_stream

    def test_01_validate(self):
        # 3 different kinds of validation requires

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

        # 5. Incorrect status code

        # 6. Empty content
        pass

    def test_04_validate_md_content_fail(self):
        # 7. No format supplied

        # 8. Incorrect format supplied

        # 9. Package invald/corrupt

        # 10. No match data in either md or package
        pass