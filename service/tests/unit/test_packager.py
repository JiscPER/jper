# from octopus.modules.es.testindex import ESTestCase
from unittest import TestCase
from service import packages, store
from copy import deepcopy

from service.tests import fixtures
from octopus.core import app
from lxml import etree
from octopus.lib import paths
import os

PACKAGE = "http://router.jisc.ac.uk/packages/FilesAndJATS"
TEST_FORMAT = "http://router.jisc.ac.uk/packages/OtherTestFormat"
TEST_HANDLER = "service.tests.fixtures.TestPackageHandler"
STORE_ID = "12345"

class TestModels(TestCase):
    def setUp(self):
        super(TestModels, self).setUp()

        self.old_ph = deepcopy(app.config["PACKAGE_HANDLERS"])
        app.config["PACKAGE_HANDLERS"].update({TEST_FORMAT : TEST_HANDLER})

        self.old_store = app.config["STORE_IMPL"]
        app.config["STORE_IMPL"] = "service.store.StoreLocal"

        self.custom_zip_path = paths.rel2abs(__file__, "..", "resources", "custom.zip")

    def tearDown(self):
        super(TestModels, self).tearDown()
        app.config["PACKAGE_HANDLERS"] = self.old_ph
        app.config["STORE_IMPL"] = self.old_store

        if os.path.exists(self.custom_zip_path):
            os.remove(self.custom_zip_path)

        sm = store.StoreFactory.get()
        sm.delete(STORE_ID)

    def test_01_factory(self):
        inst = packages.PackageFactory.incoming(PACKAGE)
        assert isinstance(inst, packages.FilesAndJATS)

        inst = packages.PackageFactory.incoming(TEST_FORMAT)
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
            if name == "jats.xml":
                assert xml.tag == "article"
            elif name == "epmc.xml":
                assert xml.tag == "result"

        assert "jats.xml" in names
        assert "epmc.xml" in names

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
        assert "jats.xml" in names

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
        assert "epmc.xml" in names

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
            if name == "jats.xml":
                assert xml.tag == "article"
            elif name == "epmc.xml":
                assert xml.tag == "result"

        assert "jats.xml" in names
        assert "epmc.xml" in names

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
        assert "jats.xml" in names

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
        assert "epmc.xml" in names

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
                assert e.message == "Unable to parse epmc.xml file from store"
                raise e

        handles = fixtures.PackageFactory.custom_file_handles(invalid_jats=True)
        with self.assertRaises(packages.PackageException):
            try:
                inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=handles)
            except packages.PackageException as e:
                assert e.message == "Unable to parse jats.xml file from store"
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
        assert "content.zip" in stored
        assert "jats.xml" in stored
        assert "epmc.xml" in stored

        # check that we can retrieve the metadata files and read them
        jats = sm.get(STORE_ID, "jats.xml")
        epmc = sm.get(STORE_ID, "epmc.xml")

        # should be able to initialse the package handler around them without error
        inst = packages.PackageFactory.incoming(PACKAGE, metadata_files=[("jats.xml", jats), ("epmc.xml", epmc)])

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




