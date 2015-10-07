from octopus.core import app, add_configuration
import threading, time, os, uuid, shutil, json, string
from datetime import datetime, timedelta
from random import randint, random, triangular
from octopus.modules.jper import client
from service.tests import fixtures
from octopus.lib import dates, http, isolang
from copy import deepcopy

def _load_keys(path):
    with open(path) as f:
        return f.read().split("\n")

def _load_repo_configs(path):
    with open(path) as f:
        return json.loads(f.read())

def _select_from(arr, probs=None):
    if probs is None:
        return arr[randint(0, len(arr) - 1)]
    else:
        r = random()
        s = 0
        for i in range(len(probs)):
            s += probs[i]
            if s > r:
                return arr[i]
        return arr[len(arr) - 1]

def _select_n(arr, n):
    selection = []

    idx = range(0, len(arr))
    for x in range(n):
        if len(idx) == 0:
            break
        i = randint(0, len(idx) - 1)
        selection.append(arr[idx[i]])
        del idx[i]

    return selection

def _random_string(shortest, longest):
    length = randint(shortest, longest)
    s = ""
    pool = string.ascii_letters + "    "    # inject a few extra spaces, to increase their prevalence
    for i in range(length):
        l = randint(0, len(pool) - 1)
        s += pool[l]
    return s

def _random_url():
    return "http://example.com/file/" + uuid.uuid4().hex

def _random_datetime(since):
    epoch = datetime.fromtimestamp(0)
    lower_delta = since - epoch
    lower = int(lower_delta.total_seconds())

    now = datetime.now()
    upper_delta = now - epoch
    upper = int(upper_delta.total_seconds())

    seconds = randint(lower, upper)
    return datetime.fromtimestamp(seconds)

def _random_issn():
    first = randint(1000, 9999)
    second = randint(100, 999)
    return str(first) + "-" + str(second) + str(_select_from([1, 2, 3, 4, 5, 6, 7, 8, 9, "X"]))

def _random_doi():
    return "10." + _random_string(3, 4) + "/" + _random_string(5, 10)

def _random_email():
    return _random_string(10, 15) + "@" + _random_string(10, 15) + "." + _select_from(["ac.uk", "edu", "com"])

