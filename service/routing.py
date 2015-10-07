from octopus.lib import dates
from octopus.modules.store import store
from service import packages, models
import esprit
from service.web import app
from flask import url_for
from copy import deepcopy
import uuid

class RoutingException(Exception):
    pass

def route(unrouted):
    app.logger.info("Routing - Notification:{y}".format(y=unrouted.id))

    # first get the packaging system to load and retrieve all the metadata
    # and match data from the content file (if it exists)
    try:
        metadata, pmd = packages.PackageManager.extract(unrouted.id, unrouted.packaging_format)
    except packages.PackageException as e:
        app.logger.info("Routing - Notification:{y} failed with error '{x}'".format(y=unrouted.id, x=e.message))
        raise RoutingException(e.message)

    # extract the match data from the notification and combine it with the match data from the package
    match_data = unrouted.match_data()
    if pmd is not None:
        match_data.merge(pmd)

    # iterate through all the repository configs, collecting match provenance and
    # id information
    # FIXME: at the moment this puts all the provenance in memory and then writes it all
    # in one go later.  Probably that's OK, but it will depend on the number of fields the
    # repository matches and the number of repositories as to how big this gets.
    match_provenance = []
    match_ids = []
    try:
        for rc in models.RepositoryConfig.scroll(page_size=10, keepalive="1m"):
            prov = models.MatchProvenance()
            prov.repository = rc.repository
            prov.notification = unrouted.id
            app.logger.info("Routing - Notification:{y} matching against Repository:{x}".format(y=unrouted.id, x=rc.repository))
            match(match_data, rc, prov)
            if len(prov.provenance) > 0:
                match_provenance.append(prov)
                match_ids.append(rc.repository)
                app.logger.info("Routing - Notification:{y} successfully matched Repository:{x}".format(y=unrouted.id, x=rc.repository))
            else:
                app.logger.info("Routing - Notification:{y} did not match Repository:{x}".format(y=unrouted.id, x=rc.repository))

    except esprit.tasks.ScrollException as e:
        app.logger.info("Routing - Notification:{y} failed with error '{x}'".format(y=unrouted.id, x=e.message))
        raise RoutingException(e.message)

    app.logger.info("Routing - Notification:{y} matched to {x} repositories".format(y=unrouted.id, x=len(match_ids)))

    # write all the match provenance out to the index (could be an empty list)
    for p in match_provenance:
        p.save()
        app.logger.info("Routing - Provenance:{z} written for Notification:{y} for match to Repisitory:{x}".format(x=p.repository, y=unrouted.id, z=p.id))

    # if there are matches then the routing is successful, and we want to finalise the
    # notification for the routed index and its content for download
    if len(match_ids) > 0:
        # repackage the content that came with the unrouted notification (if necessary) into
        # the formats required by the repositories for which there was a match
        pack_links = repackage(unrouted, match_ids)

        # update the record with the information, and then
        # write it to the index
        routed = unrouted.make_routed()
        for pl in pack_links:
            routed.add_link(pl.get("url"), pl.get("type"), pl.get("format"), pl.get("access"), pl.get("packaging"))
        routed.repositories = match_ids
        routed.analysis_date = dates.now()
        if metadata is not None:
            enhance(routed, metadata)
        links(routed)
        routed.save()
        app.logger.info("Routing - Notification:{y} successfully routed".format(y=unrouted.id))
        return True
    else:
        # log the failure
        app.logger.info("Routing - Notification:{y} was not routed".format(y=unrouted.id))

        # if config says so, convert the unrouted notification to a failed notification, enhance and save
        # for later diagnosis
        if app.config.get("KEEP_FAILED_NOTIFICATIONS", False):
            failed = unrouted.make_failed()
            failed.analysis_date = dates.now()
            if metadata is not None:
                enhance(failed, metadata)
            failed.save()
            app.logger.info("Routing - Notification:{y} as stored as a Failed Notification")

        return False

    # Note that we don't delete the unrouted notification here - that's for the caller to decide

