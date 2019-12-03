'''
This is the application scheduler. 
It defines scheduled tasks and runs them as per their defined schedule.

This scheduler is started and stopped when the app is started and stopped. 
Unless RUN_SCHEDULE is set to False in the config. In which case it must be started manually / managed by supervisor.
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

import schedule, time, os, shutil, requests, datetime, tarfile, zipfile, subprocess, getpass, uuid, json, csv
from threading import Thread
from octopus.core import app, initialise
from service import reports
import models

if app.config.get('DEEPGREEN_EZB_ROUTING',False):
    import routing_deepgreen as routing
else:
    import routing


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
        # 2019-11-18 TD : add the actual path for extraction here
        tar.extractall(path=path)
        #tar.extractall()
        tar.close()
        app.logger.debug('Extracted tar ' + fl)
        return True
    except:
        try:
            with zipfile.ZipFile(fl) as zf:
                # 2019-11-18 TD : replace the 'hand made' routine by the libary call
                zf.extractall(path=path)
                # 2019-11-18 TD : this loop apparently does not work with nested folder 
                #                 structures, so we discard it
                # for member in zf.infolist():
                #     # Path traversal defense copied from
                #     # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
                #     words = member.filename.split('/')
                #     for word in words[:-1]:
                #         drive, word = os.path.splitdrive(word)
                #         head, word = os.path.split(word)
                #         if word in (os.curdir, os.pardir, ''): continue
                #         path = os.path.join(path, word)
                #     zf.extract(member, path)
            app.logger.debug('Extracted zip ' + fl)
            return True
        except Exception as e:
            app.logger.error('Scheduler - Extraction could not be done for ' + fl + ' : "{x}"'.format(x=e.message))
            return False

def flatten(destination, depth=None):
    if depth is None:
        depth = destination
    app.logger.debug('Flatten depth set ' + destination + ' ' + depth)
    #
    # 2019-11-18 TD : Introducing the '.xml' file as recursion stop. 
    #                 If an .xml file is found in a folder in the .zip file then this 
    #                 *is* a single publication to be separated from the enclosing .zip file
    has_xml = False
    for fl in os.listdir(depth):
        if 'article_metadata.xml' in fl: # De Gruyter provides a second .xml sometimes, sigh.
            os.remove(depth + '/' + fl)
            continue
        if not has_xml and '.xml' in fl:
            app.logger.debug('Flatten ' + fl + ' found in folder')
            has_xml = True
            words = destination.split('/')
            stem = words[-1] + '/' + os.path.splitext(fl)[0]
            if not os.path.exists(destination + '/' + stem):
                os.makedirs(destination + '/' + stem)
                app.logger.debug('Flatten new ' + destination + '/' + stem + ' created')
    # 2019-11-18 TD : end of recursion stop marker search
    #
    for fl in os.listdir(depth):
        app.logger.debug('Flatten at ' + fl)
        # 2019-11-18 TD : Additional check for 'has_xml' (the stop marker)
        # if '.zip' in fl: # or '.tar' in fl:
        if not has_xml and '.zip' in fl: # or '.tar' in fl:
            app.logger.debug('Flatten ' + fl + ' is an archive')
            extracted = extract(depth + '/' + fl, depth)
            if extracted:
                app.logger.debug('Flatten ' + fl + ' is extracted')
                os.remove(depth + '/' + fl)
                flatten(destination,depth)
        # 2019-11-18 TD : Additional check for 'has_xml' (the stop marker)
        # elif os.path.isdir(depth + '/' + fl):
        elif os.path.isdir(depth + '/' + fl) and not has_xml:
            app.logger.debug('Flatten ' + fl + ' is not a file, flattening')
            flatten(destination, depth + '/' + fl)
        else:
            try:
                # shutil.move(depth + '/' + fl, destination)
                # 2019-11-18 TD : Some 'new' +stem dst place to move all the single pubs into
                if has_xml and os.path.isdir(destination + '/' + stem):
                    shutil.move(depth + '/' + fl, destination + '/' + stem)
                else:
                    shutil.move(depth + '/' + fl, destination)
            except:
                pass

# 2016-11-30 TD : routine to peak in flattened packages, looking for a .xml file floating around
def pkgformat(src):
    # our first best guess...
    ### pkg_fmt = "https://datahub.deepgreen.org/FilesAndJATS"
    pkg_fmt = "unknown"
    for fl in os.listdir(src):
        app.logger.debug('Pkgformat at ' + fl)
        if '.xml' in fl:
            app.logger.debug('Pkgformat tries to open ' + src + '/' + fl)
            try:
                with open(src + '/' + fl,'r') as f:
                    for line in f:
                        if "//NLM//DTD Journal " in line:
                            pkg_fmt = "https://datahub.deepgreen.org/FilesAndJATS"
                            break
                        elif "//NLM//DTD JATS " in line:
                            pkg_fmt = "https://datahub.deepgreen.org/FilesAndJATS"
                            break
                        elif "//RSC//DTD RSC " in line:
                            pkg_fmt = "https://datahub.deepgreen.org/FilesAndRSC"
                            break

            except:
                app.logger.info('Pkgformat could not open ' + src + '/' + fl)

            # there shall only be *one* .xml as per package
            break

    app.logger.debug('Pkgformat returns ' + pkg_fmt)
    return pkg_fmt

#
# 2019-07-17 TD : change target of the move operation to the big dg_storage for all deliveries
#
def moveftp():
    try:
        # # move any files in the jail of ftp users into the temp directory for later processing
        # tmpdir = app.config.get('TMP_DIR','/tmp')
        pubstoredir = app.config.get('PUBSTOREDIR','/data/dg_storage')
        userdir = app.config.get('USERDIR','/home/sftpusers')
        userdirs = os.listdir(userdir)
        app.logger.info("Scheduler - from FTP folders found " + str(len(userdirs)) + " user directories")
        for dir in userdirs:
            # 2019-07-30 TD : One more loop over possible subfolders of the user
            #                 Please note: They are *exclusively* created by 'createFTPuser.sh' 
            #                 At least, there should be the (old) 'xfer' folder
            founditems = False
            for xfer in os.listdir(userdir + '/' + dir):
                # if len(os.listdir(userdir + '/' + dir + '/xfer')):
                if len(os.listdir(userdir + '/' + dir + '/' + xfer)):
                    founditems = True
                    # for thisitem in os.listdir(userdir + '/' + dir + '/xfer'):
                    for thisitem in os.listdir(userdir + '/' + dir + '/' + xfer):
                        app.logger.info('Scheduler - moving file ' + thisitem + ' for Account:' + dir)
                        fl = os.path.dirname(os.path.abspath(__file__)) + '/models/moveFTPfiles.sh'
                        try:
                            newowner = getpass.getuser()
                        except:
                            newowner = 'green'
                        uniqueid = uuid.uuid4().hex
                        # targetdir = tmpdir + '/' + dir
                        # uniquedir = tmpdir + '/' + dir + '/' + uniqueid
                        targetdir = pubstoredir + '/' + dir
                        # 2019-07-17 TD : introduce a new directory that will indicate pending items
                        pendingdir = pubstoredir + '/' + dir + '/pending'
                        uniquedir = pubstoredir + '/' + dir + '/' + uniqueid
                        # moveitem = userdir + '/' + dir + '/xfer/' + thisitem
                        moveitem = userdir + '/' + dir + '/' + xfer + '/' + thisitem
                        subprocess.call( [ 'sudo', fl, dir, newowner, targetdir, uniqueid, uniquedir, moveitem, pendingdir ] )

            if founditems is False:
                app.logger.debug('Scheduler - found nothing to move for Account:' + dir)
    except:
        app.logger.error("Scheduler - move from FTP failed")
        
if app.config.get('MOVEFTP_SCHEDULE',10) != 0:
    schedule.every(app.config.get('MOVEFTP_SCHEDULE',10)).minutes.do(moveftp)


#
# 2019-07-17 TD : process the big delivery/publisher dg_storage for all pending items
#
def copyftp():
    try:
        # copy any files in the big delivery/publisher dg_storage into the temp dir for processing
        tmpdir = app.config.get('TMP_DIR','/tmp')
        maxtransacts = app.config.get('MAX_TMPDIR_TRANSACTS_PER_ACC',99)
        pubstoredir = app.config.get('PUBSTOREDIR','/data/dg_storage')
        pubstoredirs = os.listdir(pubstoredir)
        app.logger.info("Scheduler - from DG-STORAGE folders found " + str(len(pubstoredirs)) + " user directories")
        for dir in pubstoredirs:
            # 2019-07-29 TD : check if 'tmpdir/dir' exists at all
            if os.path.exists(tmpdir + '/' + dir) is False:
                os.makedirs(tmpdir + '/' + dir)
            # 2019-07-17 TD : limit temp dir to 100 transactions per account
            if len(os.listdir(tmpdir + '/' + dir)) > maxtransacts:
                app.logger.info('Scheduler - skipping this copy process because len(transactions)>' + str(maxtransacts) + ' in temp directory for Account:' + dir)
                continue
            if len(os.listdir(pubstoredir + '/' + dir + '/pending')):
                for transact in os.listdir(pubstoredir + '/' + dir + '/pending'):
                    if len(os.listdir(tmpdir + '/' + dir)) > maxtransacts:
                        break
                    app.logger.info('Scheduler - copying folder of transaction ' + transact + ' for Account:' + dir)
                    src = pubstoredir + '/' + dir + '/pending/' + transact
                    dst = tmpdir + '/' + dir + '/' + transact
                    # subprocess.call( [ 'cp -R', ...] )
                    shutil.rmtree(dst, ignore_errors=True) # target MUST NOT exist!
                    shutil.copytree(src, dst)
                    try:
                        os.remove(src) # try to take the pending symlink away
                    except Exception as e:
                        app.logger.error("Scheduler - failed to delete pending entry: '{x}'".format(x=e.message))
            else:
                app.logger.debug('Scheduler - currently, nothing to copy for Account:' + dir)
    except:
        app.logger.error("Scheduler - copy from DG-STORAGE failed")

if app.config.get('COPYFTP_SCHEDULE',10) != 0:
    schedule.every(app.config.get('COPYFTP_SCHEDULE',10)).minutes.do(copyftp)


def processftp():
    try:
        # list all directories in the temp dir - one for each ftp user for whom files have been moved from their jail
        userdir = app.config.get('TMP_DIR','/tmp')
        userdirs = os.listdir(userdir)
        app.logger.debug("Scheduler - processing for FTP found " + str(len(userdirs)) + " temp user directories")
        for dir in userdirs:
            # configure for sending anything for the user of this dir
            apiurl = app.config['API_URL']
            acc = models.Account().pull(dir)
            if acc is None:
                continue
            apiurl += '?api_key=' + acc.data['api_key']
            # there is a uuid dir for each item moved in a given operation from the user jail
            for udir in os.listdir(userdir + '/' + dir):
                thisdir = userdir + '/' + dir + '/' + udir
                app.logger.debug('Scheduler - processing ' + thisdir + ' for Account:' + dir)
                for xpub in os.listdir(thisdir):
                    pub = xpub
                    # should be a dir per publication notification - that is what they are told to provide
                    # and at this point there should just be one pub in here, whether it be a file or directory or archive
                    # if just a file, even an archive, dump it into a directory so it can be zipped easily
                    if os.path.isfile(thisdir + '/' + pub):
                        nf = uuid.uuid4().hex
                        os.makedirs(thisdir + '/' + nf)
                        shutil.move(thisdir + '/' + pub, thisdir + '/' + nf + '/')
                        pub = nf
                    
                    # by now this should look like this:
                    # /Incoming/ftptmp/<useruuid>/<transactionuuid>/<uploadeddirORuuiddir>/<thingthatwasuploaded>

                    # they should provide a directory of files or a zip, but it could just be one file
                    # but we don't know the hierarchy of the content, so we have to unpack and flatten it all
                    # unzip and pull all docs to the top level then zip again. Should be jats file at top now
                    flatten(thisdir + '/' + pub)

                    # 2019-11-18 TD : 'flatten' has been modified to process bulk deliveries
                    #                 (i.e. more then one pub per zip file!) as well.
                    #                 If it is bulk, there maybe a lot of zip files, and 
                    #                 we need a loop:
                    pdir = thisdir
                    if os.path.isdir(thisdir + '/' + pub + '/' + pub):
                        pdir = thisdir + '/' + pub + '/' + pub
                    #
                    for singlepub in os.listdir(pdir):
                        # 2016-11-30 TD : Since there are (at least!?) 2 formats now available, we have to find out
                        ## 2019-11-18 TD : original path without loop where zip file is packed
                        ##                 from  source folder "thisdir + '/' + pub"
                        ## pkg_fmt = pkgformat(thisdir + '/' + pub)
                        ## #
                        ## pkg = thisdir + '/' + pub + '.zip'
                        ## zip(thisdir + '/' + pub, pkg)
                        ##
                        pkg_fmt = pkgformat(pdir + '/' + singlepub)
                        #
                        pkg = pdir + '/' + singlepub + '.zip'
                        zip(pdir + '/' + singlepub, pkg)

                        # create a notification and send to the API to join the unroutednotification index
                        notification = {
                            "content": { "packaging_format": pkg_fmt }
                            #"content": {"packaging_format": "https://datahub.deepgreen.org/FilesAndJATS"}
                            ## "content": {"packaging_format": "https://pubrouter.jisc.ac.uk/FilesAndJATS"}
                        }
                        files = [
                            ("metadata", ("metadata.json", json.dumps(notification), "application/json")),
                            ("content", ("content.zip", open(pkg, "rb"), "application/zip"))
                        ]
                        app.logger.debug('Scheduler - processing POSTing ' + pkg + ' ' + json.dumps(notification))
                        resp = requests.post(apiurl, files=files, verify=False)
                        if str(resp.status_code).startswith('4') or str(resp.status_code).startswith('5'):
                            app.logger.error('Scheduler - processing completed with POST failure to ' + apiurl + ' - ' + str(resp.status_code) + ' - ' + resp.text)
                        else:
                            app.logger.info('Scheduler - processing completed with POST to ' + apiurl + ' - ' + str(resp.status_code))

                shutil.rmtree(userdir + '/' + dir + '/' + udir, ignore_errors=True) # 2019-12-02 TD : kill "udir" folder no matter what status

    except Exception as e:
        app.logger.error('Scheduler - failed scheduled process for FTP temp directories: "{x}"'.format(x=e.message))

if app.config.get('PROCESSFTP_SCHEDULE',10) != 0:
    schedule.every(app.config.get('PROCESSFTP_SCHEDULE',10)).minutes.do(processftp)


def checkunrouted():
    urobjids = []
    robjids = []
    counter = 0
    limit = app.config.get('CHECKUNROUTED_SCHEDULE',10) * 5
    # 2019-06-13 TD : to cope with mass deliveries, we have to limit the next loop 
    #                 (factor 10 times the time to the next call seems reasonable...)
    try:
        app.logger.debug("Scheduler - check for unrouted notifications")
        # query the service.models.unroutednotification index
        # returns a list of unrouted notification from the last three up to four months
        counter = 0
        for obj in models.UnroutedNotification.scroll():
            counter += 1
            res = routing.route(obj)
            if res:
                robjids.append(obj.id)
            else:
                urobjids.append(obj.id)
            # 2019-06-13 TD : to cope with mass deliveries, we have to limit 
            #                 the loop over the unrouted notifs
            if counter >= limit:
                break

        # 2017-06-06 TD : replace str() by .format() string interpolation
        app.logger.debug("Scheduler - routing sent {cnt} notification(s) for routing".format(cnt=counter))

        if app.config.get("DELETE_ROUTED", False) and len(robjids) > 0:
            # 2017-06-06 TD : replace str() by .format() string interpolation
            app.logger.debug("Scheduler - routing deleting {x} of {cnt} unrouted notification(s) that have been processed and routed".format(x=len(robjids),cnt=counter))
            models.UnroutedNotification.bulk_delete(robjids)
            # 2017-05-17 TD :
            time.sleep(2) # 2 seconds grace time

        if app.config.get("DELETE_UNROUTED", False) and len(urobjids) > 0:
            # 2017-06-06 TD : replace str() by .format() string interpolation
            app.logger.debug("Scheduler - routing deleting {x} of {cnt} unrouted notifications that have been processed and were unrouted".format(x=len(urobjids),cnt=counter))
            models.UnroutedNotification.bulk_delete(urobjids)
            # 2017-05-17 TD :
            time.sleep(2) # again, 2 seconds grace

    except Exception as e:
        app.logger.error("Scheduler - Failed scheduled check for unrouted notifications: cnt={cnt}, len(robjids)={a}, len(urobjids)={b}".format(cnt=counter,a=len(robjids),b=len(urobjids)))
        app.logger.error("Scheduler - Failed scheduled check for unrouted notifications: '{x}'".format(x=e.message))

if app.config.get('CHECKUNROUTED_SCHEDULE',10) != 0:
    schedule.every(app.config.get('CHECKUNROUTED_SCHEDULE',10)).minutes.do(checkunrouted)



def monthly_reporting():
    # python schedule does not actually handle months, so this will run every day and check whether the current month has rolled over or not
    try:
        app.logger.debug('Scheduler - Running monthly reporting')
        
        # create / update a monthly deliveries by institution report
        # it should have the columns HEI, Jan, Feb...
        # and rows are HEI names then count for each month
        # finally ends with sum total (total of all numbers above) 
        # and unique total (total unique objects accessed - some unis may have accessed the same one)
        # query the retrieval index to see which institutions have retrieved content from the router in the last month
        
        month = datetime.datetime.now().strftime("%B")[0:3]
        year = str(datetime.datetime.now().year)
        app.logger.debug('Scheduler - checking monthly reporting for ' + month + ' ' + year)
        reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
        if not os.path.exists(reportsdir): os.makedirs(reportsdir)
        monthtracker = reportsdir + '/monthtracker.cfg'
        try:
            lm = open(monthtracker,'r')
            lastmonth = lm.read().strip('\n')
            lm.close()
        except:
            lm = open(monthtracker,'w')
            lm.close()
            lastmonth = ''
            
        if lastmonth != month:
            app.logger.debug('Scheduler - updating monthly report of notifications delivered to institutions')
            lmm = open(monthtracker,'w')
            lmm.write(month)
            lmm.close()
        
            # get the month number that we are reporting on
            tmth = datetime.datetime.utcnow().month - 1

            # if the month is zero, it means the year just rolled over
            if tmth == 0:
                tmth = 12
                lastyear = int(year) - 1
                frm = str(lastyear) + "-" + str(tmth) + "-01T00:00:00Z"
                to_date = str(year) + "-01-01T00:00:00Z"
            else:
                mnthstr = str(tmth) if tmth > 9 else "0" + str(tmth)
                nexmnth = str(tmth + 1) if tmth + 1 > 9 else "0" + str(tmth + 1)
                frm = str(year) + "-" + mnthstr + "-01T00:00:00Z"
                if tmth == 12:
                    nextyear = int(year) + 1
                    to_date = str(nextyear) + "-01-01T00:00:00Z"
                else:
                    to_date = str(year) + "-" + nexmnth + "-01T00:00:00Z"

            # specify the file that we're going to output to
            reportfile = reportsdir + '/monthly_notifications_to_institutions_' + year + '.csv'

            # run the delivery report
            reports.delivery_report(frm, to_date, reportfile)

            # necessary tasks for other monthly reporting could be defined here
            # reporting that has to run more regularly could be defined as different reporting methods altogether
            # and controlled with different settings in the config
            
    except Exception as e:
        app.logger.error("Scheduler - Failed scheduled reporting job: '{x}'".format(x=e.message))
  
if app.config.get('SCHEDULE_MONTHLY_REPORTING',False):
    schedule.every().day.at("00:05").do(monthly_reporting)

    
def delete_old_routed():
    app.logger.info('Scheduler - checking for old routed indexes to delete')
    try:
        # each day send a delete to the index name that is beyond the range of those to keep
        # so only actually has an effect on the first day of each month - other days in the month it is sending a delete to an index that is already gone
        # index names look like routed201601
        # so read from config how many months to keep, and add 1 to it
        # so if in March, and keep is 3, then it becomes 4
        keep = app.config.get('SCHEDULE_KEEP_ROUTED_MONTHS',3) + 1
        year = datetime.datetime.utcnow().year
        # subtracting the keep gives us a month of -1 if now March
        month = datetime.datetime.utcnow().month - keep
        if month < 1:
            # so roll back the year, and set the month to 11 (if now March)
            year = year - 1
            month = 12 + month
        # so idx would look like routed201511 if now March - meaning we would keep Dec, Jan, and Feb (and Mar currently in use of course)
        idx = 'routed' + str(year) + str(month)
        addr = app.config['ELASTIC_SEARCH_HOST'] + '/' + app.config['ELASTIC_SEARCH_INDEX'] + '/' + idx
        app.logger.debug('Scheduler - sending delete to ' + addr)
        # send the delete - at the start of a month this would delete an index. Other days it will just fail
        requests.delete(addr)
    except Exception as e:
        app.logger.error("Scheduler - Failed monthly routed index deletion: '{x}'".format(x=e.message))

if app.config.get('SCHEDULE_DELETE_OLD_ROUTED',False):
    schedule.every().day.at("03:00").do(delete_old_routed)

    
def cheep():
    app.logger.debug("Scheduled cheep")
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
    

if __name__ == "__main__":
    initialise()
    print "starting scheduler"
    app.logger.debug("Scheduler - starting up directly in own process.")
    run()
    
