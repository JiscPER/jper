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

    def test_02_routed(self):
        # try making one from scratch
        rn = models.RoutedNotification()

        # try building one from a complete datastructure
        source = fixtures.NotificationFactory.routed_notification()
        rn = models.RoutedNotification(source)

        assert rn.id == "1234567890"

    def test_03_routing_meta(self):
        # make one from scratch
        rm = models.RoutingMetadata()

        # build one from an example document
        source = fixtures.NotificationFactory.routing_metadata()
        rm = models.RoutingMetadata(source)

    def test_04_repository_config(self):
        # make one from scratch
        rc = models.RepositoryConfig()

        # build one from example document
        source = fixtures.RepositoryFactory.repo_config()
        rc = models.RepositoryConfig(source)

    def test_05_match_provenance(self):
        # make one from scratch
        mp = models.MatchProvenance()

        # build one from example document
        source = fixtures.RepositoryFactory.match_provenance()
        mp = models.MatchProvenance(source)

    def test_06_retrieval(self):
        # make one from scratch
        mp = models.RetrievalRecord()

        # build one from example document
        source = fixtures.RepositoryFactory.retreival_record()
        mp = models.RetrievalRecord(source)