def match(notification_data, repository_config, provenance):
    """
    Match the incoming notification data, to the repository config and determine
    if there is a match

    :param notification_data:   models.RoutingMetadata
    :param repository_config:   models.RepositoryConfig
    :return:  list of models.MatchProvenance objects, or None if no match
    """
    # just to give us a short-hand without compromising the useful names in the method sig
    md = notification_data
    rc = repository_config

    match_algorithms = {
        "domains" : {
            "urls" : domain_url,
            "emails" : domain_email
        },
        "name_variants" : {
            "affiliations" : exact_substring
        },
        "author_emails" : {
            "emails" : exact
        },
        "author_ids" : {
            "author_ids" : author_match
        },
        "postcodes" : {
            "postcodes" : postcode_match
        },
        "grants" : {
            "grants" : exact
        },
        "strings" : {
            "urls" : domain_url,
            "emails" : exact,
            "affiliations" : exact_substring,
            "author_ids" : author_string_match,
            "postcodes" : postcode_match,
            "grants" : exact
        }
    }

    repo_property_values = {
        "author_ids" : author_id_string
    }

    match_property_values = {
        "author_ids" : author_id_string
    }

    # do the required matches
    matched = False
    for repo_property, sub in match_algorithms.iteritems():
        for match_property, fn in sub.iteritems():
            for rprop in getattr(rc, repo_property):
                for mprop in getattr(md, match_property):
                    m = fn(rprop, mprop)
                    if m is not False:  # it will be a string then
                        matched = True

                        # convert the values that have matched to string values suitable for provenance
                        rval = repo_property_values.get(repo_property)(rprop) if repo_property in repo_property_values else rprop
                        mval = match_property_values.get(match_property)(mprop) if match_property in match_property_values else mprop

                        # record the provenance
                        provenance.add_provenance(repo_property, rval, match_property, mval, m)

    # if none of the required matches hit, then no need to look at the optional refinements
    if not matched:
        return False

    # do the match refinements
    # if the configuration specifies a keyword, it must match the notification data, otherwise
    # the match fails
    if len(rc.keywords) > 0:
        trip = False
        for rk in rc.keywords:
            for mk in md.keywords:
                m = exact(rk, mk)
                if m is not False: # then it is a string
                    trip = True
                    provenance.add_provenance("keywords", rk, "keywords", mk, m)
        if not trip:
            return False

    # as above, if the config requires a content type it must match the notification data or the match fails
    if len(rc.content_types) > 0:
        trip = False
        for rc in rc.content_types:
            for mc in md.content_types:
                m = exact(rc, mc)
                if m is True:
                    trip = True
                    provenance.add_provenance("content_types", rc, "content_types", mc, m)
        if not trip:
            return False

    return len(provenance.provenance) > 0

def enhance(routed, metadata):
    """
    Enhance the routed notification with the extracted metadata

    :param routed:
    :param metadata:
    :return:
    """
    # some of the fields are easy - we just want to accept the existing
    # value if it is set, otherwise take the value from the other metadata
    accept_existing = [
        "title", "version", "publisher", "source_name", "type",
        "language", "publication_date", "date_accepted", "date_submitted",
        "license"
    ]
    for ae in accept_existing:
        if getattr(routed, ae) is None and getattr(metadata, ae) is not None:
            setattr(routed, ae, getattr(metadata, ae))

    # add any new identifiers to the source identifiers
    mis = metadata.source_identifiers
    for id in mis:
        # the API prevents us from adding duplicates, so just add them all and let the model handle it
        routed.add_source_identifier(id.get("type"), id.get("id"))

    # add any new identifiers
    ids = metadata.identifiers
    for id in ids:
        routed.add_identifier(id.get("id"), id.get("type"))

    # add any new authors, using a slightly complex merge strategy:
    # 1. If both authors have identifiers and one matches, they are equivalent and missing name/affiliation/identifiers should be added
    # 2. If one does not have identifiers, match by name.
    # 3. If name matches, add any missing affiliation/identifiers
    mas = metadata.authors
    ras = routed.authors
    for ma in mas:
        for ra in ras:
            merged = _merge_entities(ra, ma, "name", other_properties=["affiliation"])
            if not merged:
                routed.add_author(ma)

    # merge project entities in with the same rule set as above
    mps = metadata.projects
    rps = routed.projects
    for mp in mps:
        for rp in rps:
            merged = _merge_entities(rp, mp, "name", other_properties=["grant_number"])
            if not merged:
                routed.add_project(mp)

    # add any new subjects
    for s in metadata.subjects:
        routed.add_subject(s)


