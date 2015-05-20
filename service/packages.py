from octopus.core import app
from octopus.lib import plugin
import zipfile, os, sys
from lxml import etree
from octopus.modules.epmc.models import JATS, EPMCMetadataXML
from service import store, models
from StringIO import StringIO

class PackageException(Exception):
    pass

class PackageFactory(object):

    @classmethod
    def incoming(cls, format, zip_path=None, metadata_files=None):
        formats = app.config.get("PACKAGE_HANDLERS", {})
        cname = formats.get(format)
        klazz = plugin.load_class(cname)
        return klazz(zip_path, metadata_files)

class PackageManager(object):

    @classmethod
    def ingest(cls, store_id, zip_path, format):
        # load the package manager and the storage manager
        pm = PackageFactory.incoming(format, zip_path)
        sm = store.StoreFactory.get()

        # store the zip file as-is
        sm.store(store_id, "content.zip", source_path=zip_path)

        # now extract the metadata streams from the package
        for name, stream in pm.metadata_streams():
            sm.store(store_id, name, source_stream=stream)

        # finally remove the local copy of the zip file
        os.remove(zip_path)

    @classmethod
    def extract(cls, store_id, format):
        # load the storage manager
        sm = store.StoreFactory.get()

        # list the stored file and determine which are the metadata files
        remotes = sm.list(store_id)
        if "content.zip" in remotes:
            remotes.remove("content.zip")

        # create a list of tuples of filenames and contents
        handles = []
        for r in remotes:
            fh = sm.get(store_id, r)
            handles.append((r, fh))

        # create the specific package manager around the new metadata
        pm = PackageFactory.incoming(format, metadata_files=handles)

        # now do the metadata and the match analysis extraction
        md = pm.notification_metadata()
        ma = pm.match_data()

        # return the extracted data
        return md, ma


class PackageHandler(object):
    """
    Interface/Parent class for all objects wishing to provide package handling
    """
    def __init__(self, zip_path=None, metadata_files=None):
        self.zip_path = zip_path
        self.metadata_files = metadata_files
        self.zip = None

    def metadata_streams(self):
        """
        generator, should yield
        """
        for x in []:
            yield None, None

    def notification_metadata(self):
        return models.NotificationMetadata()

    def match_data(self):
        return models.RoutingMetadata()

class FilesAndJATS(PackageHandler):
    """
    This is the default format that we currently prefer to get from
    providers.  It consists of a zip of a single XML file which is the JATS fulltext,
    a single PDF which is the fulltext, and an arbitrary number of other
    files which are supporting information.  It may also contain the NLM/EPMC
    formatted metadata as XML

    To be valid, the zip must just consist of the JATS file OR the EPMC metadata file.
    All other files are optional
    """
    def __init__(self, zip_path=None, metadata_files=None):
        super(FilesAndJATS, self).__init__(zip_path=zip_path, metadata_files=metadata_files)

        self.jats = None
        self.epmc = None

        if self.zip_path is not None:
            self._load_from_zip()
        elif self.metadata_files is not None:
            self._load_from_metadata()

    def metadata_streams(self):
        sources = [("jats.xml", self.jats), ("epmc.xml", self.epmc)]
        for n, x in sources:
            if x is not None:
                yield n, StringIO(x.tostring())

    def notification_metadata(self):
        pass

    def match_data(self):
        pass

    def _load_from_metadata(self):
        for name, stream in self.metadata_files:
            if name == "jats.xml":
                try:
                    xml = etree.fromstring(stream.read())
                    self._set_jats(xml)
                except Exception:
                    raise PackageException("Unable to parse jats.xml file from store")
            elif name == "epmc.xml":
                try:
                    xml = etree.fromstring(stream.read())
                    self._set_epmc(xml)
                except Exception:
                    raise PackageException("Unable to parse epmc.xml file from store")

        if not self._is_valid():
            raise PackageException("No JATS fulltext or EPMC metadata found in metadata files")

    def _load_from_zip(self):
        try:
            self.zip = zipfile.ZipFile(self.zip_path, "r", allowZip64=True)
        except zipfile.BadZipfile as e:
            raise PackageException("Zip file is corrupt - cannot read.")

        for x in self._xml_files():
            try:
                doc = etree.fromstring(self.zip.open(x).read())
            except Exception:
                raise PackageException("Unable to parse XML file in package {x}".format(x=x))

            if doc.tag in ["resultList", "result"]:
                self._set_epmc(doc)
            elif doc.tag == "article":
                self._set_jats(doc)

        if not self._is_valid():
            raise PackageException("No JATS fulltext or EPMC metadata found in package")

    def _xml_files(self):
        if self.zip is None:
            return []
        xmls = []
        for name in self.zip.namelist():
            if name.endswith(".xml"):
                xmls.append(name)
        return xmls

    def _set_epmc(self, xml):
        if xml.tag == "resultList":
            res = xml.find("result")
            if res is not None:
                self.epmc = EPMCMetadataXML(xml=res)
            else:
                raise PackageException("Unable to find result element in EPMC resultList")
        elif xml.tag == "result":
            self.epmc = EPMCMetadataXML(xml=xml)

    def _set_jats(self, xml):
        self.jats = JATS(xml=xml)

    def _is_valid(self):
        # is valid if either one or both of jats/epmc is not none
        return self.jats is not None or self.epmc is not None
