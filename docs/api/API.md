# DeepGreen API

This document specifies the interface and data formats to be used by the DeepGreen REST API.

The current version of the API is v1, and it can be accessed at

    https://www.oa-deepgreen.de/api/v1

All URL paths provided in this document will extend from this base url.

In many cases you will need an API key to access the API, and this can be obtained from your Router account page.

## For Publishers

If you are a publisher (also referred to here as a "provider"), providing content to the router, you have access to 2 endpoints:

1. The validation endpoint
2. The notification endpoint

The first allows you, during initial set-up of your API client, to check that the content you are sending is going to
work with the Router, and the second is the way to send us a real notification to be routed.

You can create content in 2 ways in the router:

1. As a metadata-only notification
2. As a metadata + binary package notification

The first allows you to provide publication information which complies with our native JSON format as an [Incoming Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/IncomingNotification.md).

The second allows you to give us a multi-part request containing the publication information which complies with our native JSON format as an [Incoming Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/IncomingNotification.md)
plus a zipped binary package containing content in a supported [Packaging Format](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/PACKAGING.md).

The following sections describe the HTTP methods, headers, body content and expected responses for each of the above endpoints and content.

### Important information about notification metadata

If you are providing metadata, you should include as much bibliographic and author identifying metadata as possible, to give
us the best chance of routing the content to a suitable repository.  For example, the following fields would be key:

| Field | Content |
|-------|---------|
| metadata.author.affiliation | The author's affiliation as a string.  Multiple affiliations can be included, but all condensed into a single string |
| metadata.author.identifier.id | An identifier for the author (e.g. their ORCID or email).  Ideally also populate metadata.author.identifier.type for each identifier |
| metadata.author.name | The author's name |
| metadata.project.grant_number | The grant number associated with the project from which the publication arises |
| metadata.title | The title of the article |
| metadata.source.identifier.id | The identifier of the journal for the publication, such as the ISSN.  Ideally also populate metadata.source.identifier.type for each identifier |
| metadata.identifier.id | An identifier for the article, such as the DOI.  Ideally also populate the metadata.identifier.type field for each identifier |

For the embargo period, you should ideally use **embargo.end**.  If this is provided, then **embargo.start** and **embargo.duration** 
would be considered secondary information not to be acted upon.

If you have publicly hosted content (e.g. splash pages, full-text web pages, or PDFs) that you want to share with the router, so that repositories can download the content directly, please place these in a **links** element.  For example:

    "links" : [
        {
            "type" : "splash",
            "format" : "text/html",
            "url" : "http://example.com/article1/index.html",
        },
        {
            "type" : "fulltext",
            "format" : "text/html",
            "url" : "http://example.com/article1/fulltext.html",
        },
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "url" : "http://example.com/article1/fulltext.pdf",
        }
    ]

### Validation Endpoint

The Validation API allows you to test that your data feed to the system will be successful.

You must have the user role "provider" to access this endpoint - if you do not have this role, please contact the Router administrator.

#### Metadata-only request

If you are sending only the notification JSON, the request must take the form:

    POST /validate?api_key=<api_key>
    Content-Type: application/json
    
    [Incoming Notification JSON]

#### Metadata + Package request

If you are sending binary content as well as the metadata, the request must take the form:

    POST /validate?api_key=<api_key>
    Content-Type: multipart/form-data; boundary=FulltextBoundary
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="metadata"
    Content-Type: application/json
    
    [Incoming Notification JSON]
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="content"
    Content-Type: application/zip
    
    [Package]
    
    --FulltextBoundary--

If you are carrying out this request you MUST include the **content.packaging_format** field in the notification metadata, 
and include the identifier to the appropriate format identifier as per the [Packaging Format](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/PACKAGING.md) documentation.

It is also possible to send a request which has limited/no JSON metadata, and relies entirely on any metadata embedded in the Package.

To do this, send the bare-minimum JSON notification, with only the format identifier of the package included.  For example:

    POST /validate?api_key=<api_key>
    Content-Type: multipart/form-data; boundary=FulltextBoundary
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="metadata"
    Content-Type: application/json
    
    {
        "content" : {
            "packaging_format" : "https://datahub.deepgreen.org/FilesAndJATS"
        },
    }
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="content"
    Content-Type: application/zip
    
    [Package]
    
    --FulltextBoundary--

#### Possible Responses

On authentication failure (e.g. invalid api_key, incorrect user role) the API will respond with a 401 (Unauthorised) and no response body.

On validation failure the system will respond with the following:

    HTTP 1.1  400 Bad Request
    Content-Type: application/json
    
    {
        "error" : "<human readable error message>"
    }

On validation success, the system will respond with 204 (No Content) and no response body.

### Notification Endpoint

The Notification API takes an identical request to the Validation API, so that you can develop
against the Validation API and then switch seamlessly over to live notifications.  The only difference will
be in the response body.

You must have the user role "provider" to access this endpoint - if you do not have this role, please contact the Router administrator.

