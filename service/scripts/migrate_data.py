import esprit
import logging
from service import models


def old_es_connection():
    # Old ES data
    host = 'localhost'
    port = '9200'
    index = 'jper'
    verify_ssl = False
    index_per_type = False
    return esprit.raw.Connection(host, index, port=port, verify_ssl=verify_ssl, index_per_type=index_per_type)


def types_with_data(conn, logging):
    # return each index type with data and count of records to be transferred

    index_types = esprit.raw.list_types(conn)
    index_types.remove('_default_')
    index_types.sort()

    data_types = {}
    routed_types = []
    for index_type in index_types:
        search_response = esprit.raw.search(conn, index_type)
        if search_response.status_code != 200:
            logging.error("No query data for index types")
            continue
        count = search_response.json().get('hits', {}).get('total', 0)
        if count > 0:
            data_types[index_type] = count
            logging.info("Found {n} records in {t}".format(n=count, t=index_type))
            if index_type.startswith('routed'):
                routed_types.append(index_type)
    return data_types, routed_types


def sort_accounts_and_notifications(conn, logging, routed_types):
    standard_accounts = {}
    accounts_to_delete = {}
    accounts_to_rename = {}
    accounts_to_check = {}
    bibids_to_check = ['aTIHO', 'aUBPO', 'aGFZPO', 'aGSF', 'aFHRT', 'aFHBOG', 'aUBKL', 'aUBMZ']

    # find standard accounts
    q = {
        "query": {
            "prefix": {"repository.bibid": "a"}
        },
        "size": 1000,
        "fields": [
            "repository.bibid"
        ]
    }
    search_response = esprit.raw.search(conn, 'account', query=q)
    if search_response.status_code != 200:
        logging.error("No query data for match all accounts")
        return
    search_data = search_response.json()
    number_of_matches = search_data.get('hits', {}).get('total', 0)

    # find matching regular account
    for doc in search_data.get('hits', {}).get('hits', []):
        bibids = doc.get('fields', {}).get("repository.bibid", [])
        if len(bibids) != 1:
            logging.error("No unique bibid for account {s}".format(s=doc['_id']))
            continue
        bibid = bibids[0]
        standard_accounts[doc['_id']] = {'bibid': bibid}
        q = {
            "query": {
                "match": {"repository.bibid.exact": bibid[1:]}
            },
            "fields": [
                "repository.bibid"
            ]
        }
        matching_repo_response = esprit.raw.search(conn, 'account', query=q)
        if matching_repo_response.status_code != 200:
            continue
        matching_repo_data = matching_repo_response.json()
        if matching_repo_data.get('hits', {}).get('total', 0) == 0:
            accounts_to_rename[doc['_id']] = {'bibid': bibid}
        elif matching_repo_data.get('hits', {}).get('total', 0) == 1:
            if bibid in bibids_to_check:
                accounts_to_check[doc['_id']] = {
                    'bibid': bibid,
                    'matching_repo_id': matching_repo_data.get('hits', {}).get('hits', [])[0].get('_id')
                }
            else:
                accounts_to_delete[doc['_id']] = {'bibid': bibid}
    logging.info("Number of accounts to be deleted: {dn}".format(dn=len(accounts_to_delete.keys())))
    logging.info("Number of accounts to be renamed: {dn}".format(dn=len(accounts_to_rename.keys())))
    logging.info("Number of accounts to be checked: {dn}".format(dn=len(accounts_to_check.keys())))
    total = len(accounts_to_rename.keys()) + len(accounts_to_check.keys()) + len(accounts_to_delete.keys())
    if total != number_of_matches:
        logging.warning("Not all accounts have been tallied")
    notifications_to_modify = check_account_notifications(conn, logging, accounts_to_check, routed_types)
    logging.info("Number of unique notifications to be modified: {dn}".format(dn=len(notifications_to_modify.keys())))
    return standard_accounts, accounts_to_delete, accounts_to_rename, notifications_to_modify


