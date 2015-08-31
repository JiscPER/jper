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

import schedule, time, os, shutil, requests, datetime, tarfile, zipfile
from threading import Thread
from octopus.core import app

from service import models, routing

# TODO set this somewhere sensible, but note it may not be the live url because we could send it locally depending on server setup
apikey = "" # TODO should this be the apikey of a special user that runs from the ftp, or do we do this with the api key of the user that did the ftp upload?
apiurl = "https://pubrouter.jisc.ac.uk/api/v2/" + "notification?api_key=" + apikey
tmpdirbase = "/tmp/"
tmpbupdir = "/home/mark/ftptmp/"


# functions for the checkftp to unzip and move stuff up then zip again in incoming packages
def zip(src, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()
def extract(destination, depth=None):
    if not depth:
        depth = []
    for file_or_dir in os.listdir(os.path.join([destination] + depth, "\\")):
        if os.path.isfile(file_or_dir):
            try:
                tar = tarfile.open(file_or_dir)
                tar.extractall()
                tar.close()
            except:
                try:
                    zip = zipfile.open(file_or_dir)
                    zip.extractall()
                    zip.close()
                except:
                    pass                   
        else:
            extract(destination, os.path.join(depth + [file_or_dir], "\\"))    
def flatten(destination, depth=None):
    if not depth:
        depth = []
    for file_or_dir in os.listdir(os.path.join([destination] + depth, "\\")):
        if os.path.isfile(file_or_dir):
            shutil.move(file_or_dir, destination)
        else:
            flatten(destination, os.path.join(depth + [file_or_dir], "\\"))

def checkftp():
    try:
        app.logger.info("Scheduled check for FTP")
        # list all directories on /home/sftpusers (one for each publisher)
        userdirs = os.listdir('/home/sftpusers')
        app.logger.info("Scheduled check for FTP found " + str(len(userdirs)) + " user directories")
        for dir in userdirs:
            thisdir = userdirs + '/' + dir + '/xfer'
            if os.path.isdir(thisdir):
                if len(os.listdir(thisdir)) > 0:
                    # TODO: add a check for the folder name to see if matching user is logged in, by subprocessing the w command
                    # in which case do nothing on this iteration because the user is probably in the process of sending files
                    # if not empty and not in use, move the contents to a tmp dir
                    tmpdir = tmpdirbase + dir
                    if not os.path.exists(tmpdir): os.makedirs(tmpdir)
                    for file in os.listdir(thisdir):
                        srcf = os.path.join(thisdir, file)
                        dstf = os.path.join(tmpdir, file)
                        shutil.move(srcf,dstf)
                        
                    # assume a directory per publication - that is what they are told to provide
                    # unzip everything then pull all docs to the top level then zip again. Should be jats file at top now
                    app.logger.info("Scheduled check for FTP processing for " + thisdir)
                    extract(tmpdir)
                    flatten(tmpdir)
                    ts = datetime.datetime.strftime(datetime.datetime.now(), '%Y_%m_%d_%H_%M_%S')
                    pkg = tmpdir + '/' + dir + '_' + ts
                    zip(tmpdir,pkg)
                    pkg += '.zip'
                    
                    # create a notification
                    notification = {
                        "content": "https://pubrouter.jisc.ac.uk/FilesAndJATS"
                    }

                    # send to the API to get put on the unroutednotification index
                    files = [
                        ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
                        ("content", ("content.zip", open(pkg, "rb"), "application/zip"))
                    ]
                    resp = requests.post(apiurl, files=files)
                    # TODO check the resp and if all good remove the files, but if not what?
                    
                    # for the moment copy original content and created zip from tmp to somewhere just in case
                    tmnow = datetime.datetime.strftime(datetime.datetime.now(), '%Y_%m_%d_%H_%M_%S')
                    tmpbupdirnow = tmpbupdir + tmnow
                    if not os.path.exists(tmpbupdirnow): os.makedirs(tmpbupdirnow)
                    for file in os.listdir(tmpdir):
                        srcf = os.path.join(tmpdir, file)                        
                        dstf = os.path.join(tmpbupdirnow, file)
                        shutil.move(srcf,dstf)
                    shutil.move(pkg,os.path.join(tmpbupdirnow, pkg.split('/')[-1]))
                        
                    # empty and delete the tmp dir and the zip
                    #os.remove(pkg) commented out because currently is temporarily moved by code just above instead
                    shutil.rmtree(tmpdir)
    except:
        app.logger.error("FAILED scheduled check for FTP")

schedule.every(10).minutes.do(checkftp)


def checkunrouted():
    try:
        app.logger.info("Scheduled check for unrouted notifications")
        # query the service.models.unroutednotification index
        # returns a list of unrouted notification from the last three up to four months
        for obj in models.Unroutednotification.scroll():
            routing.route(obj)
    except:
        app.logger.error("FAILED scheduled check for unrouted notifications")

schedule.every(10).minutes.do(checkunrouted)


def cheep():
    app.logger.info("Scheduled cheep")
    
#schedule.every(1).minutes.do(cheep)

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