The system will not attempt to aggressively validate the request, but the
request must still be well-formed in order to succeed, so you may still receive a validation error.

On a successful call to this endpoint, your notification will be accepted into the router, but note that acceptance of a 
notification is not the same as the notification having been entered into the system for routing - at this point it has 
only been accepted for processing.  Routing to the relevant repositories will happen later, asynchronously to the request.

#### Metadata-only request

If you are sending only the notification JSON, the request must take the form:

    POST /notification?api_key=<api_key>
    Content-Type: application/json
    
    [Incoming Notification JSON]

#### Metadata + Package request

If you are sending binary content, the request must take the form:

    POST /notification?api_key=<api_key>
    Content-Type: multipart/form-data; boundary=FulltextBoundary
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="metadata"
    Content-Type: application/json
    
    [Incoming Notification JSON]
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="content"
    Content-Type: application/zip
    
    [Package]
    
    --FulltextBoundary--

If you are carrying out this request you MUST include the **content.packaging_format** field in the notification metadata, 
and include the identifier to the appropriate format identifier as per the [Packaging Format](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/PACKAGING.md) documentation.

It is also possible to send a request which has limited/no JSON metadata, and relies entirely on any metadata embedded in the Package.

To do this, send the bare-minimum JSON notification, with only the format identifier of the package included.  For example:

    POST /notification?api_key=<api_key>
    Content-Type: multipart/form-data; boundary=FulltextBoundary
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="metadata"
    Content-Type: application/json
    
    {
        "content" : {
            "packaging_format" : "https://datahub.deepgreen.org/FilesAndJATS"
        },
    }
    
    --FulltextBoundary
    
    Content-Disposition: form-data; name="content"
    Content-Type: application/zip
    
    [Package]
    
    --FulltextBoundary--

#### Possible Responses

On authentication failure (e.g. invalid api_key, incorrect user role) the system will respond with a 401 (Unauthorised) and no response body.

In the event of a malformed HTTP request, the system will respond with a 400 (Bad Request) and the response body:

    HTTP 1.1  400 Bad Request
    Content-Type: application/json
    
    {
        "error" : "<human readable error message>"
    }

On successful completion of the request, the system will respond with 202 (Accepted) and the following response body

    HTTP 1.1  202 Accepted
    Content-Type: application/json
    Location: <url for api endpoint for accepted notification>
    
    {
        "status" : "accepted",
        "id" : "<unique identifier for the notification>",
        "location" : "<url path for api endpoint for newly created notification>"
    }


## For Repositories

If you are a repository, consuming notifications from the router, you have access to 2 endpoints:

1. The notification list feed
2. The notification endpoint

The first allows you to list all routed notifications to your repository, and to page through the list in date order.

The second allows you to retrieve individual notifications and the binary/packaged content asscoiated with it.

