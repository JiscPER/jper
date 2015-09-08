# coding=utf-8

# from octopus.modules.es.testindex import ESTestCase
from unittest import TestCase
from service import packages
from octopus.modules.store import store
from copy import deepcopy

from service.tests import fixtures
from octopus.core import app
from lxml import etree
from octopus.lib import paths
import os

PACKAGE = "http://router.jisc.ac.uk/packages/FilesAndJATS"
TEST_FORMAT = "http://router.jisc.ac.uk/packages/OtherTestFormat"
SIMPLE_ZIP = "http://purl.org/net/sword/package/SimpleZip"
TEST_HANDLER = "service.tests.fixtures.TestPackageHandler"
STORE_ID = "12345"

class TestPackager(TestCase):
    def setUp(self):
        self.run_schedule = app.config.get("RUN_SCHEDULE")
        app.config["RUN_SCHEDULE"] = False

        self.old_ph = deepcopy(app.config["PACKAGE_HANDLERS"])
        app.config["PACKAGE_HANDLERS"].update({TEST_FORMAT : TEST_HANDLER})

        self.old_store = app.config["STORE_IMPL"]
        app.config["STORE_IMPL"] = "octopus.modules.store.store.StoreLocal"

        super(TestPackager, self).setUp()

        self.custom_zip_path = paths.rel2abs(__file__, "..", "resources", "custom.zip")

    def tearDown(self):
        super(TestPackager, self).tearDown()
        app.config["PACKAGE_HANDLERS"] = self.old_ph
        app.config["STORE_IMPL"] = self.old_store
        app.config["RUN_SCHEDULE"] = self.run_schedule

        if os.path.exists(self.custom_zip_path):
            os.remove(self.custom_zip_path)

        sm = store.StoreFactory.get()
        sm.delete(STORE_ID)

    def test_01_factory(self):
        # try loading incoming packages
        inst = packages.PackageFactory.incoming(PACKAGE)
        assert isinstance(inst, packages.FilesAndJATS)

        inst = packages.PackageFactory.incoming(TEST_FORMAT)
        assert isinstance(inst, fixtures.TestPackageHandler)

        # try loading converter packages
        inst = packages.PackageFactory.converter(PACKAGE)
        assert isinstance(inst, packages.FilesAndJATS)

        inst = packages.PackageFactory.converter(TEST_FORMAT)
        assert isinstance(inst, fixtures.TestPackageHandler)

    def test_02_valid_zip(self):
        # first construct the packager around the zip
        zip_path = fixtures.PackageFactory.example_package_path()
        inst = packages.PackageFactory.incoming(PACKAGE, zip_path=zip_path)

        # now check the properties are initialised as we would expect
        assert inst.zip_path == zip_path
        assert inst.zip is not None
        assert inst.jats is not None
        assert inst.epmc is not None

        # now see if we can extract the metadata streams
        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
            xml = etree.fromstring(stream.read())
            if name == "filesandjats_jats.xml":
                assert xml.tag == "article"
            elif name == "filesandjats_epmc.xml":
                assert xml.tag == "result"

        assert "filesandjats_jats.xml" in names
        assert "filesandjats_epmc.xml" in names

        # now try doing the same but with zips that only contain one of the relevant
        # metadata files (which would still be valid)

        # first a zip that just contains the jats (no epmc)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, no_epmc=True)
        inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)

        assert inst.zip_path == self.custom_zip_path
        assert inst.zip is not None
        assert inst.jats is not None
        assert inst.epmc is None

        # now see if we can extract the metadata streams
        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
        assert len(names) == 1
        assert "filesandjats_jats.xml" in names

        # now a zip that just contains the epmc (no jats)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, no_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)

        assert inst.zip_path == self.custom_zip_path
        assert inst.zip is not None
        assert inst.jats is None
        assert inst.epmc is not None

        # now see if we can extract the metadata streams
        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
        assert len(names) == 1
        assert "filesandjats_epmc.xml" in names

    def test_03_invalid_zip(self):
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, corrupt_zip=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)
            except packages.PackageException as e:
                assert e.message == "Zip file is corrupt - cannot read."
                raise e

        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, no_epmc=True, no_jats=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)
            except packages.PackageException as e:
                assert e.message == "No JATS fulltext or EPMC metadata found in package"
                raise e

        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, invalid_epmc=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)
            except packages.PackageException as e:
                assert e.message.startswith("Unable to parse XML file in package")
                raise e

        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, invalid_jats=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, zip_path=self.custom_zip_path)
            except packages.PackageException as e:
                assert e.message.startswith("Unable to parse XML file in package")
                raise e

    def test_04_valid_file_handles(self):
        handles = fixtures.PackageFactory.file_handles()
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)

        # now check the properties are initialised as we would expect
        assert inst.zip_path is None
        assert inst.zip is None
        assert inst.jats is not None
        assert inst.epmc is not None

        # now see if we can extract the metadata streams
        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
            xml = etree.fromstring(stream.read())
            if name == "filesandjats_jats.xml":
                assert xml.tag == "article"
            elif name == "filesandjats_epmc.xml":
                assert xml.tag == "result"

        assert "filesandjats_jats.xml" in names
        assert "filesandjats_epmc.xml" in names

        # now do the same but with handles containing only one of epmc and jats

        # first for files containing only jats (no epmc)
        handles = fixtures.PackageFactory.custom_file_handles(no_epmc=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)

        assert inst.zip_path is None
        assert inst.zip is None
        assert inst.jats is not None
        assert inst.epmc is None

        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
        assert len(names) == 1
        assert "filesandjats_jats.xml" in names

        # then for files containing only epmc (no jats)
        handles = fixtures.PackageFactory.custom_file_handles(no_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)

        assert inst.zip_path is None
        assert inst.zip is None
        assert inst.jats is None
        assert inst.epmc is not None

        names = []
        for name, stream in inst.metadata_streams():
            names.append(name)
        assert len(names) == 1
        assert "filesandjats_epmc.xml" in names

    def test_05_invalid_file_handles(self):
        handles = fixtures.PackageFactory.custom_file_handles(no_epmc=True, no_jats=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)
            except packages.PackageException as e:
                assert e.message == "No JATS fulltext or EPMC metadata found in metadata files"
                raise e

        handles = fixtures.PackageFactory.custom_file_handles(invalid_epmc=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)
            except packages.PackageException as e:
                assert e.message == "Unable to parse filesandjats_epmc.xml file from store"
                raise e

        handles = fixtures.PackageFactory.custom_file_handles(invalid_jats=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)
            except packages.PackageException as e:
                assert e.message == "Unable to parse filesandjats_jats.xml file from store"
                raise e

    def test_06_package_manager_ingest(self):
        # create a custom zip (the package manager will delete it, so don't use the fixed example)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path)

        # get the package manager to ingest
        packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

        # now check that the consequences of the above have worked out

        # original file should have been deleted
        assert not os.path.exists(self.custom_zip_path)

        # create our own instance of the storage manager, and query the store directly
        sm = store.StoreFactory.get()

        # check that all the files have been stored
        stored = sm.list(STORE_ID)
        assert len(stored) == 3
        assert "FilesAndJATS.zip" in stored
        assert "filesandjats_jats.xml" in stored
        assert "filesandjats_epmc.xml" in stored

        # check that we can retrieve the metadata files and read them
        jats = sm.get(STORE_ID, "filesandjats_jats.xml")
        epmc = sm.get(STORE_ID, "filesandjats_epmc.xml")

        # should be able to initialse the package handler around them without error
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=[("filesandjats_jats.xml", jats), ("filesandjats_epmc.xml", epmc)])

    def test_07_package_manager_ingest_fail(self):
        # create a package that has an error in it
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path, corrupt_zip=True)

        # try to import it, and expect a PackageException to be raised
        with self.assertRaises(packages.PackageException):
            packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

        # now switch the current store for one which will fail to save
        app.config["STORE_IMPL"] = "service.tests.fixtures.packages.StoreFailStore"

        # now do a correctly structured package, but make sure a store exception
        # is handled
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path)
        with self.assertRaises(store.StoreException):
            packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

    def test_08_match_data(self):
        # generate the match data
        fhs = fixtures.PackageFactory.file_handles(elife_jats=False, epmc_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=fhs)
        rm = inst.match_data()

        # this is the data we expect to have been extracted
        author_list = "Cerasoli E, Ryadnov MG, Austen BM."
        authors = ["Cerasoli E", "Ryadnov MG", "Austen BM", "Eleonora Cerasoli", "Maxim G. Ryadnov", "Brian M. Austen"]
        affs = [
            "Biotechnology Department, National Physical Laboratory Teddington, UK.",
            "Basic Medical Sciences, St. George's University of London London, UK.",
            "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK",
            "2 Basic Medical Sciences, St. George's University of London, EH106KL London, UK"
        ]
        grants = ["085475/B/08/Z", "085475/08/Z"]
        keywords = ["Humans", "Glaucoma, Open-Angle", "Chemistry", u'A\u03b2 oligomers',
                    "neurodegeneration", "protein misfolding", "fibrillogenesis", "Alzheimer's disease"]
        emails = ["sghk200@sgul.ac.uk"]
        postcodes = ["SW1 5EY", "EH106KL"]


        # check that we got all the data we expected
        als = rm.get_author_ids(type="author-list")
        assert len(als) == 1
        assert als[0]["id"] == author_list

        names = rm.get_author_ids(type="name")
        assert len(names) == len(authors)
        for a in names:
            assert a["id"] in authors

        affiliations = rm.affiliations
        assert len(affiliations) == len(affs)
        for a in affs:
            assert a in affiliations

        gids = rm.grants
        assert len(gids) == len(grants)
        for g in grants:
            assert g in gids

        keys = rm.keywords
        assert len(keys) == len(keywords)
        for k in keywords:
            assert k in keys

        es = rm.emails
        assert len(es) == len(emails)
        for e in emails:
            assert e in es

        codes = rm.postcodes
        assert len(codes) == len(postcodes)
        for c in codes:
            assert c in postcodes

    def test_09_epmc_metadata(self):
        """
        Ok, so technically this is testing a private method on a specific instance of the
        packager, but that method does some quite difficult work, so needs to be tested in isolation
        We will also test it further down as part of the broader function it is part of
        :return:
        """
        fhs = fixtures.PackageFactory.file_handles(elife_jats=False, epmc_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=fhs)
        md = inst._epmc_metadata()

        # These are the results we would expect
        title = u"The elusive nature and diagnostics of misfolded Aβ oligomers."
        type = "Journal Article"
        lang = "eng"
        pubdate = "2015-03-19T00:00:00Z"
        pmid = "25853119"
        pmcid = "PMC4365737"
        doi = "10.3389/fchem.2015.00017"
        issns = ["2296-2646"]
        authors = [
            {"name" : "Cerasoli E", "affiliation" : "Biotechnology Department, National Physical Laboratory Teddington, UK."},
            {"name" : "Ryadnov MG", "affiliation" : "Biotechnology Department, National Physical Laboratory Teddington, UK."},
            {"name" : "Austen BM", "affiliation" : "Basic Medical Sciences, St. George's University of London London, UK."}
        ]
        projects = [
            {"name" : "Wellcome Trust", "grant_number" : "085475/B/08/Z"},
            {"name" : "Wellcome Trust", "grant_number" : "085475/08/Z"}
        ]
        subjects = ["Humans", "Glaucoma, Open-Angle", u'A\u03b2 Oligomers',
                    "Neurodegeneration", "protein misfolding", "Fibrillogenesis", "Alzheimer's disease"]

        assert md.title == title
        assert md.type == type
        assert md.language == lang
        assert md.publication_date == pubdate
        assert md.get_identifiers("pmid")[0] == pmid
        assert md.get_identifiers("pmcid")[0] == pmcid
        assert md.get_identifiers("doi")[0] == doi
        assert md.get_identifiers("issn") == issns

        count = 0
        for a in md.authors:
            for comp in authors:
                if a.get("name") == comp.get("name"):
                    assert a.get("affiliation") == comp.get("affiliation")
                    count += 1
        assert count == 3

        count = 0
        for p in md.projects:
            for comp in projects:
                if p.get("grant_number") == comp.get("grant_number"):
                    assert p.get("name") == comp.get("name")
                    count += 1
        assert count == 2

        for s in md.subjects:
            assert s in subjects
        assert len(subjects) == len(md.subjects)

    def test_10_jats_metadata(self):
        """
        Ok, so technically this is testing a private method on a specific instance of the
        packager, but that method does some quite difficult work, so needs to be tested in isolation
        We will also test it further down as part of the broader function it is part of
        :return:
        """
        fhs = fixtures.PackageFactory.file_handles(elife_jats=False, epmc_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=fhs)
        md = inst._jats_metadata()

        # These are the results we would expect
        title = u"The elusive nature and diagnostics of misfolded Aβ oligomers"
        publisher = "Frontiers Media S.A."
        accepted = "2015-02-24T00:00:00Z"
        submitted = "2014-12-15T00:00:00Z"
        license_type = "open-access"
        license_url = "http://creativecommons.org/licenses/by/4.0/"
        pmcid = "PMC4365737"
        doi = "10.3389/fchem.2015.00017"
        issns = ["2296-2646"]
        authors = [
            {"name" : "Eleonora Cerasoli", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Maxim G. Ryadnov", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Brian M. Austen", "affiliation" : "2 Basic Medical Sciences, St. George's University of London, EH106KL London, UK"}
        ]
        subjects = ["Chemistry", u'A\u03b2 oligomers',
                    "neurodegeneration", "protein misfolding", "fibrillogenesis", "Alzheimer's disease"]

        assert md.title == title
        assert md.publisher == publisher
        assert md.date_accepted == accepted
        assert md.date_submitted == submitted

        lic = md.license
        assert lic.get("title") == license_type
        assert lic.get("type") == license_type
        assert lic.get("url") == license_url

        assert md.get_identifiers("pmcid")[0] == pmcid
        assert md.get_identifiers("doi")[0] == doi
        assert md.get_identifiers("issn") == issns

        count = 0
        for a in md.authors:
            for comp in authors:
                if a.get("name") == comp.get("name"):
                    assert a.get("affiliation") == comp.get("affiliation")
                    count += 1
        assert count == 3

        for s in md.subjects:
            assert s in subjects
        assert len(subjects) == len(md.subjects)

    def test_11_notification_metadata(self):
        fhs = fixtures.PackageFactory.file_handles(elife_jats=False, epmc_jats=True)
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=fhs)
        md = inst.notification_metadata()

        # These are the results we would expect
        title = u"The elusive nature and diagnostics of misfolded Aβ oligomers"
        publisher = "Frontiers Media S.A."
        type = "Journal Article"
        lang = "eng"
        pubdate = "2015-03-19T00:00:00Z"
        accepted = "2015-02-24T00:00:00Z"
        submitted = "2014-12-15T00:00:00Z"
        license_type = "open-access"
        license_url = "http://creativecommons.org/licenses/by/4.0/"
        pmid = "25853119"
        pmcid = "PMC4365737"
        doi = "10.3389/fchem.2015.00017"
        issns = ["2296-2646"]
        authors = [
            {"name" : "Eleonora Cerasoli", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Maxim G. Ryadnov", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Brian M. Austen", "affiliation" : "2 Basic Medical Sciences, St. George's University of London, EH106KL London, UK"}
        ]
        projects = [
            {"name" : "Wellcome Trust", "grant_number" : "085475/B/08/Z"},
            {"name" : "Wellcome Trust", "grant_number" : "085475/08/Z"}
        ]
        subjects = ["Chemistry", u'A\u03b2 oligomers', "neurodegeneration", "protein misfolding", "fibrillogenesis",
                    "Alzheimer's disease", "Humans", "Glaucoma, Open-Angle", u'A\u03b2 Oligomers', "Neurodegeneration",
                    "Fibrillogenesis"]

        assert md.title == title
        assert md.publisher == publisher
        assert md.type == type
        assert md.language == lang
        assert md.publication_date == pubdate
        assert md.date_accepted == accepted
        assert md.date_submitted == submitted

        lic = md.license
        assert lic.get("title") == license_type
        assert lic.get("type") == license_type
        assert lic.get("url") == license_url

        assert md.get_identifiers("pmid")[0] == pmid
        assert md.get_identifiers("pmcid")[0] == pmcid
        assert md.get_identifiers("doi")[0] == doi
        assert md.get_identifiers("issn") == issns

        count = 0
        for a in md.authors:
            for comp in authors:
                if a.get("name") == comp.get("name"):
                    assert a.get("affiliation") == comp.get("affiliation")
                    count += 1
        assert count == 3

        count = 0
        for p in md.projects:
            for comp in projects:
                if p.get("grant_number") == comp.get("grant_number"):
                    assert p.get("name") == comp.get("name")
                    count += 1
        assert count == 2

        for s in md.subjects:
            assert s in subjects
        assert len(subjects) == len(md.subjects)

    def test_12_package_manager_extract(self):
        # create a custom zip (the package manager will delete it, so don't use the fixed example)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path)

        # get the package manager to ingest
        packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

        # now the item is in the store, get the package manager to extract from store
        md, rm = packages.PackageManager.extract(STORE_ID, PACKAGE)

        # These are the results we would expect from the metadata (same as in the previous test)
        title = u"The elusive nature and diagnostics of misfolded Aβ oligomers"
        publisher = "Frontiers Media S.A."
        type = "Journal Article"
        lang = "eng"
        pubdate = "2015-03-19T00:00:00Z"
        accepted = "2015-02-24T00:00:00Z"
        submitted = "2014-12-15T00:00:00Z"
        license_type = "open-access"
        license_url = "http://creativecommons.org/licenses/by/4.0/"
        pmid = "25853119"
        pmcid = "PMC4365737"
        doi = "10.3389/fchem.2015.00017"
        issns = ["2296-2646"]
        authors = [
            {"name" : "Eleonora Cerasoli", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Maxim G. Ryadnov", "affiliation" : "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK"},
            {"name" : "Brian M. Austen", "affiliation" : "2 Basic Medical Sciences, St. George's University of London, EH106KL London, UK"}
        ]
        projects = [
            {"name" : "Wellcome Trust", "grant_number" : "085475/B/08/Z"},
            {"name" : "Wellcome Trust", "grant_number" : "085475/08/Z"}
        ]
        subjects = ["Chemistry", u'A\u03b2 oligomers', "neurodegeneration", "protein misfolding", "fibrillogenesis",
                    "Alzheimer's disease", "Humans", "Glaucoma, Open-Angle", u'A\u03b2 Oligomers', "Neurodegeneration",
                    "Fibrillogenesis"]

        assert md.title == title
        assert md.publisher == publisher
        assert md.type == type
        assert md.language == lang
        assert md.publication_date == pubdate
        assert md.date_accepted == accepted
        assert md.date_submitted == submitted

        lic = md.license
        assert lic.get("title") == license_type
        assert lic.get("type") == license_type
        assert lic.get("url") == license_url

        assert md.get_identifiers("pmid")[0] == pmid
        assert md.get_identifiers("pmcid")[0] == pmcid
        assert md.get_identifiers("doi")[0] == doi
        assert md.get_identifiers("issn") == issns

        count = 0
        for a in md.authors:
            for comp in authors:
                if a.get("name") == comp.get("name"):
                    assert a.get("affiliation") == comp.get("affiliation")
                    count += 1
        assert count == 3

        count = 0
        for p in md.projects:
            for comp in projects:
                if p.get("grant_number") == comp.get("grant_number"):
                    assert p.get("name") == comp.get("name")
                    count += 1
        assert count == 2

        for s in md.subjects:
            assert s in subjects
        assert len(subjects) == len(md.subjects)

        # this is the data we expect to have been extracted for the match
        author_list = "Cerasoli E, Ryadnov MG, Austen BM."
        authors = ["Cerasoli E", "Ryadnov MG", "Austen BM", "Eleonora Cerasoli", "Maxim G. Ryadnov", "Brian M. Austen"]
        affs = [
            "Biotechnology Department, National Physical Laboratory Teddington, UK.",
            "Basic Medical Sciences, St. George's University of London London, UK.",
            "1 Biotechnology Department, National Physical Laboratory, SW1 5EY Teddington, UK",
            "2 Basic Medical Sciences, St. George's University of London, EH106KL London, UK"
        ]
        grants = ["085475/B/08/Z", "085475/08/Z"]
        keywords = ["Humans", "Glaucoma, Open-Angle", "Chemistry", u'A\u03b2 oligomers',
                    "neurodegeneration", "protein misfolding", "fibrillogenesis", "Alzheimer's disease"]
        emails = ["sghk200@sgul.ac.uk"]
        postcodes = ["SW1 5EY", "EH106KL"]


        # check that we got all the data we expected
        als = rm.get_author_ids(type="author-list")
        assert len(als) == 1
        assert als[0]["id"] == author_list

        names = rm.get_author_ids(type="name")
        assert len(names) == len(authors)
        for a in names:
            assert a["id"] in authors

        affiliations = rm.affiliations
        assert len(affiliations) == len(affs)
        for a in affs:
            assert a in affiliations

        gids = rm.grants
        assert len(gids) == len(grants)
        for g in grants:
            assert g in gids

        keys = rm.keywords
        assert len(keys) == len(keywords)
        for k in keywords:
            assert k in keys

        es = rm.emails
        assert len(es) == len(emails)
        for e in emails:
            assert e in es

        codes = rm.postcodes
        assert len(codes) == len(postcodes)
        for c in codes:
            assert c in postcodes

    def test_13_filesandjats_names(self):
        pm = packages.PackageFactory.incoming(PACKAGE)
        assert pm.zip_name() == "FilesAndJATS.zip"
        assert "filesandjats_jats.xml" in pm.metadata_names()
        assert "filesandjats_epmc.xml" in pm.metadata_names()
        assert "FilesAndJATS" in pm.url_name()

    def test_14_faj_sz_convert(self):
        # get a package manager and the path to our test package
        pm = packages.PackageFactory.converter(PACKAGE)
        in_path = fixtures.PackageFactory.example_package_path()

        # run the coversion to the custom zip path
        converted = pm.convert(in_path, SIMPLE_ZIP, self.custom_zip_path)

        assert converted is True
        assert os.path.exists(self.custom_zip_path)
        assert os.path.isfile(self.custom_zip_path)

        # now try a conversion to an unsupported format
        os.remove(self.custom_zip_path)
        converted = pm.convert(in_path, "random string", self.custom_zip_path)

        assert converted is False
        assert not os.path.exists(self.custom_zip_path)

    def test_15_package_manager_covert(self):
        # first put a package into the store
        # create a custom zip (the package manager will delete it, so don't use the fixed example)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path)

        # get the package manager to ingest
        packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

        # now run the conversion to 2 formats, one of which cannot be converted to and the other of which can
        conversions = packages.PackageManager.convert(STORE_ID, PACKAGE, [TEST_FORMAT, SIMPLE_ZIP])

        # check that the result looks right
        assert len(conversions) == 1    # not 2!
        assert len(conversions[0]) == 3     # it's a tuple
        assert conversions[0][0] == SIMPLE_ZIP
        assert conversions[0][1] == "SimpleZip.zip"
        assert conversions[0][2] == "SimpleZip.zip"

        # now check that under the hood the right things happened
        tmp = store.StoreFactory.tmp()
        assert not tmp.exists(STORE_ID)

        # check that the remote store still exists
        s = store.StoreFactory.get()
        assert s.exists(STORE_ID)

        # check that the new file is there along with the others
        l = s.list(STORE_ID)
        assert "SimpleZip.zip" in l
        assert len(l) == 4          # the files and jats zip, the 2 extracted metadata files, and the simple zip

        # ensure that the new file has content
        f = s.get(STORE_ID, "SimpleZip.zip")
        c = f.read()        # file is only small and this is a test, so read it all into memory
        assert len(c) > 0

    def test_16_convert_no_source(self):
        # try to run the conversion without creating the stored object in the first place
        conversions = packages.PackageManager.convert(STORE_ID, PACKAGE, [TEST_FORMAT, SIMPLE_ZIP])
        assert len(conversions) == 0

        # now create the container, but remove the file, to see if we can trip up the converter

        # create a custom zip (the package manager will delete it, so don't use the fixed example)
        fixtures.PackageFactory.make_custom_zip(self.custom_zip_path)

        # get the package manager to ingest
        packages.PackageManager.ingest(STORE_ID, self.custom_zip_path, PACKAGE)

        # interfere with the store, and delete the file we want to convert from, leaving behind the
        # store directory itself
        s = store.StoreFactory.get()
        s.delete(STORE_ID, "FilesAndJATS.zip")

        conversions = packages.PackageManager.convert(STORE_ID, PACKAGE, [TEST_FORMAT, SIMPLE_ZIP])
        assert len(conversions) == 0



