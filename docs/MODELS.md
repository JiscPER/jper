# JPER: Data Models

This document defines the core system models that will be used to represent the notifications as they 
arrive and are analysed and then delivered to repositories.

The overall flow of data through these models is as follows:

1. Incoming notifications are stored as **Unrouted Notifications**

2. **Unrouted Notifications** are read in via some asynchronous process which generates the **Routing Metadata**

3. The **Routing Metadata** is compared with the **Repository Configuration** and the **Repository Match Provenance** is created in the event of a match

4. The **Unrouted Notification** is enhanced with information from the analysis process and written as a **Routed Notification**

5. When repositories retrieve **Routed Notifications** and record of this is placed in the **Repository Retrievals** (required for analysis of REF compliance)

It also documents other key system entities such as the user account models.

## Unrouted Notification

```json
{
    "id" : "<opaque identifier for this notification>",
    "created_date" : "<date this notification was received>",
    "last_updated" : "<last modification time - required by storage layer>",
    
    "event" : "<keyword for the kind of notification: acceptance, publication, etc.>",
    
    "provider" : {
        "id" : "<user account id of the provider>",
        "agent" : "<string defining the software/process which put the content here, provided by provider - is this useful?>",
        "ref" : "<provider's globally unique reference for this research object>",
        "route" : "<method by which notification was received: native api, sword, ftp>"
    },
    
    "targets" : [
        {
            "repository" : "<identifying string for repository - base URL, user account>",
            "requirement" : "<must|should>"
        }
    ],
    
    "content" : {
        "packaging_format" : "<identifier for packaging format used>",
        "store_id" : "<information for retrieving the content from local store (tbc)>"
    },
    
    "links" : [
        {
            "type" : "<link type: splash|fulltext>",
            "format" : "<text/html|application/pdf|application/xml|application/zip|...>",
            "access" : "<type of access control on the resource: 'router' (reuqires router auth) or 'public' (no auth)>",
            "url" : "<provider's splash, fulltext or machine readable page>",
            "packaging" : "<packaging format identifier>"
        }
    ],
    
    "embargo" : {
        "end" : "<date embargo expires>",
        "start" : "<date embargo starts>",
        "duration" : "<number of months for embargo to run>"
    },
    
    "metadata" : {
        "title" : "<publication title>",
        "version" : "<version of the record, e.g. AAM>",
        "publisher" : "<publisher of the content>",
        "source" : {
            "name" : "<name of the journal or other source (e.g. book)>",
            "identifier" : [
                {"type" : "issn", "id" : "<issn of the journal (could be print or electronic)>" },
                {"type" : "eissn", "id" : "<electronic issn of the journal>" },
                {"type" : "pissn", "id" : "<print issn of the journal>" },
                {"type" : "doi", "id" : "<doi for the journal or series>" }
            ]
        },
        "identifier" : [
            {"type" : "doi", "id" : "<doi for the record>" }
        ],
        "type" : "publication/content type",
        "author" : [
            {
                "name" : "<author name>",
                "identifier" : [
                    {"type" : "orcid", "id" : "<author's orcid>"},
                    {"type" : "email", "id" : "<author's email address>"},
                ],
                "affiliation" : "<author affiliation>"
            }
        ],
        "language" : "<iso language code>",
        "publication_date" : "<publication date>",
        "date_accepted" : "<date accepted for publication>",
        "date_submitted" : "<date submitted for publication>",
        "license_ref" : {
            "title" : "<name of licence>",
            "type" : "<type>", 
            "url" : "<url>", 
            "version" : "<version>",
        },
        "project" : [
            {
                "name" : "<name of funder>", 
                "identifier" : [
                    {"type" : "<identifier type>", "id" : "<funder identifier>"}
                ],
                "grant_number" : "<funder's grant number>"
            }
        ],
        "subject" : ["<subject keywords/classifications>"]
    }
}
```

Note that *target* will not be implemnented in the first version of this system

## Routed Notification

A **Routed Notification** is almost the same as an **Unrouted Notification**, with the following data structure added to it.

Note also:

* ids persist from unrouted to routed notifications
* created_date persists from unrouted to routed notifications
* The *target* field of the **Unrouted Notification** will be removed as it is superseded by the repository matches

```json
{
    "analysis_date" : "<date the routing analysis was carried out>",
    "repositories" : ["<ids of repository user accounts whcih match this notification>"]
}
```

## Routing Metadata

This model may or may not need to be persisted to the index.  It is likely that it exists entirely for use in-memory,
though by providing an encapsulated model we gain the ability to serialise it in the future with ease, or to serialise
it for testing purposes.

