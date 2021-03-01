"""
Functions which lists all the licenses associated with a repository account
Matched on the account's Bibid and the participant list associated with licenses.
"""

from service import models


def get_matching_licenses(account_id):
    account = models.Account.pull(account_id)
    licences = []
    if account.has_role('repository'):
        alliances = models.Alliance.pull_by_participant_id(account.repository_bibid)
        rec = models.RepositoryConfig.pull_by_repo(account_id)
        if not alliances:
            return licences
        for alliance in alliances:
            license = models.License.pull(alliance.license_id)
            checked = True
            if license.id in rec.excluded_license:
                checked = False
            licences += [{"id": license.id, "name": license.name, "type": license.type, "checked": checked}]
    return licences
