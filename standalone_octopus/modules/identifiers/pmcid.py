import re

def normalise(pmcid):
    pmcid = pmcid.strip()
    rx = r"^(PMC){0,1}[\d]{5,7}$"

    if not pmcid.startswith("PMC"):
        pmcid = "PMC" + pmcid

    result = re.match(rx, pmcid)

    if result is None:
        raise ValueError(pmcid + " does not seem to be a valid PMCID")

    return pmcid