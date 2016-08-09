# RepositoryConfig

The JSON structure of the model is as follows:

```json
{
    "author_ids": [
        {
            "id": "string", 
            "type": "string"
        }
    ], 
    "content_types": [
        "string"
    ], 
    "created_date": "string", 
    "domains": [
        "string"
    ], 
    "grants": [
        "string"
    ], 
    "id": "string", 
    "keywords": [
        "string"
    ], 
    "last_updated": "string", 
    "name_variants": [
        "string"
    ], 
    "postcodes": [
        "string"
    ], 
    "repo": "string", 
    "strings": [
        "string"
    ]
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| author_ids.id | author identifier (e.g. their email) to match on | unicode |  |  |
| author_ids.type | author identifier type (e.g. "email") | unicode |  |  |
| content_types | list of content types of interest - stored, but not used in this version of the system | unicode |  |  |
| created_date | Date this record was created | unicode |  |  |
| domains | Domains operated by the institution | unicode |  |  |
| grants | grant ids that the institution may be interested in | unicode |  |  |
| id | opaque, persistent system identifier for this record | unicode |  |  |
| keywords | freetext keywors to match on - stored, but not used in this version of the system | unicode |  |  |
| last_updated | Date this record was last modified | unicode |  |  |
| name_variants | Names by which the institution is known | unicode |  |  |
| postcodes | Postcodes for addresses where to match on | unicode |  |  |
| repo |  | unicode |  |  |
| strings | list of arbitrary match strings | unicode |  |  |
