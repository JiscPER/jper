# UnroutedNotification

```json
{
    "content": {
        "packaging_format": "string", 
        "store_id": "string"
    }, 
    "created_date": "2015-11-24T11:41:00Z", 
    "embargo": {
        "duration": 0, 
        "end": "2015-11-24T11:41:00Z", 
        "start": "2015-11-24T11:41:00Z"
    }, 
    "event": "string", 
    "id": "string", 
    "last_updated": "2015-11-24T11:41:00Z", 
    "links": [
        {
            "access": "string", 
            "format": "string", 
            "packaging": "string", 
            "proxy": "string", 
            "type": "string", 
            "url": "string"
        }
    ], 
    "metadata": {
        "author": [
            {
                "affiliation": "string", 
                "identifier": [
                    {
                        "id": "string", 
                        "type": "string"
                    }
                ], 
                "name": "string"
            }
        ], 
        "date_accepted": "2015-11-24T11:41:00Z", 
        "date_submitted": "2015-11-24T11:41:00Z", 
        "identifier": [
            {
                "id": "string", 
                "type": "string"
            }
        ], 
        "language": "string", 
        "license_ref": {
            "title": "string", 
            "type": "string", 
            "url": "string", 
            "version": "string"
        }, 
        "project": [
            {
                "grant_number": "string", 
                "identifier": [
                    {
                        "id": "string", 
                        "type": "string"
                    }
                ], 
                "name": "string"
            }
        ], 
        "publication_date": "2015-11-24T11:41:00Z", 
        "publisher": "string", 
        "source": {
            "identifier": [
                {
                    "id": "string", 
                    "type": "string"
                }
            ], 
            "name": "string"
        }, 
        "subject": [
            "string"
        ], 
        "title": "string", 
        "type": "string", 
        "version": "string"
    }, 
    "provider": {
        "agent": "string", 
        "id": "string", 
        "ref": "string", 
        "route": "string"
    }
}
```

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| content.packaging_format |  | unicode |  |  |
| content.store_id |  | unicode |  |  |
| created_date |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| embargo.duration |  | int |  |  |
| embargo.end |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| embargo.start |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| event |  | unicode |  |  |
| id |  | unicode |  |  |
| last_updated |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| links.access |  | unicode |  | router, public |
| links.format |  | unicode |  |  |
| links.packaging |  | unicode |  |  |
| links.proxy |  | unicode |  |  |
| links.type |  | unicode |  |  |
| links.url |  | unicode | URL |  |
| metadata.author.affiliation |  | unicode |  |  |
| metadata.author.identifier.id |  | unicode |  |  |
| metadata.author.identifier.type |  | unicode |  |  |
| metadata.author.name |  | unicode |  |  |
| metadata.date_accepted |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| metadata.date_submitted |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| metadata.identifier.id |  | unicode |  |  |
| metadata.identifier.type |  | unicode |  |  |
| metadata.language |  | unicode | 3 letter ISO language code |  |
| metadata.license_ref.title |  | unicode |  |  |
| metadata.license_ref.type |  | unicode |  |  |
| metadata.license_ref.url |  | unicode | URL |  |
| metadata.license_ref.version |  | unicode |  |  |
| metadata.project.grant_number |  | unicode |  |  |
| metadata.project.identifier.id |  | unicode |  |  |
| metadata.project.identifier.type |  | unicode |  |  |
| metadata.project.name |  | unicode |  |  |
| metadata.publication_date |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| metadata.publisher |  | unicode |  |  |
| metadata.source.identifier.id |  | unicode |  |  |
| metadata.source.identifier.type |  | unicode |  |  |
| metadata.source.name |  | unicode |  |  |
| metadata.subject |  | unicode |  |  |
| metadata.title |  | unicode |  |  |
| metadata.type |  | unicode |  |  |
| metadata.version |  | unicode |  |  |
| provider.agent |  | unicode |  |  |
| provider.id |  | unicode |  |  |
| provider.ref |  | unicode |  |  |
| provider.route |  | unicode |  |  |
