"""
Functions which lists all the licenses associated with a repository account
Matched on the account's Bibid and the participant list associated with licenses.
"""

from service import models


def get_matching_licenses(account_id):
    account = models.Account.pull(account_id)
    matching_licenses = []
    if not account.has_role('repository'):
        return []
    # Get repository config for account
    rec = models.RepositoryConfig.pull_by_repo(account_id)
    # Get all matching license from alliance (participant) data
    alliances = models.Alliance.pull_by_participant_id(account.repository_bibid) or []
    alliances = (alli for alli in alliances if alli.is_active())
    licenses = (models.License.pull(alliance.license_id) for alliance in alliances)
    licenses = filter(None, licenses)
    licenses = (lic for lic in licenses if lic.is_active())
    matching_licenses.extend(licenses)

    # Get all gold licences if it isn't a subject repository
    if not account.has_role('subject_repository'):
        gold_licences = models.License.pull_by_key('type', 'gold') or []
        gold_licences = filter(None, gold_licences)
        gold_licences = (lic for lic in gold_licences if lic.is_active())
        matching_licenses.extend(gold_licences)

    # prepare list of matching licenses with preferred information
    licenses = []
    for license in matching_licenses:
        if license.id in [l['id'] for l in licenses]:
            continue
        checked = True
        if rec and license.id in rec.excluded_license:
            checked = False
        licenses += [{"id": license.id, "name": license.name, "type": license.type, "checked": checked}]
    return licenses
