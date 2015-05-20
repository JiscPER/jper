from service.packages import PackageHandler
from octopus.lib import paths
from service import store

import zipfile, os, codecs
from StringIO import StringIO

RESOURCES = paths.rel2abs(__file__, "..", "resources")

class TestPackageHandler(PackageHandler):
    pass

class StoreFailStore(store.StoreLocal):
    def store(self, container_id, target_name, source_path=None, source_stream=None):
        raise store.StoreException("Nope")

class StoreFailRetrieve(store.StoreLocal):
    def get(self, container_id, target_name):
        raise store.StoreException("Shant")

class PackageFactory(object):

    @classmethod
    def example_package_path(cls):
        from service.tests import fixtures
        return fixtures.APIFactory.example_package_path()

    @classmethod
    def make_custom_zip(cls, path, no_jats=False, no_epmc=False, invalid_jats=False, invalid_epmc=False, corrupt_zip=False):
        # if we want a corrupt zip, no need to pay attention to any of the other options
        if corrupt_zip:
            with open(path, "wb") as f:
                f.write("alkdsjfasdfwqefnjwqeoijqwefoqwefoihwqef")
            return

        # create the zip we're going to populate
        zip = zipfile.ZipFile(path, "w")

        # determine if we need to write a jats file
        if not no_jats:
            if invalid_jats:
                zip.writestr("invalidjats.xml", "akdsjiwqefiw2fuwefoiwqejhqfwe")
            else:
                zip.write(os.path.join(RESOURCES, "valid_jats_elife.xml"), "validjats.xml")

        # determine if we need to write an epmc file
        if not no_epmc:
            if invalid_epmc:
                zip.writestr("invalidepmc.xml", "akdsjiwqefiw2fuwefoiwqejhqfwe")
            else:
                zip.write(os.path.join(RESOURCES, "valid_epmc.xml"), "validepmc.xml")

        zip.close()

    @classmethod
    def file_handles(cls):
        jats = codecs.open(os.path.join(RESOURCES, "valid_jats_elife.xml"), "rb")
        epmc = codecs.open(os.path.join(RESOURCES, "valid_epmc.xml"), "rb")
        return [("jats.xml", jats), ("epmc.xml", epmc)]

    @classmethod
    def custom_file_handles(cls, no_jats=False, no_epmc=False, invalid_jats=False, invalid_epmc=False):
        handles = []

        if not no_jats:
            if invalid_jats:
                handles.append(("jats.xml", StringIO("akdsjiwqefiw2fuwefoiwqejhqfwe")))
            else:
                jats = codecs.open(os.path.join(RESOURCES, "valid_jats_elife.xml"), "rb")
                handles.append(("jats.xml", jats))

        if not no_epmc:
            if invalid_epmc:
                handles.append(("epmc.xml", StringIO("akdsjiwqefiw2fuwefoiwqejhqfwe")))
            else:
                epmc = codecs.open(os.path.join(RESOURCES, "valid_epmc.xml"), "rb")
                handles.append(("epmc.xml", epmc))

        return handles
