"""
Functions which lists all the licenses associated with a repository account
Matched on the account's Bibid and the participant list associated with licenses.
"""

from service import models


def get_matching_licenses(account_id):
    account = models.Account.pull(account_id)
    licences = []
    if account.has_role('repository'):
        # Get repository config for account
        rec = models.RepositoryConfig.pull_by_repo(account_id)
        # Get all matching license from alliance (participant) data
        alliances = models.Alliance.pull_by_participant_id(account.repository_bibid)
        if not alliances:
            alliances = []
        for alliance in alliances:
            license = models.License.pull(alliance.license_id)
            if not license:
                continue
            checked = True
            if rec and license.id in rec.excluded_license:
                checked = False
            licences += [{"id": license.id, "name": license.name, "type": license.type, "checked": checked}]
        if not account.has_role('subject_repository'):
            # Get all gold licences
            gold_licences = models.License.pull_by_key('type', 'gold')
            if not gold_licences:
                gold_licences = []
            for license in gold_licences:
                checked = True
                if rec and license.id in rec.excluded_license:
                    checked = False
                licences += [{"id": license.id, "name": license.name, "type": license.type, "checked": checked}]
    return licences
