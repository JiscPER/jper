# JPER: Data Models

This document lists the core system objects which manage the process of taking a notification from the API and running
them through the routing process.

The diagram below shows the basic relationships between the objects as they pass through the Routing Process.

![ModelObjects](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/ModelObjects.png)

Each of the model objects is defined as a JSON document which is persisted in the Elasticsearch back-end.  The details
of each model object can be found under the following links:

* [Unrouted Notification](https://github.com/JiscPER/jper/blob/develop/docs/system/UnroutedNotification.md)
* [Routing Metadata](https://github.com/JiscPER/jper/blob/develop/docs/system/RoutingMetadata.md)
* [Repository Configuration](https://github.com/JiscPER/jper/blob/develop/docs/system/RepositoryConfig.md)
* [Match Provenance](https://github.com/JiscPER/jper/blob/develop/docs/system/MatchProvenance.md)
* [Failed Notification](https://github.com/JiscPER/jper/blob/develop/docs/system/FailedNotification.md)
* [Routed Notification](https://github.com/JiscPER/jper/blob/develop/docs/system/RoutedNotification.md)