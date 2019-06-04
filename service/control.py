"""
Module which controls the active role of accounts
"""
from service import models


def activate_account(acc_id):
    """
    Activate the repository.

    This sets the repository role to "active", which in turn means the router will
    pick up this account and run deposits against the repo.

    :param acc_id: account to activate
    :return:
    """
    # see if there's a repository for this account
    acc = models.Account.pull(acc_id)

    # if there is one, turn it on
    if acc is not None and acc.has_role('repository'):
        acc.set_active()
        acc.save()


def deactivate_account(acc_id):
    """
    Deactivate the repository.

    This sets the repository role to "passive", which in turn means the router will ignore this
    account in its normal run

    :param acc_id: account to deactivate
    :return:
    """
    # see if there's a repository for this account
    acc = models.Account.pull(acc_id)

    # if there is one, switch if off (i.e. deactivate it for the time being)
    if acc is not None and acc.has_role('repository'):
        acc.set_passive()
        acc.save()

