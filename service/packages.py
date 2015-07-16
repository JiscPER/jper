from octopus.core import app
from octopus.lib import plugin
import zipfile, os, sys
from lxml import etree
from octopus.modules.epmc.models import JATS, EPMCMetadataXML
from service import models
from octopus.modules.store import store
from StringIO import StringIO

class PackageException(Exception):
    pass

class PackageFactory(object):

    @classmethod
    def incoming(cls, format, zip_path=None, metadata_files=None):
        formats = app.config.get("PACKAGE_HANDLERS", {})
        cname = formats.get(format)
        if cname is None:
            raise PackageException("No handler for package format {x}".format(x=format))
        klazz = plugin.load_class(cname)
        return klazz(zip_path=zip_path, metadata_files=metadata_files)

class PackageManager(object):

    @classmethod
    def ingest(cls, store_id, zip_path, format, storage_manager=None):
        # load the package manager and the storage manager
        pm = PackageFactory.incoming(format, zip_path)
        if storage_manager is None:
            storage_manager = store.StoreFactory.get()

        # store the zip file as-is
        storage_manager.store(store_id, "content.zip", source_path=zip_path)

        # now extract the metadata streams from the package
        for name, stream in pm.metadata_streams():
            storage_manager.store(store_id, name, source_stream=stream)

        # finally remove the local copy of the zip file
        os.remove(zip_path)

    @classmethod
    def extract(cls, store_id, format, storage_manager=None):
        # load the storage manager
        if storage_manager is None:
            storage_manager = store.StoreFactory.get()

        # check the object exists in the store - if not do nothing
        if not storage_manager.exists(store_id):
            return None, None

        # list the stored file and determine which are the metadata files
        remotes = storage_manager.list(store_id)
        if "content.zip" in remotes:
            remotes.remove("content.zip")

        # create a list of tuples of filenames and contents
        handles = []
        for r in remotes:
            fh = storage_manager.get(store_id, r)
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
        emd = None
        jmd = None

        # extract all the relevant data from epmc
        if self.epmc is not None:
            emd = self._epmc_metadata()

        # extract all the relevant data from jats
        if self.jats is not None:
            jmd = self._jats_metadata()

        return self._merge_metadata(emd, jmd)

    def match_data(self):
        match = models.RoutingMetadata()

        # extract all the relevant match data from epmc
        if self.epmc is not None:
            self._epmc_match_data(match)

        # extract all the relevant match data from jats
        if self.jats is not None:
            self._jats_match_data(match)

        return match

    def _merge_metadata(self, emd, jmd):
        if emd is None:
            emd = models.NotificationMetadata()
        if jmd is None:
            jmd = models.NotificationMetadata()

        md = models.NotificationMetadata()

        md.title = jmd.title if jmd.title is not None else emd.title
        md.publisher = jmd.publisher
        md.type = emd.type
        md.language = emd.language
        md.publication_date = emd.publication_date if emd.publication_date is not None else jmd.publication_date
        md.date_accepted = jmd.date_accepted
        md.date_submitted = jmd.date_submitted
        md.license = jmd.license

        for id in emd.identifiers:
            md.add_identifier(id.get("id"), id.get("type"))
        for id in jmd.identifiers:
            md.add_identifier(id.get("id"), id.get("type"))

        md.authors = jmd.authors if len(jmd.authors) > 0 else emd.authors
        md.projects = emd.projects

        for s in emd.subjects:
            md.add_subject(s)
        for s in jmd.subjects:
            md.add_subject(s)

        return md

    def _jats_metadata(self):
        md = models.NotificationMetadata()

        md.title = self.jats.title
        md.publisher = self.jats.publisher
        md.publication_date = self.jats.publication_date
        md.date_accepted = self.jats.date_accepted
        md.date_submitted = self.jats.date_submitted

        type, url, _ = self.jats.get_licence_details()
        md.set_license(type, url)

        for issn in self.jats.issn:
            md.add_identifier(issn, "issn")

        md.add_identifier(self.jats.pmcid, "pmcid")
        md.add_identifier(self.jats.doi, "doi")

        for author in self.jats.authors:
            name = author.get("given-names", "") + " " + author.get("surname", "")
            if name.strip() == "":
                continue
            affs = "; ".join(author.get("affiliations", []))
            obj = {"name" : name}
            if affs is not None and affs != "":
                obj["affiliation"] = affs
            md.add_author(obj)

        for kw in self.jats.categories:
            md.add_subject(kw)
        for kw in self.jats.keywords:
            md.add_subject(kw)

        return md

    def _epmc_metadata(self):
        md = models.NotificationMetadata()

        md.title = self.epmc.title
        md.type = self.epmc.publication_type
        md.language = self.epmc.language
        md.publication_date = self.epmc.publication_date

        md.add_identifier(self.epmc.pmid, "pmid")
        md.add_identifier(self.epmc.pmcid, "pmcid")
        md.add_identifier(self.epmc.doi, "doi")

        for issn in self.epmc.issns:
            md.add_identifier(issn, "issn")

        for author in self.epmc.authors:
            fn = author.get("fullName")
            if fn is None:
                continue
            aff = author.get("affiliation")
            obj = {"name" : fn}
            if aff is not None:
                obj["affiliation"] = aff
            md.add_author(obj)

        for grant in self.epmc.grants:
            obj = {}
            gid = grant.get("grantId")
            if gid is not None:
                obj["grant_number"] = gid
            ag = grant.get("agency")
            if ag is not None:
                obj["name"] = ag
            if len(obj.keys()) > 0:
                md.add_project(obj)

        for kw in self.epmc.mesh_descriptors:
            md.add_subject(kw)
        for kw in self.epmc.keywords:
            md.add_subject(kw)

        return md

    def _jats_match_data(self, match):
        # subject keywords
        for c in self.jats.categories:
            match.add_keyword(c)

        # individual authors, emails, affiliations
        for a in self.jats.contribs:
            # name
            name = a.get("given-names", "") + " " + a.get("surname", "")
            if name.strip() != "":
                match.add_author_id(name, "name")

            # email
            email = a.get("email")
            if email is not None:
                match.add_email(email)

            # affiliations
            affs = a.get("affiliations", [])
            for a in affs:
                match.add_affiliation(a)

        # other keywords
        for k in self.jats.keywords:
            match.add_keyword(k)

        # other email addresses
        for e in self.jats.emails:
            match.add_email(e)

    def _epmc_match_data(self, match):
        # author string
        author_string = self.epmc.author_string
        if author_string is not None:
            match.add_author_id(author_string, "author-list")

        # individual authors and their affiliations
        authors = self.epmc.authors
        for a in authors:
            # name
            fn = a.get("fullName")
            if fn is not None:
                match.add_author_id(fn, "name")

            # affiliation
            aff = a.get("affiliation")
            if aff is not None:
                match.add_affiliation(aff)

        # grant ids
        gs = self.epmc.grants
        for g in gs:
            gid = g.get("grantId")
            if gid is not None:
                match.add_grant_id(gid)

        # keywords
        keys = self.epmc.mesh_descriptors
        for k in keys:
            match.add_keyword(k)

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
