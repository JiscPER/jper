from octopus.core import app
from octopus.lib import plugin
import zipfile, os, shutil
from lxml import etree
from octopus.modules.epmc.models import JATS, EPMCMetadataXML
from octopus.modules.identifiers import postcode
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
            msg = "No handler for package format {x}".format(x=format)
            app.logger.info("Package Factory Incoming - {x}".format(x=msg))
            raise PackageException(msg)
        klazz = plugin.load_class(cname)
        return klazz(zip_path=zip_path, metadata_files=metadata_files)

    @classmethod
    def converter(cls, format):
        formats = app.config.get("PACKAGE_HANDLERS", {})
        cname = formats.get(format)
        if cname is None:
            msg = "No handler for package format {x}".format(x=format)
            app.logger.info("Package Factory Converter - {x}".format(x=msg))
            raise PackageException(msg)
        klazz = plugin.load_class(cname)
        return klazz()

class PackageManager(object):

    @classmethod
    def ingest(cls, store_id, zip_path, format, storage_manager=None):
        app.logger.info("Package Ingest - StoreID:{a}; Format:{b}".format(a=store_id, b=format))

        # load the package manager and the storage manager
        pm = PackageFactory.incoming(format, zip_path)
        if storage_manager is None:
            storage_manager = store.StoreFactory.get()

        # store the zip file as-is (with the name specified by the packager)
        storage_manager.store(store_id, pm.zip_name(), source_path=zip_path)

        # now extract the metadata streams from the package
        for name, stream in pm.metadata_streams():
            storage_manager.store(store_id, name, source_stream=stream)

        # finally remove the local copy of the zip file
        os.remove(zip_path)

    @classmethod
    def extract(cls, store_id, format, storage_manager=None):
        app.logger.info("Package Extract - StoreID:{a}; Format:{b}".format(a=store_id, b=format))

        # load the storage manager
        if storage_manager is None:
            storage_manager = store.StoreFactory.get()

        # check the object exists in the store - if not do nothing
        if not storage_manager.exists(store_id):
            return None, None

        # get an instance of the package manager that can answer naming convention questions
        pm = PackageFactory.incoming(format)

        # list the stored file and determine which are the metadata files
        remotes = storage_manager.list(store_id)
        mdfs = pm.metadata_names()
        mds = []
        for r in remotes:
            if r in mdfs:
                mds.append(r)

        # create a list of tuples of filenames and contents
        handles = []
        for r in mds:
            fh = storage_manager.get(store_id, r)
            handles.append((r, fh))

        # create the specific package manager around the new metadata (replacing the old instance)
        pm = PackageFactory.incoming(format, metadata_files=handles)

        # now do the metadata and the match analysis extraction
        md = pm.notification_metadata()
        ma = pm.match_data()

        # return the extracted data
        return md, ma

    @classmethod
    def convert(cls, store_id, source_format, target_formats, storage_manager=None):
        app.logger.info("Package Convert - StoreID:{a}; SourceFormat:{b}; TargetFormats:{c}".format(a=store_id, b=source_format, c=",".join(target_formats)))

        # load the storage manager
        if storage_manager is None:
            storage_manager = store.StoreFactory.get()

        # get an instance of the local temp store
        tmp = store.StoreFactory.tmp()

        # get the packager that will do the conversions
        pm = PackageFactory.converter(source_format)

        # check that there is a source package to convert
        if not storage_manager.exists(store_id):
            return []

        try:
            # first check the file we want exists
            if not pm.zip_name() in storage_manager.list(store_id):
                return []

            # make a copy of the storage manager's version of the package manager's primary file into the local
            # temp directory
            stream = storage_manager.get(store_id, pm.zip_name())
            tmp.store(store_id, pm.zip_name(), source_stream=stream)

            # get the in path for the converter to use
            in_path = tmp.path(store_id, pm.zip_name())

            # a record of all the conversions which took place, with all the relevant additonal info
            conversions = []

            # for each target format, load it's equivalent packager to get the storage name,
            # then run the conversion
            for tf in target_formats:
                tpm = PackageFactory.converter(tf)
                out_path = tmp.path(store_id, tpm.zip_name(), must_exist=False)
                converted = pm.convert(in_path, tf, out_path)
                if converted:
                    conversions.append((tf, tpm.zip_name(), tpm.zip_name()))

            # with the conversions completed, synchronise back to the storage system
            for tf, zn, un in conversions:
                stream = tmp.get(store_id, zn)
                storage_manager.store(store_id, zn, source_stream=stream)
        finally:
            try:
                # finally, burn the local copy
                tmp.delete(store_id)
            except:
                raise store.StoreException("Unable to delete from tmp storage {x}".format(x=store_id))

        # return the conversions record to the caller
        return conversions

class PackageHandler(object):
    """
    Interface/Parent class for all objects wishing to provide package handling
    """
    def __init__(self, zip_path=None, metadata_files=None):
        self.zip_path = zip_path
        self.metadata_files = metadata_files
        self.zip = None

    ################################################
    ## methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer
        """
        raise NotImplementedError()

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager
        """
        raise NotImplementedError()

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls
        """
        raise NotImplementedError()

    ################################################
    ## Methods for retriving data from the actual package

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

    def convertible(self, target_format):
        return False

    def convert(self, in_path, target_format, out_path):
        return False

class SimpleZip(PackageHandler):
    """
    Very basic class for representing the SimpleZip package format
    """

    ################################################
    ## methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer
        """
        return "SimpleZip.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager
        """
        return []

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls
        """
        return "SimpleZip"

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

    ################################################
    ## Overrides of methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer
        """
        return "FilesAndJATS.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager
        """
        return ["filesandjats_jats.xml", "filesandjats_epmc.xml"]

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls
        """
        return "FilesAndJATS"

    ################################################
    ## Overrids of methods for retriving data from the actual package

    def metadata_streams(self):
        sources = [("filesandjats_jats.xml", self.jats), ("filesandjats_epmc.xml", self.epmc)]
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

    def convertible(self, target_format):
        return target_format in ["http://purl.org/net/sword/package/SimpleZip"]

    def convert(self, in_path, target_format, out_path):
        if target_format == "http://purl.org/net/sword/package/SimpleZip":
            self._simple_zip(in_path, out_path)
            return True
        return False

    ################################################
    ## Internal methods

    def _simple_zip(self, in_path, out_path):
        # files and jats are already basically a simple zip, so a straight copy
        shutil.copyfile(in_path, out_path)

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

            # affiliations (and postcodes)
            affs = a.get("affiliations", [])
            for a in affs:
                match.add_affiliation(a)
                codes = postcode.extract_all(a)
                for code in codes:
                    match.add_postcode(code)

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

            # affiliation (and postcode)
            aff = a.get("affiliation")
            if aff is not None:
                match.add_affiliation(aff)
                codes = postcode.extract_all(aff)
                for code in codes:
                    match.add_postcode(code)

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
            if name == "filesandjats_jats.xml":
                try:
                    xml = etree.fromstring(stream.read())
                    self._set_jats(xml)
                except Exception:
                    raise PackageException("Unable to parse filesandjats_jats.xml file from store")
            elif name == "filesandjats_epmc.xml":
                try:
                    xml = etree.fromstring(stream.read())
                    self._set_epmc(xml)
                except Exception:
                    raise PackageException("Unable to parse filesandjats_epmc.xml file from store")

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
