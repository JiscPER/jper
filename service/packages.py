"""
Provides general packaging handling infrastructure and specific implementations of known packaging formats

All packaging format handlers should extend the PackageHandler class defined in this module.

Packages should then be configured through the PACKAGE_HANDLERS configuration option
"""

from octopus.core import app
from octopus.lib import plugin
import zipfile, os, shutil
from lxml import etree
from octopus.modules.epmc.models import JATS, EPMCMetadataXML, RSCMetadataXML
# from octopus.modules.identifiers import postcode
# 2017-01-19 TD : in the deepgreen setting, postcodes are not needed. They are rather counter-productive...
from service import models
from octopus.modules.store import store
from StringIO import StringIO

class PackageException(Exception):
    """
    Generic exception to be thrown when there are issues working with packages
    """
    pass

class PackageFactory(object):
    """
    Factory which provides methods for accessing specific PackageHandler implementations
    """

    @classmethod
    def incoming(cls, format, zip_path=None, metadata_files=None):
        """
        Obtain an instance of a PackageHandler for the provided format to be used to work
        with processing an incoming binary object.

        If the zip path is provided, the handler will be constructed around that file

        If only the metadata file handles are provided, the handler will be constructed around them

        Metadata file handles should be of the form

        ::

            [("filename", <file handle>)]

        It is recommended that as the metadata files are likely to be highly implementation specific
        that you rely on the handler itself to provide you with the names of the files, which you may
        use to retrieve the streams from store.

        :param format: format identifier for the package handler.  As seen in the configuration.
        :param zip_path: file path to an accessible on-disk location where the zip file is stored
        :param metadata_files: list of tuples of filename/filehandle pairs for metadata files extracted from a package
        :return: an instance of a PackageHandler, constructed with the zip_path and/or metadata_files
        """
        formats = app.config.get("PACKAGE_HANDLERS", {})
        cname = formats.get(format)
        if cname is None:
            msg = "No handler for package format {x}".format(x=format)
            app.logger.debug("Package Factory Incoming - {x}".format(x=msg))
            raise PackageException(msg)
        klazz = plugin.load_class(cname)
        return klazz(zip_path=zip_path, metadata_files=metadata_files)

    @classmethod
    def converter(cls, format):
        """
        Obtain an instance of a PackageHandler which can be used to during package conversion to read/write
        the supplied format

        :param format: format identifier for the package handler.  As seen in the configuration.
        """
        formats = app.config.get("PACKAGE_HANDLERS", {})
        cname = formats.get(format)
        if cname is None:
            msg = "No handler for package format {x}".format(x=format)
            app.logger.debug("Package Factory Converter - {x}".format(x=msg))
            raise PackageException(msg)
        klazz = plugin.load_class(cname)
        return klazz()

