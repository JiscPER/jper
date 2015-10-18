'''
This is the application scheduler. 
It defines scheduled tasks and runs them as per their defined schedule.

This scheduler is started and stopped when the app is started and stopped. 
It is presumed to run on one machine at present.

If scaling later requires having multiple machines, then this scheduler should only run on the machine that has access to 
the relevant directories. There is a task that moves files from ftp user jail directories to tmp processing locations, and 
this is the limitation - creating sftp accounts has to happen on one machine or across machines, but that would increase 
attack surface for security vulnerability. So probably better to have only one machine open to sftp, and if necessary for 
later scale the script that is called to move data from the sftp jails to processing locations could do so by round-robin 
to multiple processing machines. The jper app config has settings for running this scheduler and what frequencies to run each 
process, so it is just a case of installing jper on each machine but only setting the frequencies for the processes desired to 
be scheduled on each given machine.

Or, if scheduled tasks themselves also need to be scaled up, the scheduler can continue to run on 
all machines but some synchronisation would have to be added to that tasks were not run on every machine. Also, each machine 
running the schedule would need access to any relevant directories.
'''

import schedule, time, os, shutil, requests, datetime, tarfile, zipfile, subprocess, getpass, uuid, json
from threading import Thread
from octopus.core import app

import models, routing


# functions for the checkftp to unzip and move stuff up then zip again in incoming packages
def zip(src, dst):
    zf = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()
def extract(fl,path):
    app.logger.debug('Extracting ' + fl)
    try:
        # TODO the tar method has not yet been tested...
        tar = tarfile.open(fl)
        tar.extractall()
        tar.close()
        app.logger.debug('Extracted tar ' + fl)
        return True
    except:
        try:
            with zipfile.ZipFile(fl) as zf:
                for member in zf.infolist():
                    # Path traversal defense copied from
                    # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
                    words = member.filename.split('/')
                    for word in words[:-1]:
                        drive, word = os.path.splitdrive(word)
                        head, word = os.path.split(word)
                        if word in (os.curdir, os.pardir, ''): continue
                        path = os.path.join(path, word)
                    zf.extract(member, path)
            app.logger.debug('Extracted zip ' + fl)
            return True
        except:
            app.logger.debug('Extraction could not be done for ' + fl)
            return False
def flatten(destination, depth=None):
    if depth is None:
        depth = destination
    app.logger.debug('Flatten depth set ' + destination + ' ' + depth)
    for fl in os.listdir(depth):
        app.logger.debug('Flatten at ' + fl)
        if os.path.isfile(depth + '/' + fl):
            app.logger.debug('Flatten ' + fl + ' is file')
            extracted = extract(depth + '/' + fl, depth)
            if extracted:
                app.logger.debug('Flatten ' + fl + ' is extracted')
                os.remove(depth + '/' + fl)
                flatten(destination,depth)
            else:
                try:
                    shutil.move(depth + '/' + fl, destination)
                except:
                    pass
        else:
            app.logger.debug('Flatten ' + fl + ' is not a file, flattening')
            flatten(destination, depth + '/' + fl)


def moveftp():
    try:
        # move any files in the jail of ftp users into the temp directory for later processing
        tmpdir = app.config.get('TMP_DIR','/tmp')
        userdir = app.config.get('USERDIR','/home/sftpusers')
        userdirs = os.listdir(userdir)
        app.logger.info("Scheduler - from FTP folders found " + str(len(userdirs)) + " user directories")
        for dir in userdirs:
            if len(os.listdir(userdir + '/' + dir + '/xfer')):
                app.logger.info('Scheduler - moving files for Account:' + dir)
                fl = os.path.dirname(os.path.abspath(__file__)) + '/models/moveFTPfiles.sh'
                try:
                    newowner = getpass.getuser()
                except:
                    newowner = 'mark'
                uniquedir = tmpdir + '/' + dir + '/' + uuid.uuid4().hex
                subprocess.call( [ 'sudo', fl, dir, newowner, userdir, tmpdir, uniquedir ] )
            else:
                app.logger.info('Scheduler - found nothing to move for Account:' + dir)
    except:
        app.logger.info("Scheduler - for move from FTP failed")
        
