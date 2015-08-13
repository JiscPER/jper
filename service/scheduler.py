'''
This is the application scheduler. 
It defines scheduled tasks and runs them as per their defined schedule.

This scheduler is started and stopped when the app is started and stopped. 
It is presumed to run on one machine at present.

If scaling later requires having multiple machines, then this scheduler should only run on the machine that has access to 
the relevant directories. Or, if scheduled tasks themselves also need to be scaled up, the scheduler can continue to run on 
all machines but some synchronisation would have to be added to that tasks were not run on every machine. Also, each machine 
running the schedule would need access to any relevant directories.
'''

import schedule, time, os, shutil, requests, datetime
from threading import Thread

from service import models, routing

# TODO set this somewhere sensible, but note it may not be the live url because we could send it locally depending on server setup
apikey = "" # TODO should this be the apikey of a special user that runs from the ftp, or do we do this with the api key of the user that did the ftp upload?
apiurl = "https://pubrouter.jisc.ac.uk/api/v2/" + "notification?api_key=" + apikey
tmpdirbase = "/tmp/"
tmpbupdir = "/home/mark/ftptmp/"


def checkftp():
    try:
        print "checking ftp..."
        # list all directories on /home/sftpusers (one for each publisher)
        userdirs = os.listdir('/home/sftpusers')
        for dir in userdirs:
            thisdir = userdirs + '/' + dir + '/xfer'
            if os.path.isdir(thisdir):
                if len(os.listdir(thisdir)) > 0:
                    # TODO: add a check for the folder name to see if matching user is logged in, by subprocessing the w command
                    # in which case do nothing on this iteration because the user is probably in the process of sending files
                    # but if not empty and not in use, move the contents to a tmp dir
                    tmpdir = tmpdirbase + dir
                    if not os.path.exists(tmpdir): os.makedirs(tmpdir)
                    for file in os.listdir(thisdir):
                        srcf = os.path.join(thisdir, file)
                        dstf = os.path.join(tmpdir, file)
                        shutil.move(srcf,dstf)
                        
                    # unzip everything (could be stuff for more than one article in there...)
                    # so a loop may be needed for the following
                    
                    # find the config file and create a notification?
                    notification = {}
                    
                    # rezip and prep the pkg url for sending the zip to the API
                    pkg = tmpdir + 'sth'

                    # send to the API to get put on the unroutednotification index
                    files = [
                        ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
                        ("content", ("content.zip", open(pkg, "rb"), "application/zip"))
                    ]
                    resp = requests.post(apiurl, files=files)
                    # TODO check the resp and if all good remove the files, but if not what?
                    
                    # for the moment copy the content from tmp to somewhere just in case
                    tmnow = datetime.datetime.strftime(datetime.datetime.now(), '%Y_%m_%d_%H_%M_%S')
                    tmpbupdirnow = tmpbupdir + tmnow
                    if not os.path.exists(tmpbupdirnow): os.makedirs(tmpbupdirnow)
                    for file in os.listdir(tmpdir):
                        srcf = os.path.join(tmpdir, file)                        
                        dstf = os.path.join(tmpbupdirnow, file)
                        shutil.move(srcf,dstf)
                        
                    # empty and delete the tmp dir
                    shutil.rmtree(tmpdir)
    except:
        print "failed to check ftp"

schedule.every(10).minutes.do(checkftp)


def checkunrouted():
    try:
        print "checking for unrouted notifications"
        # query the service.models.unroutednotification index
        # returns a list of unrouted notification from the last three up to four months
        urids = [i['_source']['id'] for i in models.Unroutednotification().query(q="*",size="100000").get('hits',[]).get('hits',[])]

        # run service.routing.route on them
        for urid in urids:
            unfn = models.Unroutednotification(urid)
            routing.route(unfn)
    except:
        print "failed to check for unrouted notifications"

schedule.every(10).minutes.do(checkunrouted)


def cheep():
    print "scheduled cheep"
    
schedule.every(1).minutes.do(cheep)

def run():
    while True:
        schedule.run_pending()
        time.sleep(1)

def go():
    thread = Thread(target = run)
    thread.daemon = True
    thread.start()
    


'''
Other things that could be scheduled later:

backups

schedule dropping unwanted indexes - such as unwanted unrouted notification time types, old logs

schedule generating stats for reports

schedule an ftp folder check / cleanout

schedule sword deposits to institutions

'''