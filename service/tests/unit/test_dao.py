from octopus.modules.es.testindex import ESTestCase
from service import dao
from service.tests import fixtures
from octopus.lib import dataobj
from datetime import datetime
from octopus.core import app
import esprit, time

ESV = app.config.get("ELASTIC_SEARCH_VERSION", "1.4.2")

class TestDAO(ESTestCase):
    def setUp(self):
        self.run_schedule = app.config.get("RUN_SCHEDULE")
        app.config["RUN_SCHEDULE"] = False

        super(TestDAO, self).setUp()

        # self.unrouted_timebox = app.config["ESDAO_TIME_BOX_UNROUTED"]
        # self.unrouted_lookback = app.config["ESDAO_TIME_BOX_LOOKBACK_UNROUTED"]

    def tearDown(self):
        super(TestDAO, self).tearDown()
        #app.config["ESDAO_TIME_BOX_UNROUTED"] = self.unrouted_timebox
        #app.config["ESDAO_TIME_BOX_LOOKBACK_UNROUTED"] = self.unrouted_lookback
        app.config["RUN_SCHEDULE"] = self.run_schedule

    def test_01_unrouted(self):
        # give the dao object a general workout
        d = dao.UnroutedNotificationDAO()
        d.save()
        m = d.mappings()
        e = d.example()

        assert isinstance(e, dao.UnroutedNotificationDAO)

        # leaving these assertions in (albeit modified), but we've backed out on time-boxing the unrouted DAO now

        wt = d.get_write_type()
        assert wt.startswith("unrouted")
        # assert wt.endswith(datetime.utcnow().strftime("%Y%m"))

        rts = d.get_read_types()
        assert len(rts) == 1
        for rt in rts:
            assert rt.startswith("unrouted")

    """
    This test is no longer valid, but leaving it in for future reference.
    Unrouted notifications are no longer stored in a time-boxed type

    def test_02_unrouted_timebox(self):
        # set some testable config values
        app.config["ESDAO_TIME_BOX_UNROUTED"] = "second"
        app.config["ESDAO_TIME_BOX_LOOKBACK_UNROUTED"] = 6

        # Note - there is a chance that this test will fail, if the calls to get_write_type and save fall
        # over the boundary of a second.  If this becomes a problem then we should have something which
        # checks the milliseconds, and sleeps until we're at the start of the next second before proceeding

        # create two notifications, far enough apart that they should
        # be written to separate index types
        d1 = dao.UnroutedNotificationDAO()
        w1 = d1.get_write_type()
        d1.save()

        time.sleep(2)

        d2 = dao.UnroutedNotificationDAO()
        w2 = d2.get_write_type()
        d2.save()

        # give the indices time to refresh (note we can't use a blocking save in a timeboxed type)
        time.sleep(2)

        # check that we have different write types, and that they both resolve to indices
        assert w1 != w2
        assert esprit.raw.type_exists(d2.__conn__, w1, es_version=ESV)
        assert esprit.raw.type_exists(d2.__conn__, w2, es_version=ESV)

        # get the read types, and check that the write types appear in them
        rts = d2.get_read_types()
        assert len(rts) == 7
        assert w1 in rts
        assert w2 in rts

        # execute a search over the read types, and check that we get both our
        # objects back
        resp = esprit.raw.search(d2.__conn__, rts)
        res = esprit.raw.unpack_result(resp)
        assert len(res) == 2

        # now ensure that we can also pull both of our objects
        d3 = dao.UnroutedNotificationDAO.pull(d1.id)
        d4 = dao.UnroutedNotificationDAO.pull(d2.id)

        assert d3 is not None
        assert d4 is not None
    """

    def test_03_routed(self):
        # give the dao object a general workout
        d = dao.RoutedNotificationDAO()
        d.save()
        m = d.mappings()
        e = d.example()

        assert isinstance(e, dao.RoutedNotificationDAO)

        wt = d.get_write_type()
        assert wt.startswith("routed")
        assert wt.endswith(datetime.utcnow().strftime("%Y%m"))

        rts = d.get_read_types()
        assert len(rts) == 4
        for rt in rts:
            assert rt.startswith("routed")

    def test_04_routed_timebox(self):
        # set some testable config values
        app.config["ESDAO_TIME_BOX_ROUTED"] = "second"
        app.config["ESDAO_TIME_BOX_LOOKBACK_ROUTED"] = 6

        # Note - there is a chance that this test will fail, if the calls to get_write_type and save fall
        # over the boundary of a second.  If this becomes a problem then we should have something which
        # checks the milliseconds, and sleeps until we're at the start of the next second before proceeding

        # create two notifications, far enough apart that they should
        # be written to separate index types
        d1 = dao.RoutedNotificationDAO()
        w1 = d1.get_write_type()
        d1.save()

        time.sleep(2)

        d2 = dao.RoutedNotificationDAO()
        w2 = d2.get_write_type()
        d2.save()

        # give the indices time to refresh (note we can't use a blocking save in a timeboxed type)
        time.sleep(2)

        # check that we have different write types, and that they both resolve to indices
        assert w1 != w2
        assert esprit.raw.type_exists(d2.__conn__, w1, es_version=ESV)
        assert esprit.raw.type_exists(d2.__conn__, w2, es_version=ESV)

        # get the read types, and check that the write types appear in them
        rts = d2.get_read_types()
        assert len(rts) == 7
        assert w1 in rts
        assert w2 in rts

        # execute a search over the read types, and check that we get both our
        # objects back
        resp = esprit.raw.search(d2.__conn__, rts)
        res = esprit.raw.unpack_result(resp)
        assert len(res) == 2

        # now ensure that we can also pull both of our objects
        d3 = dao.RoutedNotificationDAO.pull(d1.id)
        d4 = dao.RoutedNotificationDAO.pull(d2.id)

        assert d3 is not None
        assert d4 is not None

    def test_05_repo_config(self):
        # give the dao object a general workout
        d = dao.RepositoryConfigDAO()
        d.save()
        m = d.mappings()
        e = d.example()

        assert isinstance(e, dao.RepositoryConfigDAO)

        wt = d.get_write_type()
        assert wt == "repo_config"

        rts = d.get_read_types()
        assert len(rts) == 1
        assert "repo_config" in rts

    def test_06_match_prov(self):
        # give the dao object a general workout
        d = dao.MatchProvenanceDAO()
        d.save()
        m = d.mappings()
        e = d.example()

        assert isinstance(e, dao.MatchProvenanceDAO)

        wt = d.get_write_type()
        assert wt == "match_prov"

        rts = d.get_read_types()
        assert len(rts) == 1
        assert "match_prov" in rts

    def test_07_retrieval(self):
        # give the dao object a general workout
        d = dao.RetrievalRecordDAO()
        d.save()
        m = d.mappings()
        e = d.example()

        assert isinstance(e, dao.RetrievalRecordDAO)

        wt = d.get_write_type()
        assert wt == "retrieval"

        rts = d.get_read_types()
        assert len(rts) == 1
        assert "retrieval" in rts