def _make_notification(error=False, routable=0, repo_configs=None):
    if error:
        return {"something" : "broken"}

    # get a base notification from the test fixtures
    note = fixtures.APIFactory.incoming()

    # now overwrite everything with randomised content
    note["event"] = _select_from(["accepted", "published"])
    note["provider"]["agent"] = _random_string(4, 10)
    note["provider"]["ref"] = _random_string(5, 6)

    note["links"] = []
    for i in range(randint(0, 5)):
        link = {}
        link["type"] = _select_from(["fulltext", "splash"])
        link["format"] = _select_from(["application/pdf", "text/html"])
        link["url"] = _random_url()
        note["links"].append(link)

    es = _random_datetime(datetime.fromtimestamp(0))
    ee = _random_datetime(es)
    note["embargo"]["start"] = es.strftime("%Y-%m-%dT%H:%M:%SZ")
    note["embargo"]["end"] = ee.strftime("%Y-%m-%dT%H:%M:%SZ")
    note["embargo"]["duration"] = int((ee - es).total_seconds() / (60 * 60 * 24 * 30))

    note["metadata"]["title"] = _random_string(50, 200)
    note["metadata"]["version"] = _select_from(["AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"])
    note["metadata"]["publisher"] = _random_string(10, 25)
    note["metadata"]["source"]["name"] = _random_string(30, 100)
    note["metadata"]["source"]["identifier"] = [{"type" : "issn", "id" : _random_issn()}]

    note["metadata"]["identifier"][0]["id"] = _random_doi()

    note["metadata"]["author"] = []
    for i in range(randint(1, 3)):
        author = {}
        author["name"] = _random_string(10, 20)
        author["identifier"] = [{"type" : "email", "id" : _random_email()}]
        author["affiliation"] = _random_string(10, 40)
        note["metadata"]["author"].append(author)

    note["metadata"]["language"] = _select_from(isolang.ISO_639_2)[0]

    ds = _random_datetime(datetime.fromtimestamp(0))
    da = _random_datetime(ds)
    pd = _random_datetime(da)
    note["metadata"]["publication_date"] = pd.strftime("%Y-%m-%dT%H:%M:%SZ")
    note["metadata"]["date_accepted"] = da.strftime("%Y-%m-%dT%H:%M:%SZ")
    note["metadata"]["date_submitted"] = ds.strftime("%Y-%m-%dT%H:%M:%SZ")

    note["metadata"]["license_ref"] = {}
    note["metadata"]["license_ref"]["title"] = _select_from(["CC0", "CC BY", "CC BY-SA", "CC BY-SA-ND"])
    note["metadata"]["license_ref"]["type"] = note["metadata"]["license_ref"]["title"]
    note["metadata"]["license_ref"]["url"] = "http://creativecommons.org/" + note["metadata"]["license_ref"]["title"].lower().replace(" ", "-")
    note["metadata"]["license_ref"]["version"] = _select_from(["1.0", "2.0", "3.0", "4.0"])

    note["metadata"]["project"] = []
    for i in range(randint(1, 2)):
        project = {}
        project["name"] = _random_string(3, 6)
        project["identifier"] = [{"type" : "ringold", "id" : _random_string(10, 16)}]
        project["grant_number"] = _random_string(5, 7)
        note["metadata"]["project"].append(project)

    note["metadata"]["subject"] = []
    for i in range(randint(0, 10)):
        note["metadata"]["subject"].append(_random_string(10, 15))

    # now determine if we are going to add routing metadata to this notification
    route = _select_from([True, False], [routable, 1 - routable])

    # we're not going to route it, the random content alone is sufficient
    if not route:
        return note

    route_to = _select_n(repo_configs, randint(1, len(repo_configs)))

    uber = {}
    for cfg in route_to:
        field = _select_from(["domains", "name_variants", "author_ids", "postcodes", "grants", "strings"])
        idx = randint(0, len(cfg[field]) - 1)
        if field not in uber:
            uber[field] = []
        uber[field].append(cfg[field][idx])

    # now layer the uber match record over the randomised notification
    for k, v in uber.iteritems():
        if k == "domains":
            # add an author with that domain in their email
            for domain in v:
                author = {}
                author["name"] = _random_string(10, 20)
                author["identifier"] = [{"type" : "email", "id" : _random_string(10, 12) + "@" + domain}]
                note["metadata"]["author"].append(author)
        elif k == "name_variants":
            # add an author with that name variant in their affiliation
            for nv in v:
                author = {}
                author["name"] = _random_string(10, 20)
                author["affiliation"] = nv
                note["metadata"]["author"].append(author)
        elif k == "author_ids":
            # add an author with these properties
            for aid in v:
                author = {}
                if aid.get("type") == "name":
                    author["name"] = aid.get("id")
                else:
                    author["name"] = _random_string(10, 20)
                    author["identifier"] = [{"type" : aid.get("type"), "id" : aid.get("id")}]
                note["metadata"]["author"].append(author)
        elif k == "postcodes":
            # add an author with that postcode in their affiliation
            for postcode in v:
                author = {}
                author["name"] = _random_string(10, 20)
                author["affiliation"] = postcode
                note["metadata"]["author"].append(author)
        elif k == "grants":
            # add a project with that grant number
            for grant in v:
                project = {}
                project["name"] = _random_string(3, 6)
                project["grant_number"] = grant
                note["metadata"]["project"].append(project)
        elif k == "strings":
            # add an author with that string in their affiliation
            for s in v:
                author = {}
                author["name"] = _random_string(10, 20)
                author["affiliation"] = s
                note["metadata"]["author"].append(author)

    return note

