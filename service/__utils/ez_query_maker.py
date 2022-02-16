def by_id(id_str: str) -> dict:
    return {
        'query': {
            'bool': {
                'must': [
                    {'query_string': {'query': id_str}}
                ]
            }
        }
    }


def by_term(term, value) -> dict:
    return {"query": {"term": {
        term: value
    }}}


def match_all(size=1000) -> dict:
    return {
        'query': {
            'bool': {
                'must': [
                    {'match_all': {}}
                ]
            }
        },
        'size': size
    }


def query_key_by_query_str(key: str, val: str) -> dict:
    return {
        "query": {
            "query_string": {
                "query": val,
                "default_field": key,
                "default_operator": "AND"
            }
        }
    }
