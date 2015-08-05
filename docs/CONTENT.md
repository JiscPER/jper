# Content Workflow

**NOTE: this document is not part of the system specification - it's some thoughts on how best to handle content**

PROPOSAL: All content that is publicly accessible should be provided by reference, all other content should be provided by value.

ADDENDUM: Not only should the content be publicly accessible by reference, but it must be under a GETtable URL (so, not POST, or any other method)

NOTE: in the case that publicly accessible by-reference files are provided, the system will not be able to track accesses to that
content.  This means that we may need to explicitly receive notifications of retrieval from API users.

## Mechanisms by which content comes into the system

Content may arrive into the system or via the system in a number of ways:

1. By value - attached to a notification as a zip file

2. By reference - via one or more links provided in the notification

The second option further breaks down into several kinds of by-reference:

a. Publicly accessible links - anyone with the URL can retrieve the content

b. Links only accessible to the router - only the router can retrieve the content

c. Links accessible to repositories - on the repository (possibly via its institution's credentials) can retrieve the content

Options (b) and (c) may provide access to the resources via a number of routes: IP restriction, explicit username/password, or authentication token.

Because of these layers of complexity in handling restricted by-reference files, see the proposal above that all by-reference files be freely retrievable


## Workflow for each content delivery approach

* by-value - store the content in the system storage later, and enhance the notification with a link in the metadata which points to the url for it

```json
{
    "id" : "<notification id>",
    "links" : [
        {
            "type" : "fulltext",
            "format" : "application/zip",
            "url" : "/api/v1/notification/<id>/content",
            "access" : "router",
            "packaging" : "http://pubrouter.jisc.ac.uk/packages/FilesAndJATS"
        }
    ]
}
```

"access: router" means that to use the link the caller will need to use their router credentials.

* by-reference - all by reference links should be public, so no action is required by the router.  The link metadata should be:

```json
{
    "id" : "<notification id>",
    "links" : [
        {
            "type" : "fulltext",
            "format" : "application/pdf",
            "url" : "http://example.publisher.com/content/file.pdf",
            "access" : "public"
        }
    ]
}
```

"access: public" means that there is no restriction on the use of the link