def _get_file_path(parent_dir, max_file_size, error=False):
    # sort out a file path
    fn = uuid.uuid4().hex + ".zip"
    path = os.path.join(parent_dir, fn)

    # determine our target filesize
    mode = max_file_size / 10
    size = int(triangular(0, max_file_size, mode) * 1024 * 1024)
    # print "Size (bytes):" + str(size)

    # determine if this is going to be an error, and then pick one of the two main kinds of error
    invalid_jats = False
    corrupt_zip = False
    if error:
        errtypes = ["invalid_jats", "corrupt_zip"]
        errprobs = [0.5, 0.5]
        type = _select_from(errtypes, errprobs)
        invalid_jats = type == "invalid_jats"
        corrupt_zip = type == "corrupt_zip"

    # make a suitable package at the file-path, and then return the path
    fixtures.PackageFactory.make_custom_zip(path, invalid_jats=invalid_jats, corrupt_zip=corrupt_zip, target_size=size)
    return path

def validate(base_url, keys, throttle, mdrate, mderrors, cterrors, max_file_size, tmpdir):
    tname = threading.current_thread().name
    app.logger.info("Thread:{x} - Initialise Validate; base_url:{a}, throttle:{b}, mdrate:{c}, mderrors:{d}, cterrors:{e}, max_file_size:{f}, tmpdir:{g}".format(x=tname, a=base_url, b=throttle, c=mdrate, d=mderrors, e=cterrors, f=max_file_size, g=tmpdir))

    mdopts = ["mdonly", "md+ct"]
    mdprobs = [mdrate, 1 - mdrate]

    mderroropts = ["error", "ok"]
    mderrorprobs = [mderrors, 1 - mderrors]

    cterroropts = ["error", "ok"]
    cterrorprobs = [cterrors, 1 - cterrors]

    while True:
        try:
            api_key = _select_from(keys)
            j = client.JPER(api_key, base_url)
            # print "API " + api_key

            # determine whether the metadata we're going to send will cause errors
            mdtype = _select_from(mderroropts, mderrorprobs)
            # print "MD: " + mdtype

            # generate a notification which may or may not have an error
            note = _make_notification(error=mdtype=="error")
            # print note

            # determine whether we're going to send some content
            hasct = _select_from(mdopts, mdprobs)
            # print "CT: " + hasct
            file_handle = None
            filepath = None
            cterr = "ok"
            if hasct == "md+ct":
                # determine if the content should have an error
                cterr = _select_from(cterroropts, cterrorprobs)
                #print "CTERR:" + cterr
                filepath = _get_file_path(tmpdir, max_file_size, error=cterr=="error")
                #print "File" + filepath
                file_handle = open(filepath)

            app.logger.info("Thread:{x} - Validate request for Account:{y} Type:{z} MD:{a} CT:{b}".format(x=tname, y=api_key, z=hasct, a=mdtype, b=cterr))

            # make the validate request (which will throw an exception more often than not, because that's what we're testing)
            try:
                j.validate(note, file_handle)
                app.logger.info("Thread:{x} - Validate request resulted in success".format(x=tname))
            except:
                app.logger.info("Thread:{x} - Validate request resulted in expected exception".format(x=tname))

            # cleanup after ourselves
            if filepath is not None:
                file_handle.close()
                os.remove(filepath)

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.info("Thread:{x} - Fatal exception '{y}'".format(x=tname, y=e.message))