def _merge_entities(e1, e2, primary_property, other_properties=None):
    if other_properties is None:
        other_properties = []

    # 1. If both entities have identifiers and one matches, they are equivalent and missing properties/identifiers should be added
    if e2.get("identifier") is not None and e1.get("identifier") is not None:
        for maid in e2.get("identifier"):
            for raid in e1.get("identifier"):
                if maid.get("type") == raid.get("type") and maid.get("id") == raid.get("id"):
                    # at this point we know that e1 is the same entity as e2
                    if e1.get(primary_property) is None and e2.get(primary_property) is not None:
                        e1[primary_property] = e2[primary_property]
                    for op in other_properties:
                        if e1.get(op) is None and e2.get(op) is not None:
                            e1[op] = e2[op]
                    for maid2 in e2.get("identifier"):
                        match = False
                        for raid2 in e1.get("identifier"):
                            if maid2.get("type") == raid2.get("type") and maid2.get("id") == raid2.get("id"):
                                match = True
                                break
                        if not match:
                            e1["identifier"].append(maid2)
                    return True

    # 2. If one does not have identifiers, match by primary property.
    # 3. If primary property matches, add any missing other properties/identifiers
    elif e2.get(primary_property) == e1.get(primary_property):
        for op in other_properties:
            if e1.get(op) is None and e2.get(op) is not None:
                e1[op] = e2[op]
        for maid2 in e2.get("identifier", []):
            match = False
            for raid2 in e1.get("identifier", []):
                if maid2.get("type") == raid2.get("type") and maid2.get("id") == raid2.get("id"):
                    match = True
                    break
            if not match:
                if "identifier" not in e1:
                    e1["identifier"] = []
                e1["identifier"].append(maid2)
        return True

    return False


def repackage(unrouted, repo_ids):
    # if there's no package format, there's no repackaging to be done
    if unrouted.packaging_format is None:
        return []

    pm = packages.PackageFactory.converter(unrouted.packaging_format)
    conversions = []
    for rid in repo_ids:
        acc = models.Account.pull(rid)
        if acc is None:
            # realistically this shouldn't happen, but if it does just carry on
            app.logger.warn("Repackaging - no account with id {x}; carrying on regardless".format(x=rid))
            continue
        for pack in acc.packaging:
            # if it's already in the conversion list, job done
            if pack in conversions:
                break

            # otherwise, if the package manager can convert it, also job done
            if pm.convertible(pack):
                conversions.append(pack)
                break

    if len(conversions) == 0:
        return []

    # at this point we have a de-duplicated list of all formats that we need to convert
    # the package to, that the package is capable of converting itself into
    #
    # this pulls everything from remote storage, runs the conversion, and then synchronises
    # back to remote storage
    done = packages.PackageManager.convert(unrouted.id, unrouted.packaging_format, conversions)

    links = []
    for d in done:
        with app.test_request_context():
            url = app.config.get("BASE_URL") + url_for("webapi.retrieve_content", notification_id=unrouted.id, content_id=d[2])
        links.append({
            "type": "package",
            "format" : "application/zip",
            "access" : "router",
            "url" : url,
            "packaging" : d[0]
        })

    return links

def links(routed):
    newlinks = []
    for link in routed.links:
        if link.get('access') == 'public':
            nl = deepcopy(link)
            nid = uuid.uuid4().hex
            link['proxy'] = nid
            nl['access'] = 'router'
            with app.test_request_context():
                nl['url'] = app.config.get("BASE_URL") + url_for("webapi.proxy_content", notification_id=routed.id, pid=nid)
            newlinks.append(nl)
    for l in newlinks:
        routed.add_link(l.get("url"), l.get("type"), l.get("format"), l.get("access"), l.get("packaging"))
            


###########################################################
## Individual match functions

