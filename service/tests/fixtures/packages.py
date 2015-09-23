from service.packages import PackageHandler
from octopus.lib import paths
from octopus.modules.store import store
import uuid

import zipfile, os, codecs
from StringIO import StringIO

RESOURCES = paths.rel2abs(__file__, "..", "resources")

class TestPackageHandler(PackageHandler):
    def zip_name(self):
        return "TestPackageHandler.zip"

    def metadata_names(self):
        return []

    def url_name(self):
        return "TestPackageHandler"

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
    def make_custom_zip(cls, path, no_jats=False, no_epmc=False, invalid_jats=False, invalid_epmc=False, corrupt_zip=False, target_size=None):
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
                zip.write(os.path.join(RESOURCES, "valid_jats_epmc.xml"), "validjats.xml")

        # determine if we need to write an epmc file
        if not no_epmc:
            if invalid_epmc:
                zip.writestr("invalidepmc.xml", "akdsjiwqefiw2fuwefoiwqejhqfwe")
            else:
                zip.write(os.path.join(RESOURCES, "valid_epmc.xml"), "validepmc.xml")

        # now pad the file out with pdf files until it reaches the target size (or slightly over)
        if target_size is not None:
            while os.path.getsize(path) < target_size:
                zip.write(os.path.join(RESOURCES, "download.pdf"), uuid.uuid4().hex + ".pdf")

        zip.close()

    @classmethod
    def file_handles(cls, elife_jats=True, epmc_jats=False):
        jats = None
        if elife_jats:
            jats = codecs.open(os.path.join(RESOURCES, "valid_jats_elife.xml"), "rb")
        elif epmc_jats:
            jats = codecs.open(os.path.join(RESOURCES, "valid_jats_epmc.xml"), "rb")

        epmc = codecs.open(os.path.join(RESOURCES, "valid_epmc.xml"), "rb")

        fhs = [("filesandjats_epmc.xml", epmc)]
        if jats is not None:
            fhs.append(("filesandjats_jats.xml", jats))

        return fhs

    @classmethod
    def custom_file_handles(cls, no_jats=False, no_epmc=False, invalid_jats=False, invalid_epmc=False):
        handles = []

        if not no_jats:
            if invalid_jats:
                handles.append(("filesandjats_jats.xml", StringIO("akdsjiwqefiw2fuwefoiwqejhqfwe")))
            else:
                jats = codecs.open(os.path.join(RESOURCES, "valid_jats_elife.xml"), "rb")
                handles.append(("filesandjats_jats.xml", jats))

        if not no_epmc:
            if invalid_epmc:
                handles.append(("filesandjats_epmc.xml", StringIO("akdsjiwqefiw2fuwefoiwqejhqfwe")))
            else:
                epmc = codecs.open(os.path.join(RESOURCES, "valid_epmc.xml"), "rb")
                handles.append(("filesandjats_epmc.xml", epmc))

        return handles
