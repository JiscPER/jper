import logging
import time
from typing import Callable, Iterable
from typing import Type

from esprit.dao import DomainObject

from octopus.core import app
from service.__utils import ez_query_maker

log: logging.Logger = app.logger


def object_query_first(domain_obj_cls: Type[DomainObject], *args, **kwargs):
    results = domain_obj_cls.object_query(*args, **kwargs)
    results = results and results[0]
    return results


def wait_unit(cond_fn: Callable[[], bool], timeout=10, sleep_sec=0.1):
    start_time = time.time()
    while True:
        if cond_fn():
            return True

        if (time.time() - start_time) > timeout:
            log.warning(f'wait unit failed, timeout[{timeout}]')
            return False

        time.sleep(sleep_sec)


def wait_unit_id_found(domain_obj_cls: Type[DomainObject], _id: str):
    wait_unit(lambda: domain_obj_cls.count(ez_query_maker.by_id(_id)) > 0)


def pull_all_by_key(domain_obj_cls: Type[DomainObject], key, value, use_exact=True) -> Iterable:
    exact_str = '.exact' if use_exact else ''
    res = domain_obj_cls.query(q={"query": {"term": {key + exact_str: value}}})
    return (domain_obj_cls.pull(obj['_source']['id']) for obj in res['hits']['hits'])
