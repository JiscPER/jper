# RoutingMetadata

The JSON structure of the model is as follows:

```json
{
    "affiliations": [
        "string"
    ], 
    "author_ids": [
        {
            "id": "string", 
            "type": "string"
        }
    ], 
    "content_types": [
        "string"
    ], 
    "emails": [
        "string"
    ], 
    "grants": [
        "string"
    ], 
    "keywords": [
        "string"
    ], 
    "postcodes": [
        "string"
    ], 
    "urls": [
        "string"
    ]
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| affiliations | list of author affiliations to match on | unicode |  |  |
| author_ids.id | author identifier (e.g. their email) to match on | unicode |  |  |
| author_ids.type | author identifier type (e.g. "email") | unicode |  |  |
| content_types | list of content types of interest - stored, but not used in this version of the system | unicode |  |  |
| emails | email addresses which appear in the match data | unicode |  |  |
| grants | grant ids that the institution may be interested in | unicode |  |  |
| keywords | freetext keywors to match on - stored, but not used in this version of the system | unicode |  |  |
| postcodes | Postcodes for addresses where to match on | unicode |  |  |
| urls | Any urls found in the notification metadata - currently not populated | unicode |  |  |
