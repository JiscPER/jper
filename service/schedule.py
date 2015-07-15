'''

write a schedule

monitor the incoming ftp folder
fire any new files into the api
which will put them on the unroutednotification index
move the object into the store

monitor the unroutednotification index (query it with the service.models.unroutednotification dao)
will give me unrouted ones from the last three up to four months
and then do service.routing.route on them

our backlog is the files in the ftp folder, and the unroutednotification index

schedule backups? - ask Mike

schedule dropping unwanted indexes - such as unwanted unrouted notification time types, old logs

schedule generating stats for reports

schedule an ftp folder check / cleanout

schedule sword deposits to institutions

'''