def create(base_url, keys, throttle, mdrate, mderrors, cterrors, max_file_size, tmpdir, retrieve_rate, routable, repo_configs):
    tname = threading.current_thread().name
    app.logger.info("Thread:{x} - Initialise Create; base_url:{a}, throttle:{b}, mdrate:{c}, mderrors:{d}, cterrors:{e}, max_file_size:{f}, tmpdir:{g}, retrieve_rate:{h}, routable:{i}".format(x=tname, a=base_url, b=throttle, c=mdrate, d=mderrors, e=cterrors, f=max_file_size, g=tmpdir, h=retrieve_rate, i=routable))

    mdopts = ["mdonly", "md+ct"]
    mdprobs = [mdrate, 1 - mdrate]

    mderroropts = ["error", "ok"]
    mderrorprobs = [mderrors, 1 - mderrors]

    cterroropts = ["error", "ok"]
    cterrorprobs = [cterrors, 1 - cterrors]

    retrieveopts = ["get", "not"]
    retrieveprobs = [retrieve_rate, 1 - retrieve_rate]

    while True:
        try:
            api_key = _select_from(keys)
            j = client.JPER(api_key, base_url)
            #print "API " + api_key

            # determine whether the metadata we're going to send will cause errors
            mdtype = _select_from(mderroropts, mderrorprobs)
            #print "MD: " + mdtype

            # generate a notification which may or may not have an error
            note = _make_notification(error=mdtype=="error", routable=routable, repo_configs=repo_configs)
            #print note

            # determine whether we're going to send some content
            hasct = _select_from(mdopts, mdprobs)
            #print "CT: " + hasct
            file_handle = None
            filepath = None
            cterr = "ok"
            if hasct == "md+ct":
                # determine if the content should have an error
                cterr = _select_from(cterroropts, cterrorprobs)
                #print "CTERR:" + cterr
                filepath = _get_file_path(tmpdir, max_file_size, error=cterr=="error")
                #print "File" + filepath
                file_handle = open(filepath)

            app.logger.info("Thread:{x} - Create request for Account:{y} Type:{z} MD:{a} CT:{b}".format(x=tname, y=api_key, z=hasct, a=mdtype, b=cterr))

            # make the create request, which may occasionally throw errors
            id = None
            try:
                id, loc = j.create_notification(note, file_handle)
                app.logger.info("Thread:{x} - Create request for Account:{z} resulted in success, Notification:{y}".format(x=tname, y=id, z=api_key))
            except:
                app.logger.info("Thread:{x} - Create request for Account:{y} resulted in expected exception".format(x=tname, y=api_key))

            # cleanup after ourselves
            if filepath is not None:
                file_handle.close()
                os.remove(filepath)

            # now there's a chance that we might want to check our notification has been created correctly, so we might
            # retrieve it
            if id is not None:
                ret = _select_from(retrieveopts, retrieveprobs)
                if ret == "get":
                    # time.sleep(2)   # this gives JPER a chance to catch up
                    app.logger.info("Thread:{x} - Following Create for Account:{y}, requesting copy of Notification:{z}".format(x=tname, y=api_key, z=id))
                    try:
                        n = j.get_notification(id)
                        app.logger.info("Thread:{x} - Following Create for Account:{y}, successfully retrieved copy of Notification:{z}".format(x=tname, y=api_key, z=id))
                        for link in n.links:
                            if link.get("packaging") is not None:
                                url = link.get("url")
                                app.logger.info("Thread:{x} - Following Create for Account:{y}, from Notification:{z} requesting copy of Content:{a}".format(x=tname, y=api_key, z=id, a=url))
                                try:
                                    stream, headers = j.get_content(url)
                                except Exception as e:
                                    app.logger.info("Thread:{x} - MAJOR ISSUE; get content failed for Content:{z} that should have existed.  This needs a fix: '{b}'".format(x=tname, z=url, b=e.message))
                    except Exception as e:
                        app.logger.info("Thread:{x} - MAJOR ISSUE; get notification failed for Notification:{y} that should have existed.  This needs a fix: '{b}'".format(x=tname, y=id, b=e.message))

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.info("Thread:{x} - Fatal exception '{y}'".format(x=tname, y=e.message))

