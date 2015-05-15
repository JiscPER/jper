from octopus.modules.es.testindex import ESTestCase
from service import models
from service.tests import fixtures
from octopus.lib import dataobj

class TestModels(ESTestCase):
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

        # check that we can write/read
        urn.save(blocking=True)

        urn2 = models.UnroutedNotification.pull("1234567890")
        assert urn2.data == urn.data

    def test_02_routed(self):
        # try making one from scratch
        rn = models.RoutedNotification()

        # try building one from a complete datastructure
        source = fixtures.NotificationFactory.routed_notification()
        rn = models.RoutedNotification(source)

        assert rn.id == "1234567890"

        # check that we can write/read
        rn.save(blocking=True)

        rn2 = models.RoutedNotification.pull("1234567890")
        assert rn2.data == rn.data

    def test_03_routing_meta(self):
        # make one from scratch
        rm = models.RoutingMetadata()

        # build one from an example document
        source = fixtures.NotificationFactory.routing_metadata()
        rm = models.RoutingMetadata(source)

        # Note: at this point we don't serialise routing metadata, it's an in-memory model only

    def test_04_repository_config(self):
        # make one from scratch
        rc = models.RepositoryConfig()

        # build one from example document
        source = fixtures.RepositoryFactory.repo_config()
        rc = models.RepositoryConfig(source)

        # check that we can write/read
        rc.save(blocking=True)

        rc2 = models.RepositoryConfig.pull(rc.id)
        assert rc2.data == rc.data

    def test_05_match_provenance(self):
        # make one from scratch
        mp = models.MatchProvenance()

        # build one from example document
        source = fixtures.RepositoryFactory.match_provenance()
        mp = models.MatchProvenance(source)

        # check that we can write/read
        mp.save(blocking=True)

        mp2 = models.MatchProvenance.pull(mp.id)
        assert mp2.data == mp.data

    def test_06_retrieval(self):
        # make one from scratch
        rr = models.RetrievalRecord()

        # build one from example document
        source = fixtures.RepositoryFactory.retreival_record()
        rr = models.RetrievalRecord(source)

        # check that we can write/read
        rr.save(blocking=True)

        rr2 = models.RetrievalRecord.pull(rr.id)
        assert rr2.data == rr.data

    def test_07_incoming_notification(self):
        # make one from scratch
        rr = models.IncomingNotification()

        # build one from example document
        source = fixtures.APIFactory.incoming()
        rr = models.IncomingNotification(source)

    def test_08_outgoing_notification(self):
        # make one from scratch
        rr = models.OutgoingNotification()

        # build one from example document
        source = fixtures.APIFactory.outgoing()
        rr = models.OutgoingNotification(source)

    def test_09_notification_list(self):
        kv = fixtures.APIFactory.notification_list_set_get()
        dataobj.test_dataobj(models.NotificationList(), kv)
