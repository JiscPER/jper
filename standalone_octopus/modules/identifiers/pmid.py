import re

def normalise(pmid):

    pmid = pmid.strip()
    rx = "^[\d]{1,8}$"
    pmid = pmid.lower()

    if pmid.startswith("pmid"):
        pmid = pmid.replace("pmid", "")

    if pmid.startswith(":"):
        pmid = pmid.replace(":", "")

    result = re.match(rx, pmid)
    if result is None:
        raise ValueError(pmid + " does not seem to be a valid PMID")

    return pmid