class PackageManager(object):
    """
    Class which provides an API onto the package management system

    If you need to work with packages, the operation you want to do should be covered by one of the
    methods on this class.
    """
    @classmethod
    def ingest(cls, store_id, zip_path, format, storage_manager=None):
        """
        Ingest into the storage system the supplied package, of the specified format, with the specified store_id.

        This will attempt to load a PackageHandler for the format around the zip_file.  Then the original
        zip file and the metadata files extracted from the package by the PackageHandler will be written
        to the storage system with the specified id.

        If a storage_manager is provided, that will be used as the interface to the storage system,
        otherwise a storage manager will be constructed from the StoreFactory.

        Once this method completes, the file held at zip_file will be deleted, and the definitive copy
        will be available in the store.

        :param store_id: the id to use when storing the package
        :param zip_path: locally accessible path to the source package on disk
        :param format: format identifier for the package handler.  As seen in the configuration.
        :param storage_manager: an instance of Store to use as the storage API
        """
        app.logger.debug("Package Ingest - StoreID:{a}; Format:{b}".format(a=store_id, b=format))

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
        """
        Extract notification metadata and match data from the package in the store which has the specified format

        This will look in the store for the store_id, and look for files which match the known metadata file
        names from the PackageHandler which is referenced by the format.  Once those files are found, they are loaded
        into the PackageHandler and the metadata and match data extracted and returned.

        If a storage_manager is provided, that will be used as the interface to the storage system,
        otherwise a storage manager will be constructed from the StoreFactory.

        :param store_id: the storage id where this object can be found
        :param format: format identifier for the package handler.  As seen in the configuration.
        :param storage_manager: an instance of Store to use as the storage API
        :return: a tuple of (NotificationMetadata, RoutingMetadata) representing the metadata stored in the package
        """
        app.logger.debug("Package Extract - StoreID:{a}; Format:{b}".format(a=store_id, b=format))

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
        """
        For the package held in the store at the specified store_id, convert the package from
        the source_format to the target_format.

        This will make a local copy of the source package from the storage system, make all
        the relevant conversions (also locally), and then synchronise back to the store.

        If a storage_manager is provided, that will be used as the interface to the storage system,
        otherwise a storage manager will be constructed from the StoreFactory.

        :param store_id: the storage id where this object can be found
        :param source_format: format identifier for the input package handler.  As seen in the configuration.
        :param target_format: format identifier for the output package handler.  As seen in the configuration.
        :param storage_manager: an instance of Store to use as the storage API
        :return: a list of tuples of the conversions carried out of the form [(format, filename, url name)]
        """
        app.logger.debug("Package Convert - StoreID:{a}; SourceFormat:{b}; TargetFormats:{c}".format(a=store_id, b=source_format, c=",".join(target_formats)))

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
        """
        Construct a new PackageHandler around the zip file and/or the metadata files.

        Metadata file handles should be of the form

        ::

            [("filename", <file handle>)]

        :param zip_path:
        :param metadata_files:
        :return:
        """
        self.zip_path = zip_path
        self.metadata_files = metadata_files
        self.zip = None

    ################################################
    ## methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer

        :return: the name of the zip file
        """
        raise NotImplementedError()

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager

        :return: the names of the metadata files
        """
        raise NotImplementedError()

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls

        :return: the url name
        """
        raise NotImplementedError()

    ################################################
    ## Methods for retriving data from the actual package

    def metadata_streams(self):
        """
        A generator which yields tuples of metadata file names and data streams

        :return: generator for file names/data streams
        """
        for x in []:
            yield None, None

    def notification_metadata(self):
        """
        Get the notification metadata as extracted from the package

        :return: NotificationMetadata populated
        """
        return models.NotificationMetadata()

    def match_data(self):
        """
        Get the match data as extracted from the package

        :return: RoutingMetadata populated
        """
        return models.RoutingMetadata()

    def convertible(self, target_format):
        """
        Can this handler convert to the specified format

        :param target_format: format we may want to convert to
        :return: True/False if this handler supports that output format
        """
        return False

    def convert(self, in_path, target_format, out_path):
        """
        Convert the file at the specified in_path to a package file of the
        specified target_format at the out_path.

        You should check first that this target_format is supported via convertible()

        :param in_path: locally accessible file path to the source package
        :param target_format: the format identifier for the format we want to convert to
        :param out_path: locally accessible file path for the output to be written
        :return: True/False on success/fail
        """
        return False

class SimpleZip(PackageHandler):
    """
    Very basic class for representing the SimpleZip package format

    SimpeZip is identified by the format identifier http://purl.org/net/sword/package/SimpleZip
    """

    ################################################
    ## methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer

        In this case it is SimpleZip.zip

        :return: filename
        """
        return "SimpleZip.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager

        In this case there are none

        :return: list of names
        """
        return []

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls

        In this case SimpleZip

        :return: url name
        """
        return "SimpleZip"