def listget(base_url, keys, throttle, generic_rate, max_lookback, tmpdir, repo_configs, error_rate, get_rate):
    tname = threading.current_thread().name
    app.logger.info("Thread:{x} - Initialise List/Get; base_url:{a}, throttle:{b}, generic_rate:{c}, max_lookback:{d}, tmpdir:{g}, error_rate:{h}, get_rate:{i}".format(x=tname, a=base_url, b=throttle, c=generic_rate, d=max_lookback, g=tmpdir, h=error_rate, i=get_rate))

    genopts = ["generic", "specific"]
    genprobs = [generic_rate, 1 - generic_rate]

    getopts = ["get", "leave"]
    getprobs = [get_rate, 1 - get_rate]

    erropts = ["err", "ok"]
    errprobs = [error_rate, 1 - error_rate]

    errtypes = ["page", "page_size", "missing_since", "malformed_since"]
    errtypeprobs = [0.25] * 4

    while True:
        try:
            api_key = _select_from(keys)
            j = client.JPER(api_key, base_url)
            #print "API " + api_key

            # determine whether the metadata we're going to send will cause errors
            reqtype = _select_from(genopts, genprobs)
            #print "Req: " + reqtype

            # use this to determine the repository id for the request
            repository_id = None
            if reqtype == "specific":
                config = _select_from(repo_configs)
                repository_id = config.get("repository")

            # determine the "since" date we're going to use for the request
            lookback = randint(0, max_lookback)
            since = dates.format(dates.before_now(lookback))
            # print "Since: " + since

            # choose a page size
            page_size = randint(1, 100)

            # now decide, after all that, if we're going to send a malformed request
            err = _select_from(erropts, errprobs)

            # if we are to make an erroneous request, go ahead and do it
            if err == "err":
                # choose a kind of malformed request
                malformed = _select_from(errtypes, errtypeprobs)
                params = {"page" : 1, "pageSize" : page_size, "since" : since}
                if malformed == "page":
                    params["page"] = "one"
                elif malformed == "page_size":
                    params["pageSize"] = "twelvty"
                elif malformed == "missing_since":
                    del params["since"]
                else:
                    params["since"] = "a week last thursday"

                # make the malformed url with the JPER client, so we know it gets there ok
                url = j._url("routed", id=repository_id, params=params)
                app.logger.info("Thread:{x} - List/Get sending malformed request for Account:{y} Type:{z} Error:{a} URL:{b}".format(x=tname, y=api_key, z=reqtype, a=malformed, b=url))

                # make the request, and check the response
                resp = http.get(url)
                if resp is not None and resp.status_code == 400:
                    app.logger.info("Thread:{x} - List/Get received correct 400 response to malformed request".format(x=tname))
                else:
                    if resp is None:
                        sc = None
                    else:
                        sc = resp.status_code
                    app.logger.info("Thread:{x} - MAJOR ISSUE; did not receive 400 response to malformed request, got {y}; URL:{z}".format(x=tname, y=sc, z=url))

                # continue, so that we don't have to indent the code below any further
                continue

            # if we get to here, we're going to go ahead and do a normal request
            app.logger.info("Thread:{x} - List/Get request for Account:{y} Type:{z} Since:{a}".format(x=tname, y=api_key, z=reqtype, a=since))

            # iterate over the notifications, catching any errors (which would be unexpected)
            try:
                count = 0
                for note in j.iterate_notifications(since, repository_id, page_size):
                    app.logger.info("Thread:{x} - List/Get request for Account:{y} listing notifications for Repository:{z} retrieved Notification:{a}".format(x=tname, y=api_key, z=repository_id, a=note.id))
                    count += 1

                    # determine if we're going to get the notification by itself (which is technically unnecessary, of course, but who knows what people's workflows will be)
                    reget = _select_from(getopts, getprobs)
                    if reget == "get":
                        try:
                            n = j.get_notification(note.id)
                            app.logger.info("Thread:{x} - Following List/Get for Account:{y} listing notifications for Repository:{z}, successfully retrieved copy of Notification:{a}".format(x=tname, y=api_key, z=repository_id, a=note.id))
                        except Exception as e:
                            app.logger.info("Thread:{x} - MAJOR ISSUE; get notification failed for Notification:{y} that should have existed.  This needs a fix: '{b}'".format(x=tname, y=note.id, b=e.message))

                    # now retrieve all the links in the note
                    for link in note.links:
                        url = link.get("url")
                        app.logger.info("Thread:{x} - Following List/Get for Account:{y} on Repository:{b}, from Notification:{z} requesting copy of Content:{a}".format(x=tname, y=api_key, z=note.id, a=url, b=repository_id))
                        try:
                            stream, headers = j.get_content(url)
                        except Exception as e:
                            app.logger.info("Thread:{x} - MAJOR ISSUE; get content failed for Content:{z} that should have existed.  This needs a fix: '{b}'".format(x=tname, z=url, b=e.message))

                app.logger.info("Thread:{x} - List/Get request completed successfully for Account:{y} listing notifications for Repository:{z} Count:{a}".format(x=tname, y=api_key, z=repository_id, a=count))

            except Exception as e:
                app.logger.info("Thread:{x} - MAJOR ISSUE; List/Get request for Account:{y} listing notifications for Repository:{z} resulted in exception '{e}'".format(x=tname, y=api_key, z=repository_id, e=e.message))

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.info("Thread:{x} - Fatal exception '{y}'".format(x=tname, y=e.message))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    # features governing the script as a whole
    parser.add_argument("--timeout", help="how long should this script run for", type=int, default=0)
    parser.add_argument("--pub_keys", help="path to file containing publisher api keys", default="pub_keys.txt")
    parser.add_argument("--repo_keys", help="path to file containing repository api keys", default="repo_keys.txt")
    parser.add_argument("--base_url", help="base url of the JPER API")
    parser.add_argument("--tmpdir", help="local directory where temp files can be stored", default="harness_tmp")
    parser.add_argument("--repo_configs", help="path to JSON list file containing the testing repo configs", default="repo_configs.json")

    # options to control the validation calls
    parser.add_argument("--validate_threads", help="number of threads to run for validation", default=1, type=int)
    parser.add_argument("--validate_throttle", help="number of seconds for each thread to pause between requests", default=1, type=int)
    parser.add_argument("--validate_mdrate", help="proportion of validate requests to be metadata-only (between 0 and 1) - the remainder will have content", default=0.1, type=float)
    parser.add_argument("--validate_mderrors", help="proportion of metadata-only validation requests which will contain errors (between 0 and 1)", default=0.8, type=float)
    parser.add_argument("--validate_cterrors", help="proportion of content validation requests which will contain errors (between 0 and 1)", default=0.8, type=float)
    parser.add_argument("--validate_maxfilesize", help="largest filesize to send in megabytes", default=100, type=int)

    # options to control the notification create calls
    parser.add_argument("--create_threads", help="number of threads to run for notification create", default=1, type=int)
    parser.add_argument("--create_throttle", help="number of seconds for each thread to pause between requests", default=1, type=int)
    parser.add_argument("--create_mdrate", help="proportion of create requests to be metadata-only (between 0 and 1) - the remainder will have content", default=0.1, type=float)
    parser.add_argument("--create_mderrors", help="proportion of metadata-only create requests which will contain errors (between 0 and 1)", default=0.05, type=float)
    parser.add_argument("--create_cterrors", help="proportion of content create requests which will contain errors (between 0 and 1)", default=0.05, type=float)
    parser.add_argument("--create_maxfilesize", help="largest filesize to send in megabytes", default=100, type=int)
    parser.add_argument("--create_retrieverate", help="chance (between 0 and 1) that after create the creator will attempt to get the created notification via the API", default=0.05, type=float)
    parser.add_argument("--create_routable", help="chance (between 0 and 1) that the notification will contain metadata that can be used to successfully route to a repository", default=0.5, type=float)

    # options to control the list records/get notifications calls
    parser.add_argument("--listget_threads", help="number of threads to run for list and get notifications", default=1, type=int)
    parser.add_argument("--listget_throttle", help="number of seconds for each thread to pause between requests", default=1, type=int)
    parser.add_argument("--listget_genericrate", help="proportion of requests for the generic list rather than the repo-specific list", default=0.05, type=float)
    parser.add_argument("--listget_maxlookback", help="maximum number of seconds in the past to issue as 'from' in requests", default=7776000, type=int)
    parser.add_argument("--listget_errorrate", help="proportion of requests which are malformed, and therefore result in errors", default=0.1, type=float)
    parser.add_argument("--listget_getrate", help="proportion of requests which subsequently re-get the individual notification after listing", default=0.05, type=float)

    args = parser.parse_args()

    if args.config:
        add_configuration(app, args.config)

    pycharm_debug = app.config.get('DEBUG_PYCHARM', False)
    if args.debug:
        pycharm_debug = True

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_SERVER_HOST', 'localhost'), port=app.config.get('DEBUG_SERVER_PORT', 51234), stdoutToServer=True, stderrToServer=True)
        print "STARTED IN REMOTE DEBUG MODE"

    # attempt to load the publisher and repo keys
    pubkeys = _load_keys(args.pub_keys)
    repokeys = _load_keys(args.repo_keys)

    # load the repository configs
    configs = _load_repo_configs(args.repo_configs)

    # check the tmp directory, and create it if necessary
    if not os.path.exists(args.tmpdir):
        os.mkdir(args.tmpdir)

    # this is where we'll keep a reference to all our threads
    thread_pool = []

    # create thread instances for validation
    for i in range(args.validate_threads):
        t = threading.Thread(name="validate_" + uuid.uuid4().hex, target=validate, kwargs={
            "base_url" : args.base_url,
            "keys" : pubkeys,
            "throttle" : args.validate_throttle,
            "mdrate" : args.validate_mdrate,
            "mderrors" :  args.validate_mderrors,
            "cterrors" :  args.validate_cterrors,
            "max_file_size" : args.validate_maxfilesize,
            "tmpdir" : args.tmpdir
        })
        t.daemon = True
        thread_pool.append(t)

    # create thread instances for notification create
    for i in range(args.create_threads):
        t = threading.Thread(name="create_" + uuid.uuid4().hex, target=create, kwargs={
            "base_url" : args.base_url,
            "keys" : pubkeys,
            "throttle" : args.create_throttle,
            "mdrate" : args.create_mdrate,
            "mderrors" :  args.create_mderrors,
            "cterrors" :  args.create_cterrors,
            "max_file_size" : args.create_maxfilesize,
            "tmpdir" : args.tmpdir,
            "retrieve_rate" : args.create_retrieverate,
            "routable" : args.create_routable,
            "repo_configs" : configs
        })
        t.daemon = True
        thread_pool.append(t)

    # create thread instances for list/get requests
    for i in range(args.listget_threads):
        t = threading.Thread(name="listget_" + uuid.uuid4().hex, target=listget, kwargs={
            "base_url" : args.base_url,
            "keys" : repokeys,
            "throttle" : args.listget_throttle,
            "generic_rate" : args.listget_genericrate,
            "max_lookback" :  args.listget_maxlookback,
            "tmpdir" : args.tmpdir,
            "repo_configs" : configs,
            "error_rate" : args.listget_errorrate,
            "get_rate" : args.listget_getrate
        })
        t.daemon = True
        thread_pool.append(t)

    # now kick off all the threads
    for t in thread_pool:
        app.logger.info("Starting Thread:{x}".format(x=t.name))
        t.start()

    # now we just wait until either we timeout or we are explicitly terminated (e.g. by KeyboardInterrupt)
    start = datetime.now()
    try:
        while True:
            if args.timeout > 0:
                if datetime.now() > start + timedelta(seconds=args.timeout):
                    break
    finally:
        # This is because the thread shut-down and the main function shutdown can sometimes both
        # be working on the tmp directory, and this sometimes causes exceptions.  This then just keeps
        # trying to do the delete until it succeeds
        while True:
            try:
                shutil.rmtree(args.tmpdir)
                break
            except:
                pass
        exit()