```json
{
    "urls" : ["<list of affiliation urls found in the data>"],
    "emails" : ["<list of contact emails found in the data>"],
    "affiliations" : ["<names of organisations found in the data>"],
    "author_ids" : [
        {
            "id" : "<author id string>",
            "type" : "<author id type (e.g. orcid, or name)>"
        }
    ],
    "postcodes" : ["<postcodes found in the data>"],
    "keywords" : ["<keywords and subject classifications found in the data>"],
    "grants" : ["<grant names or numbers found in the data>"],
    "content_types" : ["<list of content types of the object (probably just one)>"]
}
```

Note that *content_types* will not be implemented in this version of the system

## Repository Configuration

This defines the data that repositories will need to provide for matches against the **Routing Metadata** to happen

```json
{
    "id" : "<opaque id for repository config record>",
    "created_date" : "<date the configuration was originally created>",
    "last_updated" : "<last modification time - required by storage layer>",
    
    "repository" : "<account id of repository that owns this configuration>",
    "domains" : ["<list of all domains that match this repository's institution>"],
    "name_variants" : ["<The names by which this repository's institution is known>"],
    "author_ids" : [
        {
            "id" : "<author id string>",
            "type" : "<author id type (e.g. orcid, or name)>"
        }
    ],
    "postcodes" : ["<list of postcodes that appear in the repository's institution's addresses>"],
    "keywords" : ["<keywords and subject classifications>"],
    "grants" : ["<grant names or numbers>"],
    "content_types" : ["<list of content types the repository is interested in>"]
}
```

Note that *content_types* will not be implemented in this version of the system

## Repository Match Provenance

When a repository is matched to a notification, the repository managers may wish to review the cause of those matches
in order to refine their configuration.  This object records the match taking place and the reasons for it.

```json
{
    "id" : "<opaque id for match provenance record>",
    "created_date" : "<date the configuration was originally created>",
    "last_updated" : "<last modification time - required by storage layer>",
    
    "repository" : "<account id of repository to which the match pertains>",
    "notification" : "<id of the notification to which the match pertains>",
    "provenance" : [
        {
            "source_field" : "<field from the configuration that matched>",
            "term" : "<term from the configuration that matched>",
            "notification_field" : "<field from the notification that matched>"
            "matched" : "<text from the notification routing metadata that matched>",
            "explanation" : "<any additional explanatory text to go with this match (e.g. description of levenstein criteria)>"
        }
    ]
}
```

## Repository Retrievals

For REF compliance analysis it will be important to record when a repository retrieves a record from the router.

In order to maintan an append-only approach to the router indices, records of these retrievals will be stored in a 
simple index which notes the time of the access, and what was accessed.

```json
{
    "id" : "<opaque id for repository retrieval record>",
    "created_date" : "<date the configuration was originally created>",
    "last_updated" : "<last modification time - required by storage layer>",
    
    "repository" : "<user id of repository doing the retrieval>",
    "notification" : "<id of the notification retrieved>",
    "content" : "<the url or internal identifier of the content retrieved>",
    "retrieval_date" : "<date the repository retrieved the record>",
    "scope" : "<what the repository actually retrieved: notification, fulltext>"
}
```

## User Account

A single user account object that covers the three major user classes: Admin, Provider and Repository.  By having
a single model, one user can have multiple roles, which will be useful in testing.  Each user class will have some
of the additional fields beyond the basic authentication.

* repository -for "repository" user class
* sword_repository - for "repository" user class
* embargo - for "provider" user class
* sword_provider - for "provider" user class
* ftp_provider - for "provider" user class

Also for the packaging section, note that for any repository that is going to use SWORDv2 there needs to be a
package identifier here, or they won't be able to get any content.  That should, at minimum, contain the SimpleZip
identifier, but may also include the FilesAndJATS identifier (TBC).

    SimpleZip = http://purl.org/net/sword/package/SimpleZip

```json
{
    "id" : "<unique persistent account id>",
    "created_date" : "<date account created>",
    "last_updated" : "<date account last modified>",
    
    "email" : "<account contact email>",
    "contact_name" : "<name of key contact>",
    "password" : "<hashed password for ui login>",
    "api_key" : "<api key for api auth>",
    "role" : ["<account role: repository, provider, admin>"],
    
    "repository" : {
        "name" : "<name of the repository>",
        "url" : "<url for the repository>"
    },
    
    "sword_repository" : {
        "username" : "<username for the router to authenticate with the repository>",
        "password" : "<reversibly encrypted password for the router to authenticate with the repository>",
        "collection" : "<url for deposit collection to receive content from the router>"
    },
    
    "packaging" : [
        "<identifier - in order of preference - that should be available for this repo.  Esp. via sword interface>" 
    ],
    
    "embargo" : {
        "duration" : "<length of default embargo>",
        "from" : "<reference to field in data to measure embargo from>"
    }
}
```