############################################################################
# 2017-03-21 TD : Additional PackageHandler for OPUS4Zip package format
#
class OPUS4Zip(PackageHandler):
    """
    Basic class for representing the OPUS4Zip package format

    OPUS4Zip is identified by the format identifier http://purl.org/net/sword/package/OPUS4Zip
    """

    ################################################
    ## methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer

        In this case it is OPUS4Zip.zip

        :return: filename
        """
        return "OPUS4Zip.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager

        In this case there are none

        :return: list of names
        """
        return []

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls

        In this case OPUS4Zip

        :return: url name
        """
        return "OPUS4Zip"
#
############################################################################


class FilesAndJATS(PackageHandler):
    """
    Class for representing the FilesAndJATS format

    You should use the format identifier: https://datahub.deepgreen.org/FilesAndJATS
    ## You should use the format identifier: https://pubrouter.jisc.ac.uk/FilesAndJATS

    This is the default format that we currently prefer to get from
    providers.  It consists of a zip of a single XML file which is the JATS fulltext,
    a single PDF which is the fulltext, and an arbitrary number of other
    files which are supporting information.  It may also contain the NLM/EPMC
    formatted metadata as XML

    To be valid, the zip must just consist of the JATS file OR the EPMC metadata file.
    All other files are optional
    """
    def __init__(self, zip_path=None, metadata_files=None):
        """
        Construct a new PackageHandler around the zip file and/or the metadata files.

        Metadata file handles should be of the form

        ::

            [("filename", <file handle>)]

        :param zip_path: locally accessible path to zip file
        :param metadata_files: metadata file handles tuple
        :return:
        """
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

        In this case FilesAndJATS.zip

        :return: filname
        """
        return "FilesAndJATS.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager

        In this case ["filesandjats_jats.xml", "filesandjats_epmc.xml"]

        :return: list of metadata files
        """
        return ["filesandjats_jats.xml", "filesandjats_epmc.xml"]

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls

        In this case FilesAndJATS

        :return: url name
        """
        return "FilesAndJATS"

    ################################################
    ## Overrids of methods for retriving data from the actual package

    def metadata_streams(self):
        """
        A generator which yields tuples of metadata file names and data streams

        In this handler, this will yield up to 2 metadata streams; for "filesandjats_jats.xml" and "filesandjats_epmc.xml",
        in that order, where there is a stream present for that file.

        :return: generator for file names/data streams
        """
        sources = [("filesandjats_jats.xml", self.jats), ("filesandjats_epmc.xml", self.epmc)]
        for n, x in sources:
            if x is not None:
                yield n, StringIO(x.tostring())

    def notification_metadata(self):
        """
        Get the notification metadata as extracted from the package

        This will extract metadata from both of the JATS XML and the EPMC XML, whichever is present
        and merge them before responding.

        :return: NotificationMetadata populated
        """
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
        """
        Get the match data as extracted from the package

        This will extract match data from both of the JATS XML and the EPMC XML, whichever is present
        and merge them before responding.

        :return: RoutingMetadata populated
        """
        match = models.RoutingMetadata()

        # extract all the relevant match data from epmc
        if self.epmc is not None:
            self._epmc_match_data(match)

        # extract all the relevant match data from jats
        if self.jats is not None:
            self._jats_match_data(match)

        return match

    def convertible(self, target_format):
        """
        Checks whether this handler can do the conversion to the target format.

        This handler currently supports the following conversion formats:

        * http://purl.org/net/sword/package/SimpleZip
        * http://purl.org/net/sword/package/OPUS4Zip

        :param target_format: target format
        :return: True if in the above list, else False
        """
        # 2017-03-21 TD : added another zip format (here: OPUS4Zip)
        return target_format in ["http://purl.org/net/sword/package/SimpleZip",
                                 "http://purl.org/net/sword/package/OPUS4Zip"]

    def convert(self, in_path, target_format, out_path):
        """
        Convert the file at the specified in_path to a package file of the
        specified target_format at the out_path.

        You should check first that this target_format is supported via convertible()

        This handler currently supports the following conversion formats:

        * http://purl.org/net/sword/package/SimpleZip
        * http://purl.org/net/sword/package/OPUS4Zip

        :param in_path: locally accessible file path to the source package
        :param target_format: the format identifier for the format we want to convert to
        :param out_path: locally accessible file path for the output to be written
        :return: True/False on success/fail
        """
        # 2017-03-21 TD : additional handling of a new format (here: OPUS4Zip)
        if target_format == "http://purl.org/net/sword/package/SimpleZip":
            self._simple_zip(in_path, out_path)
            return True
        elif target_format == "http://purl.org/net/sword/package/OPUS4Zip":
            self._opus4_zip(in_path, out_path)
            return True
        return False

    ################################################
    ## Internal methods

    def _simple_zip(self, in_path, out_path):
        """
        convert to simple zip

        :param in_path:
        :param out_path:
        :return:
        """
        # files and jats are already basically a simple zip, so a straight copy
        shutil.copyfile(in_path, out_path)


    # 2017-03-21 TD : added an internal method converting to OPUS4 zip format;
    #                 basically by invoking an xslt transformation of the xml metadata 
    def _opus4_zip(self, in_path, out_path):
        """
        convert to OPUS4 zip

        :param in_path:
        :param out_path:
        :return:
        """
        # 2017-03-21 TD :
        # files and jats are already basically a OPUS4 zip, so a straight copy
        # well, almost...
        app.logger.debug("PackageHandler FilesAndJATS._opus4_zip(): ... copying {x} to {y}.".format(x=in_path,y=out_path))
        parser = etree.XMLParser(load_dtd=True, no_network=False)
        shutil.copyfile(in_path, out_path)


    def _merge_metadata(self, emd, jmd):
        """
        Merge the supplied EMPC and JATS metadata records into one

        :param emd:
        :param jmd:
        :return:
        """
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
        """
        Extract metadata from the JATS file

        :return:
        """
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
        """
        Extract metadata from the EPMC XML

        :return:
        """
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
        """
        Extract match data from the JATS XML

        :param match:
        :return:
        """
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
                # 2017-01-19 TD : not needed in DeepGreen
                #
                # codes = postcode.extract_all(a)
                # for code in codes:
                #     match.add_postcode(code)

        # other keywords
        for k in self.jats.keywords:
            match.add_keyword(k)

        # other email addresses
        for e in self.jats.emails:
            match.add_email(e)

    def _epmc_match_data(self, match):
        """
        Extract match data from the EPMC XML

        :param match:
        :return:
        """
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
                # 2017-01-19 TD : not needed in DeepGreen
                #
                # codes = postcode.extract_all(aff)
                # for code in codes:
                #     match.add_postcode(code)

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
        """
        Load the properties for this handler from the file metadata

        :return:
        """
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
        """
        Load the properties for this handler from a zip file

        :return:
        """
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
        """
        List the XML files in the zip file

        :return:
        """
        if self.zip is None:
            return []
        xmls = []
        for name in self.zip.namelist():
            if name.endswith(".xml"):
                xmls.append(name)
        return xmls

    def _set_epmc(self, xml):
        """
        set the local EMPC property on this object based on the xml document passed in

        :param xml:
        :return:
        """
        if xml.tag == "resultList":
            res = xml.find("result")
            if res is not None:
                self.epmc = EPMCMetadataXML(xml=res)
            else:
                raise PackageException("Unable to find result element in EPMC resultList")
        elif xml.tag == "result":
            self.epmc = EPMCMetadataXML(xml=xml)

    def _set_jats(self, xml):
        """
        Set the local JATS property on this object based on the xml document passed in
        :param xml:
        :return:
        """
        self.jats = JATS(xml=xml)

    def _is_valid(self):
        """
        Is this package valid as FilesAndJATS?

        :return:
        """
        # is valid if either one or both of jats/epmc is not none
        return self.jats is not None or self.epmc is not None


