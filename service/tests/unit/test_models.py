# from octopus.modules.es.testindex import ESTestCase
from unittest import TestCase
from service import models
from service.tests import fixtures

class TestModels(TestCase):
    def setUp(self):
        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()

    def test_01_unrouted(self):
        # just try making one from scratch
        urn = models.UnroutedNotification()

        # now try building one from a complete data structure
        source = fixtures.NotificationFactory.unrouted_notification()
        urn = models.UnroutedNotification(source)

        # just check the properties are retrievable
        assert urn.id == "1234567890"
