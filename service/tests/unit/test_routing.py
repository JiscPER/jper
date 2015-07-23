from octopus.modules.es.testindex import ESTestCase
# from unittest import TestCase

from service import routing, models
from service.tests import fixtures

import time

class TestPackager(ESTestCase):
    def setUp(self):
        super(TestPackager, self).setUp()

    def tearDown(self):
        super(TestPackager, self).tearDown()

    def test_01_domain_url(self):
        match_set = [
            ("ed.ac.uk", "http://www.ed.ac.uk/", True),
            ("http://www.ed.ac.uk/", "https://ed.ac.uk", True),
            ("ed.ac.uk", "ic.ac.uk", False)
        ]
        for ms in match_set:
            m = routing.domain_url(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_02_domain_email(self):
        match_set = [
            ("ed.ac.uk", "richard@ed.ac.uk", True),
            ("ic.ac.uk", "richard@phys.ic.ac.uk", True),
            ("http://www.ic.ac.uk/", "richard@ic.ac.uk", True),
            ("https://www.ic.ac.uk/physics", "richard@sci.ic.ac.uk", False)
        ]
        for ms in match_set:
            m = routing.domain_email(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_03_exact_substring(self):
        match_set = [
            ("richard", "was richard here?", True),
            ("something with  spaces ", "this is something    with spaces in it", True),
            ("this one is not", "in this one", False),
            ("this is the wrong way round", "wrong way", False),
            ("  lettERS", "VariyIng CAPITAL LeTTers  ", True)
        ]
        for ms in match_set:
            m = routing.exact_substring(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_04_exact(self):
        match_set = [
            ("richard", "richard", True),
            ("  RICHARD ", "richard   ", True),
            ("Mark", "Richard", False)
        ]
        for ms in match_set:
            m = routing.exact_substring(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_05_author_match(self):
        match_set = [
            ({"type": "orcid", "id" : "abcd"}, {"type" : "orcid", "id" : "ABCD"}, True),
            ({"type": "orcid", "id" : "abcd"}, {"type" : "orcid", "id" : "zyx"}, False),
            ({"type": "email", "id" : "abcd"}, {"type" : "orcid", "id" : "abcd"}, False),
            ({"type": "email", "id" : "richard@here"}, {"type" : "orcid", "id" : "abcd"}, False)
        ]
        for ms in match_set:
            m = routing.author_match(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_06_author_string_match(self):
        match_set = [
            ("abcd", {"type" : "orcid", "id" : "ABCD"}, True),
            ("zyx", {"type" : "email", "id" : "zyx"}, True),
            ("whatever", {"type" : "orcid", "id" : "abcd"}, False)
        ]
        for ms in match_set:
            m = routing.author_string_match(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_07_postcode_match(self):
        match_set = [
            ("HP3 9AA", "HP3 9AA", True),
            ("HP23 1BB", "hp23 1BB", True),
            ("EH10 8YY", "eh108yy", True),
            (" rh6   7PT  ", "rh67pt ", True),
            ("HP45 8IO", "eh9 7uu", False)
        ]
        for ms in match_set:
            m = routing.postcode_match(ms[0], ms[1])
            if m is False:
                assert ms[2] is False
            else:
                assert isinstance(m, basestring)
                assert len(m) > 0

    def test_50_match_success(self):
        # example routing metadata from a notification
        source = fixtures.NotificationFactory.routing_metadata()
        md = models.RoutingMetadata(source)

        # example repo config data, with the keywords and content_types removed for these tests
        # (they may be the subject of a later test)
        source2 = fixtures.RepositoryFactory.repo_config()
        del source2["keywords"]
        del source2["content_types"]
        rc = models.RepositoryConfig(source2)

        prov = models.MatchProvenance()

        m = routing.match(md, rc, prov)
        assert m is True
        assert len(prov.provenance) == 15
        check = [0] * 15

        for p in prov.provenance:
            # check that there's an explanation in all of them
            assert "explanation" in p
            assert len(p.get("explanation")) > 0    # a non-zero length string

            # run through each match that we know should have happened
            if p.get("source_field") == "domains":                          # domains
                if p.get("notification_field") == "urls":                   ## URLs
                    assert p.get("term") == "ucl.ac.uk"
                    assert p.get("matched") == "http://www.ucl.ac.uk"
                    check[0] = 1
                elif p.get("notification_field") == "emails":               ## Emails
                    assert p.get("term") == "ucl.ac.uk"
                    assert p.get("matched") == "someone@sms.ucl.ac.uk"
                    check[1] = 1

            elif p.get("source_field") == "name_variants":                  # Name Variants
                if p.get("notification_field") == "affiliations":           ## Affiliations
                    assert p.get("term") == "UCL"
                    assert p.get("matched") == "UCL"
                    check[2] = 1

            elif p.get("source_field") == "author_emails":                  # Author ID: Email
                if p.get("notification_field") == "emails":                 ## Emails
                    assert p.get("term") == "someone@sms.ucl.ac.uk"
                    assert p.get("matched") == "someone@sms.ucl.ac.uk"
                    check[3] = 1

            elif p.get("source_field") == "author_ids":                     # All Author IDs
                if p.get("notification_field") == "author_ids":             ## All Author IDs
                    assert p.get("term") in ["name: Richard Jones", "name: Mark MacGillivray", "email: someone@sms.ucl.ac.uk"]
                    assert p.get("matched") in ["name: Richard Jones", "name: Mark MacGillivray", "email: someone@sms.ucl.ac.uk"]
                    if check[4] == 0:
                        check[4] = 1
                    elif check[5] == 0:
                        check[5] = 1
                    elif check[6] == 0:
                        check[6] = 1

            elif p.get("source_field") == "postcodes":                      # Postcodes
                if p.get("notification_field") == "postcodes":              ## Postcodes
                    assert p.get("term") == "SW1 0AA"
                    assert p.get("matched") == "SW1 0AA"
                    check[7] = 1

            elif p.get("source_field") == "grants":                         # Grants
                if p.get("notification_field") == "grants":                 ## Grants
                    assert p.get("term") == "BB/34/juwef"
                    assert p.get("matched") == "BB/34/juwef"
                    check[8] = 1

            elif p.get("source_field") == "strings":                        # Strings
                if p.get("notification_field") == "urls":                   ## URLs
                    assert p.get("term") == "https://www.ed.ac.uk/"
                    assert p.get("matched") == "http://www.ed.ac.uk"
                    check[9] = 1

                elif p.get("notification_field") == "emails":               ## Emails
                    assert p.get("term") == "richard@EXAMPLE.com"
                    assert p.get("matched") == "richard@example.com"
                    check[10] = 1

                elif p.get("notification_field") == "affiliations":         ## Affiliations
                    assert p.get("term") == "cottage labs"
                    assert p.get("matched") == "Cottage Labs"
                    check[11] = 1

                elif p.get("notification_field") == "author_ids":           ## All Author IDs
                    assert p.get("term") == "AAAA-0000-1111-BBBB"
                    assert p.get("matched") == "orcid: aaaa-0000-1111-bbbb"
                    check[12] = 1

                elif p.get("notification_field") == "postcodes":            ## Postcodes
                    assert p.get("term") == "eh235tz"
                    assert p.get("matched") == "EH23 5TZ"
                    check[13] = 1

                elif p.get("notification_field") == "grants":               ## Grants
                    assert p.get("term") == "bb/34/juwef"
                    assert p.get("matched") == "BB/34/juwef"
                    check[14] = 1

        assert 0 not in check

    def test_51_match_fail(self):
        pass

    def test_98_routing_success(self):
        # add a repository config to the index
        source = fixtures.RepositoryFactory.repo_config()
        del source["keywords"]
        del source["content_types"]
        rc = models.RepositoryConfig(source)
        rc.save(blocking=True)

        # get an unrouted notification
        source2 = fixtures.NotificationFactory.unrouted_notification()
        urn = models.UnroutedNotification(source2)

        # now run the routing algorithm
        routing.route(urn)

        # NOTE: at the moment this test can't pass, as URLs are not extracted from
        # the metadata

        # give the index a chance to catch up before checking the results
        time.sleep(2)

        # check that a match provenance was recorded
        mps = models.MatchProvenance.pull_by_notification(urn.id)
        assert len(mps) == 1
        # FIXME: what else do we need to check for here?

        # check that a routed notification was created
        rn = models.RoutedNotification.pull(urn.id)
        assert rn is not None
        # FIXME: what else do we need to check for here?

    def test_99_routing_fail(self):
        pass