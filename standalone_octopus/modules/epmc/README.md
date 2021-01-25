# EuropePMC Integration

## Client Library

This is a basic client library for accessing EuropePMC

```python
    from octopus.modules.epmc import client
```

Obtain metadata by a known identifier, such as the PMCID (returns a list, ideally of length 1)

```python
    mds = EuropePMC.get_by_pmcid("PMC12345678")
```

Search on any searchable field, such as title (returns a list of results):

```python
    mds = EuropePMC.field_search("TITLE", "The Title of my Article", fuzzy=True)
```

Obtain the fulltext XML (where available) for a given PMCID:

```python
    ft = EuropePMC.fulltext("PMC12345678")
```

Metadata is represented by the object **octopus.modules.empc.client.EPMCMetadata**

FullText is represened by the object **octopus.modules.epmc.client.EPMCFullText**