if app.config.get('MOVEFTP_SCHEDULE',10) != 0:
    schedule.every(app.config.get('MOVEFTP_SCHEDULE',10)).minutes.do(moveftp)

    
def processftp():
    try:
        # list all directories in the temp dir - one for each ftp user for whom files have been moved from their jail
        userdir = app.config.get('TMP_DIR','/tmp')
        userdirs = os.listdir(userdir)
        app.logger.info("Scheduler - processing for FTP found " + str(len(userdirs)) + " temp user directories")
        for dir in userdirs:
            # configure for sending anything for the user of this dir
            apiurl = app.config['API_URL']
            acc = models.Account().pull(dir)
            apiurl += '?api_key=' + acc.data['api_key']
            # there is a uuid dir of everything moved in a given operation from the user jail
            for udir in os.listdir(userdir + '/' + dir):
                thisdir = userdir + '/' + dir + '/' + udir
                app.logger.info('Scheduler - processing ' + thisdir + ' for Account:' + dir)
                for pub in os.listdir(thisdir):
                    # should be a dir per publication notification - that is what they are told to provide
                    # so if not, dump whatever this is into a directory
                    if os.path.isfile(thisdir + '/' + pub):
                        nf = uuid.uuid4().hex
                        os.makedirs(thisdir + '/' + nf)
                        shutil.move(thisdir + '/' + pub, thisdir + '/' + nf + '/')
                        pub = nf

                    # unzip and pull all docs to the top level then zip again. Should be jats file at top now
                    flatten(thisdir + '/' + pub)
                    pkg = thisdir + '/' + pub + '.zip'
                    zip(thisdir + '/' + pub, pkg)

                    # create a notification and send to the API to join the unroutednotification index
                    notification = {
                        "content": {"packaging_format": "https://pubrouter.jisc.ac.uk/FilesAndJATS"}
                    }
                    files = [
                        ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
                        ("content", ("content.zip", open(pkg, "rb"), "application/zip"))
                    ]
                    app.logger.debug('Scheduler - processing POSTing ' + pkg + ' ' + json.dumps(notification))
                    resp = requests.post(apiurl, files=files, verify=False)
                    app.logger.info('Scheduler - processing completed with POST to ' + apiurl + ' - ' + str(resp.status_code))
                                            
            shutil.rmtree(userdir + '/' + dir)
    except:
        app.logger.error("Scheduler - failed scheduled process for FTP temp directories")

if app.config.get('PROCESSFTP_SCHEDULE',10) != 0:
    schedule.every(app.config.get('PROCESSFTP_SCHEDULE',10)).minutes.do(processftp)


def checkunrouted():
    objids = []
    try:
        app.logger.info("Scheduler - check for unrouted notifications")
        # query the service.models.unroutednotification index
        # returns a list of unrouted notification from the last three up to four months
        counter = 0
        for obj in models.UnroutedNotification.scroll():
            counter += 1
            res = routing.route(obj)
            if res: objids.append(obj.id)
        app.logger.info("Scheduler - routing sent " + str(counter) + " notifications for routing")
        if app.config.get("DELETE_UNROUTED", False) and len(objids) > 0:
            app.logger.info("Scheduler - routing deleting " + str(len(objids)) + " of " + str(counter) + " unrouted notifications that have been processed and routed")
            models.UnroutedNotification.bulk_delete(objids)
    except Exception as e:
        app.logger.error("Scheduler - Failed scheduled check for unrouted notifications: '{x}'".format(x=e.message))

if app.config.get('CHECKUNROUTED_SCHEDULE',10) != 0:
    schedule.every(app.config.get('CHECKUNROUTED_SCHEDULE',10)).minutes.do(checkunrouted)


    
    
def cheep():
    app.logger.info("Scheduled cheep")
    print "Scheduled cheep"
#schedule.every(1).minutes.do(cheep)

def run():
    while True:
        schedule.run_pending()
        time.sleep(1)

def go():
    thread = Thread(target = run)
    thread.daemon = True
    thread.start()
    