def domain_url(domain, url):
    """
    normalise the domain: strip prefixes and URL paths.  If either ends with the other, it is a match

    :param domain:
    :param url:
    :return:
    """
    # keep a copy of these for the provenance reporting
    od = domain
    ou = url

    # strip the common possible prefixes
    prefixes = ["http://", "https://"]
    for p in prefixes:
        if domain.startswith(p):
            domain = domain[len(p):]
        if url.startswith(p):
            url = url[len(p):]

    # strip everything after a path separator
    domain = domain.split("/")[0]
    url = url.split("/")[0]

    # now do the standard normalisation
    domain = _normalise(domain)
    url = _normalise(url)

    if domain.endswith(url) or url.endswith(domain):
        return "Domain matched URL: '{d}' and '{u}' have the same root domains".format(d=od, u=ou)

    return False

def domain_email(domain, email):
    """
    normalise the domain: strip prefixes an URL paths.  Normalise the email: strip everything before @.  If either ends with the other it is a match

    :param domain:
    :param email:
    :return:
    """
    # keep a copy of these for the provenance reporting
    od = domain
    oe = email

    # strip the common possible prefixes
    prefixes = ["http://", "https://"]
    for p in prefixes:
        if domain.startswith(p):
            domain = domain[len(p):]

    # strip everything after a path separator
    domain = domain.split("/")[0]

    # strip everything before @
    bits = email.split("@")
    if len(bits) > 1:
        email = bits[1]

    # now do the standard normalisation
    domain = _normalise(domain)
    email = _normalise(email)

    if domain.endswith(email) or email.endswith(domain):
        return "Domain matched email address: '{d}' and '{e}' have the same root domains".format(d=od, e=oe)

    return False

def author_match(author_obj_1, author_obj_2):
    """
    Match two author objects against eachother

    :param author_obj_1:
    :param author_obj_2:
    :return:
    """
    t1 = author_obj_1.get("type", "")
    i1 = _normalise(author_obj_1.get("id", ""))

    t2 = author_obj_2.get("type", "")
    i2 = _normalise(author_obj_2.get("id", ""))

    if t1 == t2 and i1 == i2:
        return "Author ids matched: {t1} '{i1}' is the same as {t2} '{i2}'".format(t1=t1, i1=author_obj_1.get("id", ""), t2=t2, i2=author_obj_2.get("id", ""))

    return False

def author_string_match(author_string, author_obj):
    """
    Match an arbitrary string against the id in the author object

    :param author_string:
    :param author_obj:
    :return:
    """
    ns = _normalise(author_string)
    nid = _normalise(author_obj.get("id", ""))

    if ns == nid:
        return "Author ids matched: '{s}' is the same as '{aid}'".format(s=author_string, aid=author_obj.get("id", ""))

    return False

def postcode_match(pc1, pc2):
    """
    Normalise postcodes: strip whitespace and lowercase, then exact match required
    :param pc1:
    :param pc2:
    :return:
    """
    # first do the usual normalisation
    npc1 = _normalise(pc1)
    npc2 = _normalise(pc2)

    # then go the final step and remove all the spaces
    npc1 = npc1.replace(" ", "")
    npc2 = npc2.replace(" ", "")

    if npc1 == npc2:
        return "Postcodes matched: '{a}' is the same as '{b}'".format(a=pc1, b=pc2)

    return False

def exact_substring(s1, s2):
    """
    normalised s1 must be an exact substring of normalised s2
    :param s1:
    :param s2:
    :return:
    """
    # keep a copy of these for the provenance reporting
    os1 = s1
    os2 = s2

    # normalise the strings
    s1 = _normalise(s1)
    s2 = _normalise(s2)

    if s1 in s2:
        return "'{a}' appears in '{b}'".format(a=os1, b=os2)

    return False

def exact(s1, s2):
    """
    normalised s1 must be identical to normalised s2

    :param s1:
    :param s2:
    :return:
    """
    # keep a copy of these for the provenance reporting
    os1 = s1
    os2 = s2

    # normalise the strings
    s1 = _normalise(s1)
    s2 = _normalise(s2)

    if s1 == s2:
        return "'{a}' is an exact match with '{b}'".format(a=os1, b=os2)

    return False

def _normalise(s):
    if s is None:
        return ""
    s = s.strip().lower()
    while "  " in s:    # two spaces
        s = s.replace("  ", " ")    # reduce two spaces to one
    return s


####################################################
# Functions for turning objects into their string representations

def author_id_string(aob):
    return "{x}: {y}".format(x=aob.get("type"), y=aob.get("id"))