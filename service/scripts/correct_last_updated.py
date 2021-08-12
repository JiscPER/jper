import esprit
import logging
from service import models
import json
import os
# import csv


"""
This script gets the last_updated date from elasticsearch 2.4 with one index containing many types and
modifies the records in elastic search7, with the correct last_updated date.
"""


def old_es_connection():
    host = 'localhost'
    port = '9200'
    index = 'jper'
    verify_ssl = False
    index_per_type = False
    return esprit.raw.Connection(host, index, port=port, verify_ssl=verify_ssl, index_per_type=index_per_type)


def new_es_connection():
    host = 'localhost'
    port = '9205'
    index = 'jper'
    verify_ssl = False
    index_per_type = True
    return esprit.raw.Connection(host, index, port=port, verify_ssl=verify_ssl, index_per_type=index_per_type)


def types_with_data(old_conn, logging):
    # return each index type with data and count of records to be transferred

    index_types = esprit.raw.list_types(old_conn)
    index_types.remove('_default_')
    index_types.sort()

    data_types = {}
    routed_types = []
    for index_type in index_types:
        search_response = esprit.raw.search(old_conn, index_type)
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


def update_last_updated(new_conn, logging, index_type, doc_id, date):
    # Did not use this and used bulk api instead
    url = esprit.raw.elasticsearch_url(new_conn, type="{index_type}/_update/{doc_id}".format(index_type=index_type, doc_id=doc_id))
    body = {
        "script" : {
            "source": "ctx._source.last_updated = params.last_updated",
                "lang": "painless",
                "params" : {
                    "last_updated": date
                }
        }
    }
    headers = {"content-type" : "application/json"}
    resp = esprit.raw._do_post(url, new_conn, json.dumps(body), headers=headers)
    if resp.status_code == 200:
        logging.debug("Updated record {a} with last_updated {b}".format(a=doc_id, b=date))
    else:
        logging.error("Error updating record {a} with last_updated {b}".format(a=doc_id, b=date))


def write_each_index_last_updated(old_conn, logging, index_type):
    logging.info("Starting {t}".format(t=index_type))
    q = {"query": {"match_all": {}}}
    data_scroll = esprit.tasks.scroll(old_conn, index_type, q, page_size=1000, limit=None, keepalive="10m")
    bulk_update_file = open("update_data/bulk_update_for_{a}.txt".format(a=index_type), 'w', newline='')
    # csv_file = open("update_data/last_updated_for_{a}.csv".format(a=index_type), 'w', newline='')
    # writer = csv.writer(csv_file, delimiter=',')
    # writer.writerow(['id', 'last_updated'])
    for data in data_scroll:
        # writer.writerow([data['id'], data['last_updated']])
        a = {'update': {'_id': data['id'], '_index': 'jper-'+index_type}}
        b = { 'doc': {'last_updated': data['last_updated']}}
        bulk_update_file.write("{a}\n".format(a=json.dumps(a)))
        bulk_update_file.write("{b}\n".format(b=json.dumps(b)))
    # csv_file.close()
    bulk_update_file.close()
    logging.info("Finished {t}".format(t=index_type))


def record_last_updated(old_conn, logging):
    _data_types, routed_types = types_with_data(old_conn, logging)
    if not os.path.isdir('update_data'):
        os.mkdir('update_data')
    for index_type in ['account', 'contentlog', 'failed', 'match_prov', 'repo_config', 'sword_deposit_record',
                       'sword_repository_status', 'unrouted']:
        write_each_index_last_updated(old_conn, logging, index_type)
    for index_type in routed_types:
        write_each_index_last_updated(old_conn, logging, index_type)


if __name__ == "__main__":
    # logging
    logging.basicConfig(filename='update_data/record_last_updated.log', level=logging.INFO, format='%(asctime)s %(message)s')
    old_conn = old_es_connection()
    record_last_updated(old_conn, logging)

