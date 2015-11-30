# Processing Workflows

This document outlines the main workflows involved in processing notifications coming in from publishers, being analysed, 
and identified for routing to specific repositories based on the repository accounts configuration.

## Feed Validation

In order to avoid having to run expensive-to-execute validation code against every notification that comes into the system 
(as there may be many thousands a day), the system allows publishers to send notification requests to a validation
endpoint as part of their set-up process, before committing to send them to the real notification endpoint.  

The diagram below shows sample notifications coming in to the Validation API, which is almost identical to the Notification 
API, and that requests must be authenticated and authorised as they would in the live feed.  Notifications are then 
validated to a suitable level: 

* check that the package can be unzipped
* that the JSON metadata from the native API is well-formed
* any JATS XML metadata or full-text is readable and schema compliant.  

It will not attempt to verify the integrity of any additional full-text files (such as PDFs) which come with the package.  
It will attempt to confirm that any by-reference links sent in the notification resolve to actual files, to ensure that 
publisher’s URLs are working correctly (again, the content of those files will not be validated).

![FeedValidation](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/FeedValidation.png)


## Notification

Notification proceeds in a very similar form to validation: the publisher sends the Notification to the Notification API, 
is authenticated and authorised and then the notification is stored in a temporary location and accepted without further 
validation.  At this point the Notification API responds to confirm that the Notification has been received successfully.  

At the same time it triggers a process of analysis of the deposit held in temporary storage which operates asynchronously 
to the publisher’s request.  This extracts data from the notification, analyses 
the potential affiliations, and relates Notifications to the repositories interested in that content.

![CreateNotification](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/CreateNotification.png)

## Match and Routing

Analysis of a Notification to determine the appropriate routing takes place asynchronously from the request to the 
Notification API by the publisher.

First notifications are unpacked; they may contain:
 
* native JSON metadata from the API
* JATS XML metadata and full-texts
* references to other files hosted by the publisher
* actual copies of binary files.  

We are only interested in analysing the JSON and the JATS.

The next step is to extract all useful metadata from the item that could be used for routing.  We start with the 
bibliographic metadata which may contain important keywords and content type information, then a deep analysis of the NLM/JATS-formatted 
files for potential affiliation information; this may include author names and affiliation fields, email addresses and 
URLs, ORCIDs, postal addresses and department names and keywords, etc.

Once there is a corpus of information extracted from the Notification which can be used to potentially route it to any 
interested repository, then we compare this data with the configurations for each of the repositories signed up for 
the service (see the section on User Accounts and Interface for more details), and locate accounts which meet the criteria.

The list of interested repositories is then be added to the Notification to produce an Routed Notification which will 
then be stored.  Any related files, such as the JATS files and additional binary content will be placed in medium-term 
storage (to be held as long as the retention policy requires), meanwhile the Routed Notification is written to an 
index for easy retrieval.

![MatchRouting](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/MatchRouting.png)

Also see the MATCH documentation for more details on how the match itself proceeds.

## Retrieval

The routing for a particular repository of a Notification has already been calculated by the time the repository comes to 
query for its content, and the Routed Notification has been created and stored in a way suitable for rapid querying.  
Note that the consequence of this is that repositories will only receive notifications after they have signed up, and if 
they change their configuration they will only receive notifications matching the new configuration going forwards.

The repository therefore provides a retrieve request to the Notification API, with some parameters such as the time-box for the notifications, 
the number to return per page, or their cursor’s position in a multi-page request (see the API documentation for details).  

Once their request has been authorised, we query the Routed Notification index for notifications which have been routed to that repository 
and which additionally meet the request parameters.

![Retrieval](https://raw.githubusercontent.com/JiscPER/jper/develop/docs/system/Retrieval.png)
