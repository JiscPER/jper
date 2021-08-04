# JPER System Overview

The Jisc Publications Router (JPER) consumes publication event notifications from publishers, analyses their content
and routes them to appropriate repositories, based on information those repositories provide regarding the publications
they are interested in.

The content is accessible via a well-defined API with authorisation constraints.  Publishers and repositories have user
accounts which give them access to this API.

The API is then wrapped with convenience services that represent it in ways familiar to the user base, so that it can
either be accessed directly or via a familiar method such as FTP, Swordv2, or OAI-PMH.

The below diagram shows, in broad terms, the structure of the application.

![ArchitectureOverview](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/ArchitectureOverview.png)

Publishers send the system notifications, which are a combination of JSON metadata and packaged binary content (such
as XML metadata files and fulltext PDFs, etc).  The system accepts these notifications into the index, then they are
matched against repositories based on information each repository gives JPER regarding the notifications they are
interested in (based on information such as affiliation, author identifiers, grant codes, etc).  The matched notifications
are then made available via the API for repositories to consume and ingest into their own archives.

## Core Features

The documentation in this directory contain information about the following core features of the system:

* The Data Models: There are core system model objects which represent user accounts, notifications, metadata and repository 
configurations.  They are stored and managed primarily as JSON structures.

* Data Workflows: As data enters and moves around the core it goes through various transformations and analyses, such as initial
ingest, routing/matching to repositories, and retrieval.

For information on how each of the external modules which consume the API work (SWORDv2, OAI-PMH) you should see their
respective code repositories and documentation.