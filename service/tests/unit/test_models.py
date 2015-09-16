from octopus.modules.es.testindex import ESTestCase
from octopus.core import app
from service import models
from service.tests import fixtures
from octopus.lib import dataobj

class TestModels(ESTestCase):
    def setUp(self):
        self.run_schedule = app.config.get("RUN_SCHEDULE")
        app.config["RUN_SCHEDULE"] = False

        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()
        app.config["RUN_SCHEDULE"] = self.run_schedule

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

        # request an unrouted notification
        ur = rr.make_unrouted()
        assert isinstance(ur, models.UnroutedNotification)
        assert ur.data == rr.data

    def test_08_outgoing_notification(self):
        # make one from scratch
        rr = models.OutgoingNotification()

        # build one from example document
        source = fixtures.APIFactory.outgoing()
        rr = models.OutgoingNotification(source)

    def test_09_provider_outgoing_notification(self):
        # make one from scratch
        rr = models.ProviderOutgoingNotification()

        # build one from example document
        source = fixtures.APIFactory.outgoing(provider=True)
        rr = models.ProviderOutgoingNotification(source)

    def test_10_notification_list(self):
        kv = fixtures.APIFactory.notification_list_set_get()
        dataobj.test_dataobj(models.NotificationList(), kv)

    def test_11_unrouted_outgoing(self):
        # create an unrouted notification to work with
        source = fixtures.NotificationFactory.unrouted_notification()
        urn = models.UnroutedNotification(source)
        urn.save(blocking=True)

        # get an ordinary outgoing notification
        out = urn.make_outgoing()
        assert isinstance(out, models.OutgoingNotification)
        assert len(out.links) == 0

        # get the provider's outgoing notification
        out2 = urn.make_outgoing(provider=True)
        assert isinstance(out2, models.ProviderOutgoingNotification)
        assert len(out2.links) == 2

    def test_12_routed_outgoing(self):
        # create an unrouted notification to work with
        source = fixtures.NotificationFactory.routed_notification()
        rn = models.RoutedNotification(source)
        rn.save(blocking=True)

        # get an ordinary outgoing notification
        out = rn.make_outgoing()
        assert isinstance(out, models.OutgoingNotification)
        assert len(out.links) == 1

        # get the provider's outgoing notification
        out2 = rn.make_outgoing(provider=True)
        assert isinstance(out2, models.ProviderOutgoingNotification)
        assert len(out2.links) == 3

    def test_13_unrouted_match_data(self):
        source = fixtures.NotificationFactory.unrouted_notification()
        urn = models.UnroutedNotification(source)
        md = urn.match_data()

        assert len(md.urls) == 0
        assert len(md.emails) == 2
        assert "richard@example.com" in md.emails
        assert "mark@example.com" in md.emails
        assert len(md.affiliations) == 2
        assert "Cottage Labs, HP3 9AA" in md.affiliations
        assert "Cottage Labs, EH9 5TP" in md.affiliations
        assert len(md.get_author_ids()) == 6
        assert "richard@example.com" in [aid.get("id") for aid in md.get_author_ids("email")]
        assert "mark@example.com" in [aid.get("id") for aid in md.get_author_ids("email")]
        assert "aaaa-0000-1111-bbbb" in [aid.get("id") for aid in md.get_author_ids("orcid")]
        assert "dddd-2222-3333-cccc" in [aid.get("id") for aid in md.get_author_ids("orcid")]
        assert "Richard Jones" in [aid.get("id") for aid in md.get_author_ids("name")]
        assert "Mark MacGillivray" in [aid.get("id") for aid in md.get_author_ids("name")]
        assert len(md.keywords) == 4
        assert "science" in md.keywords
        assert "technology" in md.keywords
        assert "arts" in md.keywords
        assert "medicine" in md.keywords
        assert len(md.content_types) == 1
        assert "article" in md.content_types
        assert len(md.postcodes) == 2
        assert "HP3 9AA" in md.postcodes
        assert "EH9 5TP" in md.postcodes

    def test_14_match_merge(self):
        source1 = fixtures.NotificationFactory.routing_metadata()
        rm1 = models.RoutingMetadata(source1)

        source2 = fixtures.NotificationFactory.unrouted_notification()
        urn = models.UnroutedNotification(source2)
        rm2 = urn.match_data()

        rm1.merge(rm2)

        assert len(rm1.urls) == 2
        assert "http://www.ed.ac.uk" in rm1.urls
        assert "http://www.ucl.ac.uk" in rm1.urls
        assert len(rm1.emails) == 3
        assert "richard@example.com" in rm1.emails
        assert "mark@example.com" in rm1.emails
        assert "someone@sms.ucl.ac.uk" in rm1.emails
        assert len(rm1.affiliations) == 5
        assert "Cottage Labs" in rm1.affiliations
        assert "Edinburgh Univerisity" in rm1.affiliations
        assert "UCL" in rm1.affiliations
        assert "Cottage Labs, HP3 9AA" in rm1.affiliations
        assert "Cottage Labs, EH9 5TP" in rm1.affiliations
        assert len(rm1.get_author_ids()) == 7
        assert "richard@example.com" in [aid.get("id") for aid in rm1.get_author_ids("email")]
        assert "mark@example.com" in [aid.get("id") for aid in rm1.get_author_ids("email")]
        assert "aaaa-0000-1111-bbbb" in [aid.get("id") for aid in rm1.get_author_ids("orcid")]
        assert "dddd-2222-3333-cccc" in [aid.get("id") for aid in rm1.get_author_ids("orcid")]
        assert "Richard Jones" in [aid.get("id") for aid in rm1.get_author_ids("name")]
        assert "Mark MacGillivray" in [aid.get("id") for aid in rm1.get_author_ids("name")]
        assert "someone@sms.ucl.ac.uk" in [aid.get("id") for aid in rm1.get_author_ids("email")]
        assert len(rm1.keywords) == 4
        assert "science" in rm1.keywords
        assert "technology" in rm1.keywords
        assert "arts" in rm1.keywords
        assert "medicine" in rm1.keywords
        assert len(rm1.content_types) == 1
        assert "article" in rm1.content_types
        assert len(rm1.postcodes) == 4
        for c in ["HP3 9AA", "EH9 5TP", "SW1 0AA", "EH23 5TZ"]:
            assert c in rm1.postcodes




