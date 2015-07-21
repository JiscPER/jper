# Event to Repository Matching Algorithm.

This document describes the fields available for routing incoming publications, using Match data extracted from the
metadata and package files, and comparing it with a configuration supplied by the repository to define the match criteria

## Fields in the Match data

The following fields may be extracted from the incoming metadata

* URLs
* Emails
* Affiliations
* Author Identifiers
* Postcodes
* Grants
* Keywords
* Content Types

## Fields in the Repository Config

The repository configuration may contain the following fields

* Domains
* Name Variants
* Author Identifiers
* Postcodes
* Grants
* Keywords
* Content Types
* Arbitrary Strings

## Paired fields and analysis required

In each of these paired sets of fields, the criteria for a successful match is defined.  A publication as a whole
will be considered to have been matched to a repository if one or more of these fields matches exactly.

Note that here "exact match" means that the lowercased, whitespace-trimmed strings from each field are the same.

* Domain <-> URL - normalise the domain: strip prefixes and URL paths.  If either ends with the other, it is a match
* Domain <-> Email - normalise the domain: strip prefixes an URL paths.  Normalise the email: strip everything before @.  If either ends with the other it is a match
* Name Variant <-> Affiliation - normalised name variant must be an exact substring of normalised affiliation
* Author Identifier <-> Email - exact match required
* Author Identifier <-> Author Identifier - exact match required
* Postcode <-> Postcode - Normalise postcodes: strip whitespace and lowercase, then exact match required
* Keyword <-> Keyword - exact match required
* Grant <-> Grant - exact match required
* Content Type <-> Content Type - exact match required
* Arbitrary String <-> URL - Normalise the String and the URL: strip prefixes and URL paths.  If either ends with the other, it is a match
* Arbitrary String <-> email - exact match required
* Arbitrary String <-> Affiliation - normalised string must be an exact substring of normalised affiliation
* Arbitrary String <-> Author ID - exact match required
* Arbitrary String <-> Postcode - Normalise postcodes: strip whitespace and lowercase, then exact match required
* Arbitrary String <-> Grant - exact match requried

## Defining sub-categories to be matched

A repository may specify both keywords and content types to ingest.  If the repository configuration specifies any
keywords or any subject types, then any publications matched by the process described in the previous section will
also need to match one or more keyword and one or more content type.

NOTE: at the moment, the data in the keyword and content type fields are highly variable, so it is strongly advised
that repository configurations DO NOT set these fields.  We should consider their part in the routing more carefully
in the future.