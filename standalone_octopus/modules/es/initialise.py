import esprit
from standalone_octopus.lib import plugin
from standalone_octopus.core import app

def _default_mapping():
    default_mapping = app.config.get("ELASTIC_SEARCH_DEFAULT_MAPPING")
    if default_mapping is None:
        return None

    if "mappings" in default_mapping:
        return default_mapping

    if "_default_" in default_mapping:
        return {"mappings" : default_mapping}

    return {"mappings" : {"_default_" : default_mapping}}

def put_mappings(mappings):
    # make a connection to the index
    conn = esprit.raw.Connection(app.config['ELASTIC_SEARCH_HOST'], app.config['ELASTIC_SEARCH_INDEX'])

    # get the ES version that we're working with
    es_version = app.config.get("ELASTIC_SEARCH_VERSION", "0.90.13")

    # for each mapping (a class may supply multiple), create them in the index
    for key, mapping in mappings.items():
        if not esprit.raw.type_exists(conn, key, es_version=es_version):
            r = esprit.raw.put_mapping(conn, key, mapping, es_version=es_version)
            print("Creating ES Type+Mapping for", key, "; status:", r.status_code)
        else:
            print("ES Type+Mapping already exists for", key)

def put_example(type, example):
    # make a connection to the index
    conn = esprit.raw.Connection(app.config['ELASTIC_SEARCH_HOST'], app.config['ELASTIC_SEARCH_INDEX'])

    # get the ES version that we're working with
    es_version = app.config.get("ELASTIC_SEARCH_VERSION", "0.90.13")

    if not esprit.raw.type_exists(conn, type, es_version=es_version):
        example.save()
        example.delete()
        print("Initialising ES Type+Mapping from document for", type)
    else:
        print("Not Initialising from document - ES Type+Mapping already exists for", type)

def initialise():
    # if we are not to initialise the index, stop here
    if not app.config.get("INITIALISE_INDEX", False):
        return

    # create the index itself if it needs creating
    conn = esprit.raw.Connection(app.config['ELASTIC_SEARCH_HOST'], app.config['ELASTIC_SEARCH_INDEX'])
    if not esprit.raw.index_exists(conn):
        print("Creating ES Index; host:" + str(conn.host) + " port:" + str(conn.port) + " db:" + str(conn.index))
        default_mapping = _default_mapping()
        if default_mapping is not None:
            print("Applying default mapping to index")
        esprit.raw.create_index(conn, mapping=default_mapping)
    else:
        print("ES Index Already Exists; host:" + str(conn.host) + " port:" + str(conn.port) + " db:" + str(conn.index))

    # get the list of classes which carry the type-specific mappings to be loaded
    mapping_daos = app.config.get("ELASTIC_SEARCH_MAPPINGS", [])

    # get the ES version that we're working with
    es_version = app.config.get("ELASTIC_SEARCH_VERSION", "0.90.13")

    # load each class and execute the "mappings" function to get the mappings
    # that need to be imported
    for cname in mapping_daos:
        klazz = plugin.load_class_raw(cname)
        mappings = klazz.mappings()
        put_mappings(mappings)
        """
        # for each mapping (a class may supply multiple), create them in the index
        for key, mapping in mappings.iteritems():
            if not esprit.raw.type_exists(conn, key, es_version=es_version):
                r = esprit.raw.put_mapping(conn, key, mapping, es_version=es_version)
                print "Creating ES Type+Mapping for", key, "; status:", r.status_code
            else:
                print "ES Type+Mapping already exists for", key
        """

    # get the list of classes which will give us example docs to load
    example_daos = app.config.get("ELASTIC_SEARCH_EXAMPLE_DOCS", [])

    for cname in example_daos:
        klazz = plugin.load_class_raw(cname)
        example = klazz.example()
        type = klazz.get_write_type()
        put_example(type, example)

        """
        if not esprit.raw.type_exists(conn, type, es_version=es_version):
            example.save()
            example.delete()
            print "Initialising ES Type+Mapping from document for", type
        else:
            print "Not Initialising from document - ES Type+Mapping already exists for", type
        """

    self_inits = app.config.get("ELASTIC_SEARCH_SELF_INIT", [])

    for cname in self_inits:
        klazz = plugin.load_class_raw(cname)
        klazz.self_init()