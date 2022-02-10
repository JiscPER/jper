from typing import Type

from esprit.dao import DomainObject


def object_query_first(domain_obj_cls: Type[DomainObject], *args, **kwargs):
    results = domain_obj_cls.object_query(*args, **kwargs)
    results = results and results[0]
    return results
