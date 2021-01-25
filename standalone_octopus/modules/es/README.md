# Elastisearch Integration Library

## DAO

A DAO is a Data Access Object and provides a mechanism to load data from a data source.  This module provides a DAO called *ESDAO* which
loads data from Elasticsearch.  It, in turn, extends from the *esprit* Domain Object (esprit.dao.DomainObject).

The key things that it provides are automatic configuration of the ES connection, and a default document mapping which
can be used by the ES initialisation scripts.  Therefore, to implement a DAO which can be used by your model objects, all
that is required is your own type-specific implementation:

```python
class MyDAO(standalone_octopus.modules.es.dao.ESDAO):
    __type__ = "mytype"
```

In order for this to work correctly you must have correctly set the configuration parameters:

* ELASTIC_SEARCH_HOST
* ELASTIC_SEARCH_INDEX

The DAO also provides a built-in standard ES mapping which you can override by overriding the **mapping** function (see below), and
also provides a placeholder **prep** function which subclasses can implement in order to have work done before a record
is **save**d.


### Initialisation

This module provides a function to initialise the index at application startup.  It needs to be in the rootcfg.py as follows:

```python
INITIALISE_MODULES = [
    "octopus.modules.es.initialise"
]
```

In order to have the types in the index created correctly the following configuration is required:

```python
INITIALISE_INDEX = True     # this is the default behaviour

ELASTIC_SEARCH_MAPPINGS = [
    service.dao.MyDAO       # a DAO as defined above
]
```

When the initialise function in the module is run (which magnificent octopus will do for you), it will load each class specified
and call its "mappings" function, and then put the mappings it receives into the index.

To change the mapping for a given type, just override the mappings function

```python
class MyDAO(octopus.modules.es.dao.ESDAO):
    __type__ = "mytype"
    
    @classmethod
    def mappings():
        return {
            cls.__type__ : {
                cls.__type__ : {
                    # mapping definition here
                }
            }
        }
```

Note that a single class may return mappings for multiple types - the above example assumes a one-to-one mapping between 
the class and the type of mapping it creates.

## Query Endpoint

This provides read-only access to configured query endpoints.

Can be mounted into your app as a blueprint with:

```python
    from standalone_octopus.modules.es.query import blueprint as query
    app.register_blueprint(query, url_prefix="/query")
```

To configure the endpoint, you need to provide the following configuration options

```python
    QUERY_ROUTE = {
        "query" : {                                 # the URL route at which it is mounted
            "index" : {                             # the URL name for the index type being queried
                "auth" : False,                     # whether the route requires authentication
                "role" : None,                      # if authenticated, what role is required to access the query endpoint
                "filters" : ["default"],            # names of the standard filters to apply to the query
                "dao" : "octopus.dao.MyDAO"         # classpath for DAO which accesses the underlying ES index
            }
        }
    }
    
    def default_filter(query):
        pass
    
    QUERY_FILTERS = {
        "default" : default_filter
    }
```

The **QUERY_ROUTE** maps to the url_prefix that you mounted the query endpoint at in your app, so any requests that
 come into that endpoint will activate the specified configuration.  At each endpoint you can access multiple "index types",
 which loosely correspond to types in the ES index (see below for how they are not exactly that), and for each index type
 there is a set of configuration options.
 
You can access an index type, therefore, with URLs like:

    http://localhost:5000/query/index/_search?q=mysearch
    http://localhost:5000/query/index/_search?source={<es query object>}

The index type here differs from a standard ES type, because in reality all requests go thorugh the specified **dao**, 
and while DAOs often map one-to-one with ES types, they are not required to do so.  You could therefore provide a DAO
which ran its queries across multiple types simultaneously.

Filters allow you to insert additional constraints on the query as it comes through, and these can be specified as a list
(in the order you want them applied) in the **filters** section.  The name of the filter supplied must appear in the
**QUERY_FILTERS** configuration, which in turn must map to a function which takes an incoming query and augments it (by
reference) with any additional constraints.

Note, you can also pull objects by identifier:

    http://localhost:5000/query/index/123456789

## Autocomplete Endpoint(s)

Can be mounted into your app as a blueprint with:

```python
    from octopus.modules.es.autocomplete import blueprint as autocomplete
    app.register_blueprint(autocomplete, url_prefix="/autocomplete")
```

This enables all the autocomplete endpoints, which ones you use/configure is up to you.  See below for details on the available options.

### Compound

The compound autocomplete takes a query, and returns you a multi-field object, containing the fields you are interested in.

