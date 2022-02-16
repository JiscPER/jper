import logging
import time
from typing import Callable, Iterable, Optional
from typing import Type

from esprit import raw
from esprit.dao import DomainObject

from octopus.core import app
from service.__utils import ez_query_maker

log: logging.Logger = app.logger


def object_query_first(domain_obj_cls: Type[DomainObject], *args, **kwargs):
    results = domain_obj_cls.object_query(*args, **kwargs)
    results = results[0] if results else None
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


def wait_unit_id_not_found(domain_obj_cls: Type[DomainObject], _id: str):
    wait_unit(lambda: domain_obj_cls.count(ez_query_maker.by_id(_id)) == 0)


def pull_all_by_key(domain_obj_cls: Type[DomainObject], key, value, wrap=True) -> Iterable:
    return query_objs(domain_obj_cls=domain_obj_cls, query={"query": {"term": {key: value}}}, wrap=wrap)


def query_objs(domain_obj_cls: Type[DomainObject], query: dict, wrap=True,
               raise_wrap_fail=False):
    res = domain_obj_cls.query(q=query)
    return wrap_all(domain_obj_cls, res, wrap=wrap, raise_wrap_fail=raise_wrap_fail)


def pull_by_id(domain_obj_cls: Type[DomainObject], id_val: str) -> Optional:
    lrf_list = query_objs(domain_obj_cls, ez_query_maker.by_id(id_val))
    lrf_list = list(lrf_list)
    return lrf_list[0] if lrf_list else None


def wrap_all(domain_obj_cls: Type[DomainObject], result: dict, wrap=True, raise_wrap_fail=False):
    def _safe_wrap(_r):
        try:
            return domain_obj_cls(_r)
        except Exception as e:
            if raise_wrap_fail:
                raise e
            return None

    res = raw.unpack_json_result(result)
    results = (_safe_wrap(r) if wrap else r for r in res)
    results = filter(None, results)
    return results
