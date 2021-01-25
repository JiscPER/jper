from standalone_octopus.lib import paths

SWORDV2_SERVER_CONFIG = {

    ############################################
    # Dynamically load the implementation classes for the 3 main interfaces
    # In this default configuration we use the built-in SSS repository's
    # implementations for everything
    "sword_server" : "sss.repository.SSS",
    "authenticator" : "sss.repository.SSSAuthenticator",
    "webui" : "sss.repository.WebInterface",

    ##############################################
    # General server config

    # The base url of the webservice where SSS is deployed
    "base_url" : "http://localhost:5000/",
    # if you are using Apache, you should probably use this base_url instead
    # "base_url" : "http://localhost/sss/",

    # explicitly set the sword version, so if you're testing validation of
    # service documents you can "break" it.
    "sword_version" : "2.0",

    # maximum upload size to be allowed, in bytes (this default is 16Mb)
    "max_upload_size" : 16777216,
    # used to generate errors
    # "max_upload_size" : 0,
    # Just omit the max_upload_size parameter if you don't want any limit

    # we can turn off updates and deletes in order to examine the behaviour of Method Not Allowed errors
    "allow_update" : True,
    "allow_delete" : True,

    # we can turn off deposit receipts, which is allowed by the specification
    "return_deposit_receipt" : True,

    "generator" : ("http://www.swordapp.org/sss", "2.0"),

    ##############################################
    # Default configuration for SSS repository impl

    # The number of collections that SSS will create and give to users to deposit content into
    "num_collections" : 10,

    # The directory where the deposited content should be stored
    "store_dir" : paths.rel2abs(__file__, "..", "..", "..", "..", "service", "tests", "sss_store"),
    # If you are using Apache you should set the store directory in full

    # The directory where incoming content will be temporarily stored
    "tmp_dir" : paths.rel2abs(__file__, "..", "..", "..", "..", "service", "tests", "sss_tmp"),

    # The chunk size used to copy file streams into and out of the temp directory
    "copy_chunk_size" : 8096,

    # What media ranges should the app:accept element in the Service Document support
    "app_accept" : [ "*/*" ],
    "multipart_accept" : [ "*/*" ],
    "accept_nothing" : False,

    # use these app_accept and multipart_accept values to create an invalid Service Document
    # "app_accept" : None,
    # "multipart_accept" : None,

    # should we provide sub-service urls
    "use_sub" : True,

    # What packaging formats should the sword:acceptPackaging element in the Service Document support
    "sword_accept_package" : [
            "http://purl.org/net/sword/package/SimpleZip",
            "http://purl.org/net/sword/package/Binary",
            "http://purl.org/net/sword/package/METSDSpaceSIP"
    ],

    # list of package formats that SSS can provide when retrieving the Media Resource
    "sword_disseminate_package" : [
        "http://purl.org/net/sword/package/SimpleZip"
    ],


    # Supported package format disseminators; for the content type (dictionary key), the associated
    # class will be used to package the content for dissemination
    "package_disseminators" : {
            "(& (type=\"application/zip\") (packaging=\"http://purl.org/net/sword/package/SimpleZip\") )" : "sss.ingesters_disseminators.DefaultDisseminator",
            "(& (type=\"application/zip\") )" : "sss.ingesters_disseminators.DefaultDisseminator",
            "(& (type=\"application/atom+xml;type=feed\") )" : "sss.ingesters_disseminators.FeedDisseminator"
    },

    # Supported package format ingesters; for the Packaging header (dictionary key), the associated class will
    # be used to unpackage deposited content
    "package_ingesters" : {
            "http://purl.org/net/sword/package/Binary" : "sss.ingesters_disseminators.BinaryIngester",
            "http://purl.org/net/sword/package/SimpleZip" : "sss.ingesters_disseminators.SimpleZipIngester",
            "http://purl.org/net/sword/package/METSDSpaceSIP" : "sss.ingesters_disseminators.METSDSpaceIngester"
    },

    # Ingester to use for atom entries
    "entry_ingester" : "sss.ingesters_disseminators.DefaultEntryIngester",

    # supply this header in the Packaging header to generate a http://purl.org/net/sword/error/ErrorContent
    # sword error
    "error_content_package" : "http://purl.org/net/sword/package/error",

    # The acceptable formats that the server can return the media resource in
    # on request.
    # This is used in Content Negotiation during GET on the EM-URI
    "media_resource_formats" : [
        {"content_type" : "application/zip", "packaging": "http://purl.org/net/sword/package/SimpleZip"},
        {"content_type" : "application/zip"},
        {"content_type" : "application/atom+xml;type=feed"},
        {"content_type" : "text/html"}
    ],

    # If no Accept parameters are given to the server on GET to the EM-URI the
    # following defaults will be used to determine the response type
    "media_resource_default" : {
        "content_type" : "application/zip"
    },

    # The acceptable formats that the server can return the entry document in
    # on request
    # This is used in Content Negotiation during GET on the Edit-URI
    "container_formats" : [
        {"content_type" : "application/atom+xml;type=entry" },
        {"content_type" : "application/atom+xml;type=feed" },
        {"content_type" : "application/rdf+xml" }
    ],

    # If no Accept parameters are given to the server on GET to the Edit-URI the
    # following defaults will be used to determine the response type
    "container_format_default" : {
        "content_type" : "application/atom+xml;type=entry"
    },

    ###############################################
    # Default configuration for SSS authentication

    # user details; the user/password pair should be used for HTTP Basic Authentication, and the obo is the user
    # to use for On-Behalf-Of requests.  Set authenticate=False if you want to test the server without caring
    # about authentication, set mediation=False if you want to test the server's errors on invalid attempts at
    # mediation
    "authenticate" : True,
    # If you are using apache, you can turn off this authentication and leave it
    # to the standard apache auth module
    # "authenticate" : false,
    "user" : "sword",
    "password" : "sword",

    "mediation" : True,
    "obo" : "obo",

}

