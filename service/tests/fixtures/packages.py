"""
Fixtures for testing packages
"""

from service.packages import PackageHandler
from octopus.lib import paths
from octopus.modules.store import store
import uuid

import zipfile, os, codecs
from io import StringIO

RESOURCES = paths.rel2abs(__file__, "..", "resources")
"""Path to the test resources directory, calculated relative to this file"""

class TestPackageHandler(PackageHandler):
    """
    Class which implements the PackageHandler interface for the purposes of mocks

    See the PackageHandler documentation for more information about the methods here
    """

    def zip_name(self):
        return "TestPackageHandler.zip"

    def metadata_names(self):
        return []

    def url_name(self):
        return "TestPackageHandler"

class StoreFailStore(store.StoreLocal):
    """
    Class which extends the local store implementation in order to raise errors under
    useful testing conditions
    """
    def store(self, container_id, target_name, source_path=None, source_stream=None):
        """
        Raise an exception when attempting to store

        :param container_id:
        :param target_name:
        :param source_path:
        :param source_stream:
        :return:
        """
        raise store.StoreException("Nope")

class StoreFailRetrieve(store.StoreLocal):
    """
    Class which extends the local store implementation in order to raise errors under useful
    testing conditions
    """
    def get(self, container_id, target_name):
        """
        Raise an exception on retrieve

        :param container_id:
        :param target_name:
        :return:
        """
        raise store.StoreException("Shant")

class PackageFactory(object):
    """
    Class which provides access to fixtures for testing packaging
    """

    @classmethod
    def example_package_path(cls):
        """
        Get the path to the example package in the resources directory

        :return: path
        """
        from service.tests import fixtures
        return fixtures.APIFactory.example_package_path()

    @classmethod
    def make_custom_zip(cls, path, no_jats=False, no_epmc=False, invalid_jats=False, invalid_epmc=False, corrupt_zip=False, target_size=None):
        """
        Construct a custom zip file for testing packaging, which has the following features

        :param path: where to store it
        :param no_jats: whether to omit the JATS XML
        :param no_epmc: whether to omit the EPMC XML
        :param invalid_jats: whether the included JATS is invalid
        :param invalid_epmc: whether the included EPMC XML is invalid
        :param corrupt_zip: should the zip file be corrupt
        :param target_size: how large should the file be (output is approximate, not exact)
        :return:
        """
        # if we want a corrupt zip, no need to pay attention to any of the other options
        if corrupt_zip:
            with open(path, "wb") as f:
                f.write("alkdsjfasdfwqefnjwqeoijqwefoqwefoihwqef".encode('utf-8'))
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
        """
        Create metadata file handles suitable for passing to a package handler

        :param elife_jats: should there be a JATS metadata file
        :param epmc_jats: should there be an EMPC metadata file
        :return: list of tuples of filename/stream
        """
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
        """
        Custom metadata file handles suitable for passing to a package handler

        :param no_jats: omit JATS
        :param no_epmc: omit EPMC
        :param invalid_jats: should the included JATS be invalid
        :param invalid_epmc: should the included EPMC be invalid
        :return:
        """
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
