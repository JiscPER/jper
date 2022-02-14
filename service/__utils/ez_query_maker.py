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


def match_all() -> dict:
    return {
        'query': {
            'bool': {
                'must': [
                    {'match_all': {}}
                ]
            }
        }
    }
