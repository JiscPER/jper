def query_by_id(id_str: str) -> dict:
    return {
        'query': {
            'bool': {
                'must': [
                    {'query_string': {'query': id_str}}
                ]
            }
        }
    }