def check_account_notifications(conn, logging, accounts_to_check, routed_types):
    # to check routing data
    """
    accounts_to_check = {
        'id1' : {
            'bibid': 'repository bibid',
            'matching_repo_id': 'matching_repo_id'
        },
        ...
    }
    1. get all notifications routed for this standard account
    2. get all notifications routed for the matching account
    3. get list of all missing notifications
    """
    # Get all notifications routed for the standard and matching account
    notifications_to_modify = {}
    missing_notification_count = 0
    for acc_id, data in accounts_to_check.items():
        std_notifications, std_count = get_account_notifications(conn, logging, acc_id, routed_types,
                                                                 include_source=False, size=1000)
        std_notification_ids = set([doc['_id'] for doc in std_notifications])
        matching_notifications, matching_count = get_account_notifications(conn, logging, data['matching_repo_id'],
                                                                           routed_types, include_source=False,
                                                                           size=1000)
        matching_notification_ids = set([doc['_id'] for doc in matching_notifications])
        missing_notification_ids = std_notification_ids - matching_notification_ids
        count = len(list(missing_notification_ids))
        missing_notification_count += count
        logging.info("Number of missing notifications for repository {r}: {dn}".format(r=data['bibid'][1:], dn=count))
        for n_id in list(missing_notification_ids):
            repos = notifications_to_modify.get(n_id, [])
            repos.append(data['matching_repo_id'])
            notifications_to_modify[n_id] = list(set(repos))
        # accounts_to_check[acc_id]['missing_notification_ids'] = list(missing_notification_ids)
    logging.info("Total number of missing notifications: {dn}".format(dn=missing_notification_count))
    return notifications_to_modify


def get_account_notifications(conn, logging, repository_id, routed_types, include_source=True, size=100):
    # return list of all matching notifications for repository id and the count
    q = {
        "query": {
            "match": {"repositories": repository_id}
        },
        "_source": include_source,
        "size": size
    }
    search_response = esprit.raw.search(conn, routed_types, query=q)
    if search_response.status_code != 200:
        logging.info("No routing data for {id}".format(id=repository_id))
        return [], 0
    search_data = search_response.json()
    return search_data.get('hits', {}).get('hits', []), search_data.get('hits', {}).get('total', 0)


def rename_account(data):
    # change bibid
    data['repository'] = data.get('repository', {})
    bibid = data['repository'].get('bibid', '')
    data['repository']['bibid'] = bibid[1:]
    # change email
    data['email'] = data.get('email', "{bid}@deepgreen.org".format(bid=bibid))[1:]
    # data is modified by pointer, so don't have to return
    return


def add_repo_to_notification(data, new_repo_ids):
    """
    Copy missing notifications from standard to regular
    a. Add matching_repo_id to list of repository ids in `repositories`
    b. Change count in `reason` - "Matched to # qualified repositories."
    """
    repositories = data.get('repositories', [])
    repositories = list(set(repositories + new_repo_ids))
    data['repositories'] = repositories
    data['reason'] = 'Matched to {num} qualified repositories.'.format(num=len(repositories))
    # data is modified by pointer, so don't have to return
    return


def filter_and_modify_account(logging, data, **func_args):
    # a. if account in accounts_to_delete
    #     ignore
    # b. elif account in rename accounts
    #     for account in accounts_to_rename:
    #         i. account_data = get account from es
    #         ii. rename_account(account_data)
    #         iii. create a new record of type account with the _source data and save
    # c. elif account in standard_accounts:
    #     ignore
    ignore = False
    standard_accounts = func_args.get('standard_accounts', {})
    accounts_to_delete = func_args.get('accounts_to_delete', {})
    accounts_to_rename = func_args.get('accounts_to_rename', {})
    if data['id'] in accounts_to_delete.keys():
        ignore = True
        logging.info('Skipping account {aid}'.format(aid=data['id']))
    elif data['id'] in accounts_to_rename.keys():
        ignore = False
        rename_account(data)
        logging.info('Renaming account {aid}'.format(aid=data['id']))
    elif data['id'] in standard_accounts.keys():
        ignore = True
        logging.info('Skipping account {aid}'.format(aid=data['id']))
    return ignore


