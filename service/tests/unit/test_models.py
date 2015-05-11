# from octopus.modules.es.testindex import ESTestCase
from unittest import TestCase
from service import models

class TestModels(TestCase):
    def setUp(self):
        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()

    def test_01_unrouted(self):
        n = models.RoutedNotification()