This can be useful for building more complex result-selection options in the front end (e.g. showing both a suggested Journal's title and ISSN)

Note that this is the slowest and most resource intensive way of doing autocomplete, and also because it relies on result sets rather than facets may produce duplication in the returned list.

The configuration is as follows:

```python
AUTOCOMPLETE_COMPOUND = {
    "name" : {                                  # name of the autocomplete, as represented in the URL (have as many of these sections as you need)
        "fields" : ["name", "description"],     # fields to return in the compound result
        "field_name_map" : {                    # map field name to name it will be referred to in the result
            "name" : "my_name",
            "description" : "my_description"
        },
        "filters" : {                           # filters to apply to the result set
            "name.exact" : {                    # field on which to filter
                "start_wildcard" : True,        # apply start wildcard?
                "end_wildcard": True,           # apply end wildcard?
                "boost" : 2.0                   # boost to apply to matches on this field
            },
            "description.exact" : {
                "start_wildcard" : True,
                "end_wildcard": True,
                "boost" : 1.0
            }
        },
        "input_filter" : lambda x : x ,         # function to apply to an incoming string before being applied to the es query
        "default_size" : 10,                    # if no size param is specified, this is how big to make the response
        "max_size" : 25,                        # if a size param is specified, this is the limit above which it won't go
        "dao" : "octopus.dao.MyDAO"             # classpath for DAO which accesses the underlying ES index
    }
}
```

You can make requests as follows:

    http://localhost:5000/autocomplete/compound/journal?q=1234
    http://localhost:5000/autocomplete/compound/journal?q=Revista&size=20

The result will be a list (ordered by relevance) containing the desired fields, e.g:

```python
    [
        {
            issn: ["0123-3475",1909-8758"],
            title: ["Revista Colombiana de Biotecnología"]
        },
        {
            issn: ["1515-6877","1851-8893"],
            title: ["Orientación y Sociedad : Revista Internacional e Interdisciplinaria de Orientación Vocacional Ocupacional "]
        }
    ]
```

#### JavasSript

The compound query endpoint can be called via the module's javascript library.  Ensure that the route to the autocomplete endpoint 
is in the javascript configuration; for example, in octopus/modules/es/settings.py

```python
    CLIENTJS_ES_COMPOUND_ENDPOINT = "/autocomplete/compound"
```


Set up an input field as an compound autocomplete field with:

```javascript
    octopus.esac.bindCompoundAutocomplete({
        selector : "#my_field",
        minimumInputLength : 3,
        placeholder :"Enter some text",
        type : "configured_endpoint",
        format : function(result) { return {id : result.term, text: result.term} },
        allow_clear : true
    })
```

Note that the "configured_endpoint" is one of the autocomplete endpoints specified in **settings.py**.

When you are building your **format** function, remember that the values in the results will be keyed as per the AUTOCOMPLETE_COMPOUND server configuration.
So if you are querying for the field "title", it will be available in "result.title".

If you want to call the autocomplete without binding to an input form, as above, you can go directly to the query method:

```javascript
    octopus.esac.compoundAutocomplete({
        q : "query string";
        size : 10;
        type : "configured_endpoint";
        success : function(data) {};
        complete : function(data) {};
        error : function(data) {};
    })
```

### Term

The term autocomplete takes a query and returns you a list of unique values which derive from that query, based on their popularity within your dataset on records which match the criteria.

Depending on whether you enable wildcard search (you probably should for best results), this can be quite computationally intensive, but unlike the Compound autocomplete it does not yield duplicate values in the result set.

The configuration is as follows:

```python
AUTOCOMPLETE_TERM = {
    "name" : {                                  # name of the autocomplete, as represented in the URL (have as many of these sections as you need)
        "filter" : {                            # The filter to apply to the result set
            "name.exact" : {                    # field on which to apply the filter
                "start_wildcard" : True,        # apply start wildcard
                "end_wildcard" : True          # apply end wildcard
            }
        },
        "facet" : "name.exact",                 # facet from which to get our results
        "input_filter" : lambda x : x,          # function to apply to an incoming string before being applied to the es query
        "default_size" : 10,                    # if no size param is specified, this is how big to make the response
        "max_size" : 25,                        # if a size param is specified, this is the limit above which it won't go
        "dao" : "octopus.dao.MyDAO"             # classpath for DAO which accesses the underlying ES index
    }
}
```

You can make requests as follows:

    http://localhost:5000/autocomplete/term/journal?q=1234
    http://localhost:5000/autocomplete/term/journal?q=Revista&size=20

The result will be a list (ordered by number of occurrances in the result set).


#### JavaScript

The term query endpoint can be called via the module's javascript library. Ensure that the route to the autocomplete endpoint 
is in the javascript configuration; for example, in octopus/modules/es/settings.py

```python
    CLIENTJS_ES_TERM_ENDPOINT = "/autocomplete/term"
```

Set up an input field as a term autocomplete field with:

```javascript
    octopus.esac.bindTermAutocomplete({
        selector : "#my_field",
        minimumInputLength : 3,
        placeholder :"Enter some text",
        type : "configured_endpoint",
        format : function(result) { return {id : result.term, text: result.term} },
        allow_clear : true,
        allow_any: false,
        multiple: false
    })
```

Note that the "configured_endpoint" is one of the autocomplete endpoints specified in **settings.py**.

**allow_any** allows the user to input any text they want in the field, even if it is not in the returned result.

**multiple** allows the user to add multiple values to the input box, each time using the autocomplete.

If you want to call the autocomplete without binding to an input form, as above, you can go directly to the query method:

```javascript
    octopus.esac.termAutocomplete({
        q : "query string";
        size : 10;
        type : "configured_endpoint";
        success : function(data) {};
        complete : function(data) {};
        error : function(data) {};
    })
```