Notifications are represented in our native JSON format as an [Outgoing Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/OutgoingNotification.md)
(or a [Provider's Outgoing Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/ProviderOutgoingNotification.md) if you happend to also be the publisher
who created it).

Packaged content is available as a zipped file whose contents conform to a supported [Packaging Format](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/PACKAGING.md).

The following sections describe the HTTP methods, headers, body content and expected responses for each of the above endpoints and content.

### Notification List Feed

This endpoint lists routed notifications in "analysed_date" order (the date we analysed the content to determine its routing to your repository), oldest first.

You may list the notifications routed to your repository, or all notifications that were routed to any repository.

Note that as notifications are never updated (only created), this sorted list is guaranteed to be complete and include the same notifications 
each time for the same request (and any extra notifications created in the time period).  This is the reason for sorting by "analysed_dat"e rather than "created_date", as the rate
at which items pass through the analysis may vary.

Allowed parameters for each request are:

* **api_key** - Optional.  May be used for tracking API usage, but no authentication is required for this endpoint.
* **since** - Required.  Timestamp from which to provide notifications, of the form YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ (in UTC timezone); YYYY-MM-DD is considered equivalent to YYYY-MM-DDT00:00:00Z
* **page** - Optional; defaults to 1.  Page number of results to return.
* **pageSize** - Optional; defaults to 25, maximum 100.  Number of results per page to return.

#### Repository routed notifications

This endpoint lists all notifications routed to your repository.

You will not be able to tell from this endpoint which other repositories have been identified as targets for this notification.

    GET /routed/<repo_id>[?<params>]

Here, **repo_id** is your Router account id, which can be obtained from your account page.

#### All routed notifications

This endpoint lists all routed notifications (i.e. not notifications which were not matched to any repository), without restricting them to the repositories they have been routed to.

You will not be able to tell from this endpoint which repositories have been identified as targets for this notification.

    GET /routed[?<params>]

#### Possible Responses

If any of the required parameters are missing, or fall outside the allowed range, you will receive a 400 (Bad Request) and an error
message in the body:

    HTTP 1.1  400 Bad Request
    Content-Type: application/json
    
    {
        "error" : "<human readable error message>"
    }


On successful request, the response will be a 200 OK, with the following body

    HTTP 1.1  200 OK
    Content-Type: application/json
    
    {
        "since" : "<date from which results start in the form YYYY-MM-DDThh:mm:ssZ>",
        "page" : "<page number of results>,
        "pageSize" : "<number of results per page>,
        "timestamp" : "<timestamp of this request in the form YYYY-MM-DDThh:mm:ssZ>",
        "total" : "<total number of results at this time>",
        "notifications" : [
            "<ordered list of 'Outgoing Notification' JSON objects>"
        ]
    }

Note that the "total" may increase between requests, as new notifications are added to the end of the list.

See the [Outgoing Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/OutgoingNotification.md) data model for more info.

### Notification Endpoint

This endpoint will return to you the JSON record for an individual notification, or the packaged content associated with it.

#### Individual Notification

The JSON metadata associated with a notification is publicly accessible, so anyone can access this endpoint.

    GET /notification/<notification_id>

Here **notification_id** is the system's identifier for an individual notification.  You may get this identifier from,
for example, the **Notification List Feed**.

If the notification does not exist, you will receive a 404 (Not Found), and no response body.

If the you are not authenticated as the original publisher of the notification, and the notification has not yet been routed, 
you will also receive a 404 (Not Found) and no response body.

If the notification is found and has been routed, you will receive a 200 (OK) and the following response body:

    HTTP 1.1  200 OK
    Content-Type: application/json
    
    [Outgoing Notification JSON]

See the [Outgoing Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/OutgoingNotification.md) data model for more info.

Some notifications may contain one or more **links** elements.  In this event, this means that there is binary content
associated with the notification available for download.  Each of the links could be one of two kinds:

1. Packaged binary content held by the router on behalf of the publisher (see the next section)
2. A proxy-URL (proxying through the Router) for public content hosted on the web by the publisher

In either case you can issue a GET request on the URL, and receie the content.

In order to tell the difference between (1) and (2), compare the following two links:

    "links" : [
        {
            "type" : "package",
            "format" : "application/zip",
            "url" : "https://www.oa-deepgreen.de/api/v1/notification/123456789/content",
            "packaging" : "https://datahub.deepgreen.org/FilesAndJATS"
        },
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "url" : "https://www.oa-deepgreen.de/api/v1/notification/123456789/content/publisherpdf",
        }
    ]

The first link has type "package" and also has an element **packaging** which tells you this is of the format "https://datahub.deepgreen.org/FilesAndJATS".

The second link does not contain a **packaging** element at all, and does not have "package" as its type.

This means the first link is a link to package held by the router, and the second is a proxy for a URL hosted by the publisher.

#### Packaged Content

Some notifications may have binary content associated with them.  If this is the case, you will see one or more **links** elements
appearing in the [Outgoing Notification](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/OutgoingNotification.md) JSON that
you retrieve via either the **Notification List Feed** or the **Individual Notification**.

Router stores full-text content for a temporary period (currently 90 days, subject to review) from the date of receipt from publisher and so it must be retrieved by a
repository within this timescale.

You need to have the user role "provider" or "repository" to access this endpoint - if you do not have the required role, please contact the Router administrator.

The notification JSON may contain a section like:

    "links" : [
        {
            "type" : "package",
            "format" : "application/zip",
            "url" : "https://www.oa-deepgreen.de/api/v1/notification/123456789/content",
            "packaging" : "https://datahub.deepgreen.org/FilesAndJATS"
        },
        {
            "type" : "package",
            "format" : "application/zip",
            "url" : "https://www.oa-deepgreen.de/api/v1/notification/123456789/content/SimpleZip",
            "packaging" : "http://purl.org/net/sword/package/SimpleZip"
        }
    ]

In this case there are 2 packages available (both representing the same content).  One is in the "FilesAndJATS" format
that the publisher originally provided to the router, and the other is in the "SimpleZip" format to which the router has
converted the incoming package.

See the documentation on [Packaging Formats](https://github.com/OA-DeepGreen/jper/blob/develop/docs/api/PACKAGING.md) to understand
what each of the formats looks like.

You may then choose one of these links to download to receive all of the content (e.g. publisher's PDF, JATS XML, additional
image files) as a single zip file.  To request it, you will also need to provide your API key:

    GET <package url>?api_key=<api_key>

Authentication failure will result in a 401 (Unauthorised), and no response body.  Authentication failure can happen for
the following reasons:
* api_key is invalid
* You do not have the user role "provider" or "repository"
* You have the role "provider" and you were not the original creator of this notification
* You have the role "repository" and this notification has not yet been routed

If the notification content is not found, you will receive a 404 (Not Found) and no response body.

If the notification content is found and authentication succeeds you will receive a 200 (OK) and the binary content:

    HTTP 1.1  200 OK
    Content-Type: application/zip
    
    [Package]

Note that a successful access by a user with the role "repository" will log a successful delivery of content notification
into the router (used for reporting on the router's ability to support REF compliance).