class FilesAndRSC(PackageHandler):
    """
    Class for representing the FilesAndRSC format

    You should use the format identifier: https://datahub.deepgreen.org/FilesAndRSC

    This is the format that we prefer to get from (the?) RSC provider(s).  It consists 
    of a zip of a single XML file which is the RSC metadata, a single PDF which is the 
    fulltext, and an arbitrary number of other files which are supporting information.  

    To be valid, the zip must just consist of the RSC metadata file.
    All other files are optional
    """
    def __init__(self, zip_path=None, metadata_files=None):
        """
        Construct a new PackageHandler around the zip file and/or the metadata files.

        Metadata file handles should be of the form

        ::

            [("filename", <file handle>)]

        :param zip_path: locally accessible path to zip file
        :param metadata_files: metadata file handles tuple
        :return:
        """
        super(FilesAndRSC, self).__init__(zip_path=zip_path, metadata_files=metadata_files)

        self.rsc_xml = None

        if self.zip_path is not None:
            self._load_from_zip()
        elif self.metadata_files is not None:
            self._load_from_metadata()

    ################################################
    ## Overrides of methods for exposing naming information

    def zip_name(self):
        """
        Get the name of the package zip file to be used in the storage layer

        In this case FilesAndRSC.zip

        :return: filname
        """
        return "FilesAndRSC.zip"

    def metadata_names(self):
        """
        Get a list of the names of metadata files extracted and stored by this packager

        In this case ["filesandrsc_rsc.xml"]

        :return: list of metadata files
        """
        return ["filesandrsc_rsc.xml"]

    def url_name(self):
        """
        Get the name of the package as it should appear in any content urls

        In this case FilesAndRSC

        :return: url name
        """
        return "FilesAndRSC"

    ################################################
    ## Overrids of methods for retriving data from the actual package

    def metadata_streams(self):
        """
        A generator which yields tuples of metadata file names and data streams

        In this handler, this will yield one metadata streams: for "filesandrsc_rsc.xml".

        :return: generator for file names/data streams
        """
        sources = [("filesandrsc_rsc.xml", self.rsc_xml)]
        for n, x in sources:
            if x is not None:
                yield n, StringIO(x.tostring())

    def notification_metadata(self):
        """
        Get the notification metadata as extracted from the package

        This will extract metadata of the RSC XML.

        :return: NotificationMetadata populated
        """
        rmd = None

        # extract all the relevant data from rsc_xml
        if self.rsc_xml is not None:
            rmd = self._rsc_metadata()

        return self._merge_metadata(None, rmd)

    def match_data(self):
        """
        Get the match data as extracted from the package

        This will extract match data of the RSC XML.

        :return: RoutingMetadata populated
        """
        match = models.RoutingMetadata()

        # extract all the relevant match data from jats
        if self.rsc_xml is not None:
            self._rsc_match_data(match)

        return match

    def convertible(self, target_format):
        """
        Checks whether this handler can do the conversion to the target format.

        This handler currently supports the following conversion formats:

        * http://purl.org/net/sword/package/SimpleZip

        :param target_format: target format
        :return: True if in the above list, else False
        """
        return target_format in ["http://purl.org/net/sword/package/SimpleZip"]

    def convert(self, in_path, target_format, out_path):
        """
        Convert the file at the specified in_path to a package file of the
        specified target_format at the out_path.

        You should check first that this target_format is supported via convertible()

        This handler currently supports the following conversion formats:

        * http://purl.org/net/sword/package/SimpleZip

        :param in_path: locally accessible file path to the source package
        :param target_format: the format identifier for the format we want to convert to
        :param out_path: locally accessible file path for the output to be written
        :return: True/False on success/fail
        """
        if target_format == "http://purl.org/net/sword/package/SimpleZip":
            self._simple_zip(in_path, out_path)
            return True
        return False

    ################################################
    ## Internal methods

    def _simple_zip(self, in_path, out_path):
        """
        convert to simple zip

        :param in_path:
        :param out_path:
        :return:
        """
        # files and rsc are already basically a simple zip, so a straight copy
        shutil.copyfile(in_path, out_path)

    def _merge_metadata(self, emd, rmd):
        """
        Merge the supplied None (==EMPC) and RSC metadata records into one

        :param emd:
        :param rmd:
        :return:
        """
        if emd is None:
            emd = models.NotificationMetadata()
        if rmd is None:
            rmd = models.NotificationMetadata()

        md = models.NotificationMetadata()

        md.title = rmd.title if rmd.title is not None else emd.title
        md.publisher = rmd.publisher
        md.type = emd.type
        md.language = emd.language
        md.publication_date = emd.publication_date if emd.publication_date is not None else rmd.publication_date
        md.date_accepted = rmd.date_accepted
        md.date_submitted = rmd.date_submitted
        md.license = rmd.license

        for id in emd.identifiers:
            md.add_identifier(id.get("id"), id.get("type"))
        for id in rmd.identifiers:
            md.add_identifier(id.get("id"), id.get("type"))

        md.authors = rmd.authors if len(rmd.authors) > 0 else emd.authors
        md.projects = emd.projects

        for s in emd.subjects:
            md.add_subject(s)
        for s in rmd.subjects:
            md.add_subject(s)

        return md

    def _rsc_metadata(self):
        """
        Extract metadata from the RSC XML

        :return:
        """
        md = models.NotificationMetadata()

        md.title = self.rsc_xml.title
        md.publisher = self.rsc_xml.publisher
        md.publication_date = self.rsc_xml.publication_date
        md.date_accepted = self.rsc_xml.date_accepted
        md.date_submitted = self.rsc_xml.date_submitted

        type, url, _ = self.rsc_xml.get_licence_details()
        md.set_license(type, url)

        for issn in self.rsc_xml.issn:
            md.add_identifier(issn, "issn")

        md.add_identifier(self.rsc_xml.pmcid, "pmcid")
        md.add_identifier(self.rsc_xml.doi, "doi")

        for author in self.rsc_xml.authors:
            name = author.get("fname", "") + " " + author.get("surname", "")
            if name.strip() == "":
                continue
            affs = "; ".join(author.get("affiliations", []))
            obj = {"name" : name}
            if affs is not None and affs != "":
                obj["affiliation"] = affs
            md.add_author(obj)

        for kw in self.rsc_xml.categories:
            md.add_subject(kw)
        for kw in self.rsc_xml.keywords:
            md.add_subject(kw)

        return md

    def _rsc_match_data(self, match):
        """
        Extract match data from the RSC XML

        :param match:
        :return:
        """
        # subject keywords
        for c in self.rsc_xml.categories:
            match.add_keyword(c)

        # individual authors, emails, affiliations
        for a in self.rsc_xml.contribs:
            # name
            name = a.get("fname", "") + " " + a.get("surname", "")
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
                # 2016-11-29 TD : skip postcode extraction since
                #                 it is not needed in DeepGreen
                # codes = postcode.extract_all(a)
                # for code in codes:
                #     match.add_postcode(code)

        # other keywords
        for k in self.rsc_xml.keywords:
            match.add_keyword(k)

        # other email addresses
        for e in self.rsc_xml.emails:
            match.add_email(e)

    def _load_from_metadata(self):
        """
        Load the properties for this handler from the file metadata

        :return:
        """
        for name, stream in self.metadata_files:
            if name == "filesandrsc_rsc.xml":
                try:
                    # 2016-11-30 TD : we need some XMLParser settings here... (don't ask!)
                    parser = etree.XMLParser(load_dtd=True, no_network=False)
                    xml = etree.fromstring(stream.read(), parser)
                    self._set_rsc(xml)
                except Exception:
                    raise PackageException("Unable to parse filesandrsc_rsc.xml file from store")

        if not self._is_valid():
            raise PackageException("No valid RSC metadata found in .xml file")

    def _load_from_zip(self):
        """
        Load the properties for this handler from a zip file

        :return:
        """
        try:
            self.zip = zipfile.ZipFile(self.zip_path, "r", allowZip64=True)
        except zipfile.BadZipfile as e:
            raise PackageException("Zip file is corrupt - cannot read.")

        for x in self._xml_files():
            try:
                # 2016-11-30 TD : we need some XMLParser settings here... (don't ask!)
                parser = etree.XMLParser(load_dtd=True, no_network=False)
                doc = etree.fromstring(self.zip.open(x).read(), parser)
            except Exception:
                raise PackageException("Unable to parse XML file in package {x}".format(x=x))

            if doc.tag == "article":
                self._set_rsc(doc)

        if not self._is_valid():
            raise PackageException("No RSC metadata found in package")

    def _xml_files(self):
        """
        List the XML files in the zip file

        :return:
        """
        if self.zip is None:
            return []
        xmls = []
        for name in self.zip.namelist():
            if name.endswith(".xml"):
                xmls.append(name)
        return xmls

    def _set_rsc(self, xml):
        """
        Set the local RSC XML property on this object based on the xml document passed in
        :param xml:
        :return:
        """
        self.rsc_xml = RSCMetadataXML(xml=xml)

    def _is_valid(self):
        """
        Is this package valid as FilesAndRSC?

        :return:
        """
        # is valid if rsc_xml is not none
        return self.rsc_xml is not None 
