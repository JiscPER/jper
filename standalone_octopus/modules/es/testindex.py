from unittest import TestCase
from standalone_octopus.core import app, initialise
import time, esprit

# switch out the live index for the test index
app.config['ELASTIC_SEARCH_INDEX'] = app.config['ELASTIC_SEARCH_TEST_INDEX']

# if a test on a previous run has totally failed and tearDown has not run, then make sure the index is gone first
TEST_CONN = esprit.raw.Connection(app.config.get('ELASTIC_SEARCH_HOST'), app.config.get('ELASTIC_SEARCH_INDEX'))
esprit.raw.delete(TEST_CONN)
time.sleep(1)

class ESTestCase(TestCase):
    def setUp(self):
        initialise()
        time.sleep(1)

    def tearDown(self):
        esprit.raw.delete(TEST_CONN)
        time.sleep(1)