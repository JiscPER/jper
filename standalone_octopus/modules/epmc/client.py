from standalone_octopus.core import app
from standalone_octopus.lib import http
import urllib.request, urllib.parse, urllib.error, string
from lxml import etree
from standalone_octopus.modules.epmc import models

def quote(s, **kwargs):
    try:
        return urllib.parse.quote_plus(s, **kwargs)
    except:
        pass

    try:
        utf = s.encode("utf-8")
        return urllib.parse.quote(utf, **kwargs)
    except:
        return None

def to_keywords(s):
    # FIXME: this method does not strip stop words - investigations into that indicate that as a natural language
    # processing thing, the libraries required to do it are awkward and overblown for our purposes.

    # translate out all of the punctuation
    exclude = set(string.punctuation)
    raw = ''.join(ch if ch not in exclude else " " for ch in s)

    # normalise the spacing
    return " ".join([x for x in raw.split(" ") if x != ""])

class EuropePMCException(Exception):
    def __init__(self, httpresponse=None, *args, **kwargs):
        super(EuropePMCException, self).__init__(*args, **kwargs)
        self.response = httpresponse

class EuropePMC(object):
    @classmethod
    def get_by_pmcid(cls, pmcid, page=1):
        return cls.field_search("PMCID", pmcid, page=page)

    @classmethod
    def get_by_pmid(cls, pmid, page=1):
        return cls.field_search("EXT_ID", pmid, page=page)

    @classmethod
    def get_by_doi(cls, doi, page=1):
        return cls.field_search("DOI", doi, page=page)

    @classmethod
    def title_exact(cls, title, page=1):
        return cls.field_search("TITLE", title, page=page)

    @classmethod
    def title_approximate(cls, title, page=1):
        nt = to_keywords(title)
        return cls.field_search("TITLE", nt, fuzzy=True, page=page)

    @classmethod
    def field_search(cls, field, value, fuzzy=False, page=1):
        wrap = "\"" if not fuzzy else ""
        quoted = quote(value, safe="/")
        qpage = quote(str(page))
        if quoted is None or qpage is None:
            raise EuropePMCException(None, "unable to url escape the string")

        url = app.config.get("EPMC_REST_API") + "search/query=" + field + ":" + wrap + quoted + wrap
        url += "&resultType=core&format=json&page=" + qpage
        app.logger.debug("Requesting EPMC metadata from " + url)

        resp = http.get(url)
        if resp is None:
            raise EuropePMCException(message="could not get a response from EPMC")
        if resp.status_code != 200:
            raise EuropePMCException(resp)

        try:
            j = resp.json()
        except:
            raise EuropePMCException(message="could not decode JSON from EPMC response")

        results = [models.EPMCMetadata(r) for r in j.get("resultList", {}).get("result", [])]
        return results

    @classmethod
    def fulltext(cls, pmcid):
        url = app.config.get("EPMC_REST_API") + pmcid + "/fullTextXML"
        app.logger.debug("Searching for Fulltext at " + url)
        resp = http.get(url)
        if resp is None:
            raise EuropePMCException(message="could not get a response for fulltext from EPMC")
        if resp.status_code != 200:
            raise EuropePMCException(resp)
        return EPMCFullText(resp.text)

class EPMCFullText(models.JATS):
    """
    For backwards compatibility - don't add any methods here
    """
    pass