def filter_and_modify_notification(logging, data, **func_args):
    """
    a. For each record in notification:
        if n_id not in notifications_to_modify:
            a. create a new record of that type (including date) with the data in _source and save
    b. for notification_id in notifications_to_modify:
        i. get notification from es
        ii. add_repo_to_notification
        iii. create a new record of type routed notification (with the date in index) and
            with the _source data and save
            typ = data['_type']
            note = RoutedNotification(data['_source'])
            note.save(type=typ)
    """
    ignore = False
    notifications_to_modify = func_args.get('notifications_to_modify', {})
    if data['id'] in notifications_to_modify.keys():
        add_repo_to_notification(data, notifications_to_modify[data['id']])
        logging.info('Modifying notification {nid}'.format(nid=data['id']))
    return ignore


def model_for_type(index_type):
    models_by_type = {
        # sword_deposit_record
        # sword_repository_status
        'account': models.Account,
        'alliance': models.Alliance,
        'contentlog': models.ContentLog,
        'failed': models.FailedNotification,
        'license': models.License,
        'match_prov': models.MatchProvenance,
        'repo_config': models.RepositoryConfig,
        'routed': models.RoutedNotification,
        'unrouted': models.UnroutedNotification
    }
    if index_type.startswith('routed'):
        return models_by_type['routed']
    return models_by_type.get(index_type, None)


def migrate_record(conn, logging, index_type, modify_data_func=None, **func_args):
    logging.info("Starting migration of {t}".format(t=index_type))
    model_class = model_for_type(index_type)
    q = {"query": {"match_all": {}}}
    data_scroll = esprit.tasks.scroll(conn, index_type, q, page_size=1000, limit=None, keepalive="10m")
    for data in data_scroll:
        ignore = False
        if modify_data_func:
            ignore = modify_data_func(logging, data, **func_args)
        if not ignore:
            mc = model_class(data)
            if index_type.startswith('routed'):
                mc.save(type=index_type)
            else:
                mc.save()
    logging.info("Finished migration of {t}".format(t=index_type))


def migrate_data(conn, logging, migrate_all=True, migrate_account=True, migrate_notification=True):
    # 1. Get types_with_data(conn)
    data_types, routed_types = types_with_data(conn, logging)
    # 2. Get list of all accounts and notifications that need sorting
    standard_accounts, accounts_to_delete, accounts_to_rename, notifications_to_modify = \
        sort_accounts_and_notifications(conn, logging, routed_types)
    # 3. For each type except account, notification, sword_deposit_record and sword_repository_status
    #    For each record in that type:
    #        create a new record of that type with the _source data and save
    if migrate_all:
        types_to_ignore = ['account', 'sword_deposit_record', 'sword_repository_status'] + routed_types
        for index_type in data_types:
            if index_type in types_to_ignore:
                continue
            migrate_record(conn, logging, index_type, modify_data_func=None)
    # 4. For type account
    #     For each record in account:
    #         create a new record based on filter_and_modify_account
    if migrate_account:
        migrate_record(conn, logging, 'account', modify_data_func=filter_and_modify_account,
                       standard_accounts=standard_accounts, accounts_to_delete=accounts_to_delete,
                       accounts_to_rename=accounts_to_rename)
    # 5. For type notification
    #     For each record in notification:
    #         create a new record based on filter_and_modify_notification
    if migrate_notification:
        for index_type in routed_types:
            if index_type in ['routed201907', 'routed201908']:
                continue
            migrate_record(conn, logging, index_type, modify_data_func=filter_and_modify_notification,
                       notifications_to_modify=notifications_to_modify)
    return


if __name__ == "__main__":
    # logging
    logging.basicConfig(filename='migration.log', level=logging.INFO, format='%(asctime)s %(message)s')
    conn = old_es_connection()
    migrate_data(conn, logging, migrate_all=False, migrate_account=False, migrate_notification=False)
