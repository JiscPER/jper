# MatchProvenance

The JSON structure of the model is as follows:

```json
{
    "created_date": "string", 
    "id": "string", 
    "last_updated": "string", 
    "notification": "string", 
    "provenance": [
        {
            "explanation": "string", 
            "matched": "string", 
            "notification_field": "string", 
            "source_field": "string", 
            "term": "string"
        }
    ], 
    "repo": "string"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| created_date | Date this record was created | unicode |  |  |
| id | opaque, persistent system identifier for this record | unicode |  |  |
| last_updated | Date this record was last modified | unicode |  |  |
| notification | id of the notification this record relates to | unicode |  |  |
| provenance.explanation | reason for the match | unicode |  |  |
| provenance.matched | Value in the repository configuration field which matched | unicode |  |  |
| provenance.notification_field | Field in the notification which matched | unicode |  |  |
| provenance.source_field | Field in the repository configuration which matched | unicode |  |  |
| provenance.term | term in the notification metadata which matched | unicode |  |  |
| repo |  | unicode |  |  |
