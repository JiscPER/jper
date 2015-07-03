from octopus.lib import dates
from service import packages, models
import esprit

class RoutingException(Exception):
    pass

def route(unrouted):
    # first get the packaging system to load and retrieve all the metadata
    # and match data
    try:
        metadata, match_data = packages.PackageManager.extract(unrouted.id, unrouted.packaging_format)
    except packages.PackageException as e:
        raise RoutingException(e.message)

    # iterate through all the repository configs, collecting match provenance and
    # id information
    # FIXME: at the moment this puts all the provenance in memory and then writes it all
    # in one go later.  Probably that's OK, but it will depend on the number of fields the
    # repository matches and the number of repositories as to how big this gets.
    match_provenance = []
    match_ids = []
    try:
        for rc in models.RepositoryConfig.scroll(page_size=10, keepalive="1m"):
            provs = match(match_data, rc)
            if provs is not None and len(provs) > 0:
                match_provenance += provs
                match_ids.append(rc.repository)

    except esprit.tasks.ScrollException as e:
        raise RoutingException(e.message)

    # write all the match provenance out to the index (could be an empty list)
    for p in match_provenance:
        p.save()

    # if there are matches, update the record with the information, and then
    # write it to the index
    if len(match_ids) > 0:
        routed = unrouted.make_routed()
        routed.repositories = match_ids
        routed.analysis_date = dates.now()
        enhance(routed, metadata)
        links(routed)
        routed.save()

def match(notification_data, repository_config):
    """
    Match the incoming notification data, to the repository config and determine
    if there is a match

    :param notification_data:   models.RoutingMetadata
    :param repository_config:   models.RepositoryConfig
    :return:  list of models.MatchProvenance objects, or None if no match
    """
    # FIXME: can't implement this until we know more about the RepositoryConfig
    return []

def enhance(routed, metadata):
    """
    Enhance the routed notification with the extracted metadata

    :param routed:
    :param metadata:
    :return:
    """
    pass

def links(routed):
    """
    Set the links on the routed object to provide the fulltext download
    in the event that it is hosted by the router

    :param routed:
    :return:
    """
    pass