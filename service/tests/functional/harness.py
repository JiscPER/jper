"""
Script which can be used to drive all aspects of the JPER API in order to test its behaviour at scale

For full documentation on using this script, see HARNESS.md

Quickstart: just execute this script with no arguments, and the defaults will be used:

::

    python harness.py
    
"""
from octopus.core import app, add_configuration
from octopus.modules.jper import client
from octopus.lib import dates, http, isolang
from service.tests import fixtures
import threading, time, os, uuid, shutil, json, string
from datetime import datetime, timedelta
from random import randint, random, triangular


def _load_keys(path):
    """
    Load API keys from the file at the specified path

    :param path:
    :return: a list of api keys
    """
    with open(path) as f:
        return [x for x in f.read().split("\n") if x is not None and x != ""]

def _load_repo_configs(path):
    """
    Load repository configurations from the json file at the specified path

    :param path:
    :return: list of json objects
    """
    with open(path) as f:
        return json.loads(f.read())

def _select_from(arr, probs=None):
    """
    Select an element randomly from the array.

    If the probs argument is provided, it must be an array of the same length as the source array
    and specify a probability between 0 and 1 that the element will be selected.  The sum of the
    probs array MUST equal 1.

    :param arr: list of elements to select from
    :param probs: probability of each element being selected
    :return: a random element from the array
    """
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
    """
    Select N unique elements from the array

    :param arr: the array to select from
    :param n: the number of elements to select
    :return: a list of elements
    """
    selection = []

    idx = list(range(0, len(arr)))
    for x in range(n):
        if len(idx) == 0:
            break
        i = randint(0, len(idx) - 1)
        selection.append(arr[idx[i]])
        del idx[i]

    return selection

def _random_string(shortest, longest):
    """
    Create a random string between the lengths of shortest and longest

    Strings are constructed out of the ascii letters and some spaces

    :param shortest: shortes the string should be
    :param longest: longest the string should be
    :return: a string
    """
    length = randint(shortest, longest)
    s = ""
    pool = string.ascii_letters + "    "    # inject a few extra spaces, to increase their prevalence
    for i in range(length):
        l = randint(0, len(pool) - 1)
        s += pool[l]
    return s

def _random_url():
    """
    Return a random url.  Actually, this always returns the same url:

    https://datahub.deepgreen.org/static/jperlogo.png
    ## https://pubrouter.jisc.ac.uk/static/jperlogo.png

    which isn't that random, but it is resolvable, and doesn't rely on an external service to be up.

    If you are messing with this module, you need to keep your eye on this bit.

    :return: url
    """
    # return "http://example.com/file/" + uuid.uuid4().hex
    ## return "https://pubrouter.jisc.ac.uk/static/jperlogo.png"
    return "https://datahub.deepgreen.org/static/jperlogo.png"

def _random_datetime(since):
    """
    Create a random datetime in the time period between now and since

    :param since: earliest date
    :return: a datetime object
    """
    epoch = datetime.fromtimestamp(0)
    lower_delta = since - epoch
    lower = int(lower_delta.total_seconds())

    now = datetime.now()
    upper_delta = now - epoch
    upper = int(upper_delta.total_seconds())

    seconds = randint(lower, upper)
    return datetime.fromtimestamp(seconds)

def _random_issn():
    """
    Generate a random ISSN.

    This provides something which looks like an issn, though the checksum digit is not calculated, so they
    may not be truly valid

    :return: something that looks like an issn
    """
    first = randint(1000, 9999)
    second = randint(100, 999)
    return str(first) + "-" + str(second) + str(_select_from([1, 2, 3, 4, 5, 6, 7, 8, 9, "X"]))

def _random_doi():
    """
    Generate a random DOI.

    Obviously this DOI won't resolve to anything in the real world

    :return: something that looks like a DOI
    """
    return "10." + _random_string(3, 4) + "/" + _random_string(5, 10)

def _random_email():
    """
    Generate a random email address

    :return: something that looks like an email
    """
    return _random_string(10, 15) + "@" + _random_string(10, 15) + "." + _select_from(["ac.uk", "edu", "com"])

def _make_notification(error=False, routable=0, repo_configs=None):
    """
    Create a notification that is suitable for sending into the system for testing.

    If error is True, then this will just return a dictionary which contains some data which does not constitute
    a valid notification.

    Otherwise, the notification will be generated using random data generators provided in this module.

    If routable is set, this should be a probability between 0 and 1 that the notification will contain data
    from the supplied repo_configs, which will in turn make the notification routable by the test system.  Therefore,
    to guarantee that the notification is routable, pass in routable=1, for a 50/50 chance pass in routable=0.5

    The repo_configs should be a list of repository configurations as python dicts which represent the actual
    repository configs in your test system.  If routable > 0 and this method decides to make the notification
    routable it will select N configurations (between 1 and all), and include some data (again at random) from
    that configuration into the test notification.  This will ensure that the notification contains some information
    from each configuration which will make it routable to the equivalent repositories.

    :param error: should the notification be erroneous
    :param routable: chance between 0 and 1 that this notification will be routable
    :param repo_configs: repository configs to use to generate routable notifications
    :return: a notification object as a dict
    """
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
        # the config may not be fully populated, so only allow us to choose from a field which has data in it
        routable_fields = []
        for f, l in cfg.items():
            if l is not None and len(l) > 0:
                routable_fields.append(f)

        # field = _select_from(["domains", "name_variants", "author_ids", "postcodes", "grants", "strings"])
        field = _select_from(routable_fields)
        idx = randint(0, len(cfg[field]) - 1)
        if field not in uber:
            uber[field] = []
        uber[field].append(cfg[field][idx])

    # now layer the uber match record over the randomised notification
    for k, v in uber.items():
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
    """
    Get a path to a file which meets the criteria

    This will construct a file of the suitable size and give you back the path to it

    :param parent_dir: the directory in which files are stored
    :param max_file_size: the maximum size of the file
    :param error: whether the file should be erroneous
    :return:
    """
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
    """
    Thread runner which carries out requests against the validate API

    This will make repeated requests to that API until it is shut-down, based on the parameters supplied

    :param base_url: the base url for the router API
    :param keys: the list of API keys to use for requests
    :param throttle: time to wait in between each request
    :param mdrate: chance between 0 and 1 that this is a metadata-only request
    :param mderrors: chance between 0 and 1 that the metadata contains errors
    :param cterrors: chance between 0 and 1 that the content contains errors
    :param max_file_size: largest file size to deposit
    :param tmpdir: directory to use for temp file storage
    :return:
    """
    tname = threading.current_thread().name
    app.logger.debug("Thread:{x} - Initialise Validate; base_url:{a}, throttle:{b}, mdrate:{c}, mderrors:{d}, cterrors:{e}, max_file_size:{f}, tmpdir:{g}".format(x=tname, a=base_url, b=throttle, c=mdrate, d=mderrors, e=cterrors, f=max_file_size, g=tmpdir))

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

            app.logger.debug("Thread:{x} - Validate request for Account:{y} Type:{z} MD:{a} CT:{b}".format(x=tname, y=api_key, z=hasct, a=mdtype, b=cterr))

            # make the validate request (which will throw an exception more often than not, because that's what we're testing)
            try:
                j.validate(note, file_handle)
                app.logger.debug("Thread:{x} - Validate request resulted in success".format(x=tname))
            except:
                app.logger.error("Thread:{x} - Validate request resulted in expected exception".format(x=tname))

            # cleanup after ourselves
            if filepath is not None:
                file_handle.close()
                os.remove(filepath)

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.error("Thread:{x} - MAJOR ISSUE - Fatal exception '{y}'".format(x=tname, y=str(e)))

def create(base_url, keys, throttle, mdrate, mderrors, cterrors, max_file_size, tmpdir, retrieve_rate, routable, repo_configs):
    """
    Thread runner which makes requests to the create API

    This will make repeated requests to that API until it is shut-down, based on the parameters supplied

    :param base_url: the base url of the router API
    :param keys: API keys to use in requests
    :param throttle: time to wait in between each request
    :param mdrate: chance between 0 and 1 of a metadata-only request
    :param mderrors: chance between 0 and 1 for an erroneous metadata record
    :param cterrors: chance between 0 and 1 for an error in the content
    :param max_file_size: largest file size to use
    :param tmpdir: temp directory for file storage
    :param retrieve_rate: chance between 0 and 1 of retrieving the created object immediately after
    :param routable: chance between 0 and 1 that the created object is routable
    :param repo_configs: repository configs to use for creating routable notifications
    :return:
    """
    tname = threading.current_thread().name
    app.logger.debug("Thread:{x} - Initialise Create; base_url:{a}, throttle:{b}, mdrate:{c}, mderrors:{d}, cterrors:{e}, max_file_size:{f}, tmpdir:{g}, retrieve_rate:{h}, routable:{i}".format(x=tname, a=base_url, b=throttle, c=mdrate, d=mderrors, e=cterrors, f=max_file_size, g=tmpdir, h=retrieve_rate, i=routable))

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

            app.logger.debug("Thread:{x} - Create request for Account:{y} Type:{z} MD:{a} CT:{b}".format(x=tname, y=api_key, z=hasct, a=mdtype, b=cterr))

            # make the create request, which may occasionally throw errors
            id = None
            try:
                id, loc = j.create_notification(note, file_handle)
                app.logger.debug("Thread:{x} - Create request for Account:{z} resulted in success, Notification:{y}".format(x=tname, y=id, z=api_key))
            except:
                app.logger.error("Thread:{x} - Create request for Account:{y} resulted in expected exception".format(x=tname, y=api_key))

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
                    app.logger.debug("Thread:{x} - Following Create for Account:{y}, requesting copy of Notification:{z}".format(x=tname, y=api_key, z=id))
                    try:
                        n = j.get_notification(id)
                        app.logger.debug("Thread:{x} - Following Create for Account:{y}, successfully retrieved copy of Notification:{z}".format(x=tname, y=api_key, z=id))
                        for link in n.links:
                            if link.get("packaging") is not None:
                                url = link.get("url")
                                app.logger.debug("Thread:{x} - Following Create for Account:{y}, from Notification:{z} requesting copy of Content:{a}".format(x=tname, y=api_key, z=id, a=url))
                                try:
                                    stream, headers = j.get_content(url)
                                except Exception as e:
                                    app.logger.error("Thread:{x} - MAJOR ISSUE; get content failed for Content:{z} that should have existed.  This needs a fix: '{b}'".format(x=tname, z=url, b=str(e)))
                    except Exception as e:
                        app.logger.error("Thread:{x} - MAJOR ISSUE; get notification failed for Notification:{y} that should have existed.  This needs a fix: '{b}'".format(x=tname, y=id, b=str(e)))

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.error("Thread:{x} - Fatal exception '{y}'".format(x=tname, y=str(e)))

def listget(base_url, keys, throttle, generic_rate, max_lookback, tmpdir, repo_configs, error_rate, get_rate):
    """
    Thread runner that issues list and get requests against the API

    This will make repeated requests to that API until it is shut-down, based on the parameters supplied

    :param base_url: base url of the routed api
    :param keys: api keys to use for requests
    :param throttle: time to wait in between requests
    :param generic_rate: chance between 0 and 1 that this is a request to the generic routing api, rather than the repository-specific one
    :param max_lookback: maximum time to use for "since" dates in requests
    :param tmpdir: temp directory for file storage
    :param repo_configs: repository configs to do retrievals for
    :param error_rate: chance between 0 and 1 to issue a malformed request
    :param get_rate: chance between 0 and 1 that after a list request each record is individually retrieved
    :return:
    """
    tname = threading.current_thread().name
    app.logger.debug("Thread:{x} - Initialise List/Get; base_url:{a}, throttle:{b}, generic_rate:{c}, max_lookback:{d}, tmpdir:{g}, error_rate:{h}, get_rate:{i}".format(x=tname, a=base_url, b=throttle, c=generic_rate, d=max_lookback, g=tmpdir, h=error_rate, i=get_rate))

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
                app.logger.debug("Thread:{x} - List/Get sending malformed request for Account:{y} Type:{z} Error:{a} URL:{b}".format(x=tname, y=api_key, z=reqtype, a=malformed, b=url))

                # make the request, and check the response
                resp = http.get(url)
                if resp is not None and resp.status_code == 400:
                    app.logger.debug("Thread:{x} - List/Get received correct 400 response to malformed request".format(x=tname))
                else:
                    if resp is None:
                        sc = None
                    else:
                        sc = resp.status_code
                    app.logger.error("Thread:{x} - MAJOR ISSUE; did not receive 400 response to malformed request, got {y}; URL:{z}".format(x=tname, y=sc, z=url))

                # continue, so that we don't have to indent the code below any further
                continue

            # if we get to here, we're going to go ahead and do a normal request
            app.logger.debug("Thread:{x} - List/Get request for Account:{y} Type:{z} Since:{a}".format(x=tname, y=api_key, z=reqtype, a=since))

            # iterate over the notifications, catching any errors (which would be unexpected)
            try:
                count = 0
                for note in j.iterate_notifications(since, repository_id, page_size):
                    app.logger.debug("Thread:{x} - List/Get request for Account:{y} listing notifications for Repository:{z} retrieved Notification:{a}".format(x=tname, y=api_key, z=repository_id, a=note.id))
                    count += 1

                    # determine if we're going to get the notification by itself (which is technically unnecessary, of course, but who knows what people's workflows will be)
                    reget = _select_from(getopts, getprobs)
                    if reget == "get":
                        try:
                            n = j.get_notification(note.id)
                            app.logger.debug("Thread:{x} - Following List/Get for Account:{y} listing notifications for Repository:{z}, successfully retrieved copy of Notification:{a}".format(x=tname, y=api_key, z=repository_id, a=note.id))
                        except Exception as e:
                            app.logger.error("Thread:{x} - MAJOR ISSUE; get notification failed for Notification:{y} that should have existed.  This needs a fix: '{b}'".format(x=tname, y=note.id, b=str(e)))

                    # now retrieve all the links in the note
                    for link in note.links:
                        url = link.get("url")
                        app.logger.debug("Thread:{x} - Following List/Get for Account:{y} on Repository:{b}, from Notification:{z} requesting copy of Content:{a}".format(x=tname, y=api_key, z=note.id, a=url, b=repository_id))
                        try:
                            stream, headers = j.get_content(url)
                        except client.JPERAuthException as e:
                            # we got a 401 back from the service, that is acceptable, since we may not be authorised to access it
                            app.logger.debug(("Thread:{x} - get content unauthorised (401) for Content:{z} - this can happen, so is not necessarily unexpected".format(x=tname, z=url)))
                        except Exception as e:
                            app.logger.error("Thread:{x} - MAJOR ISSUE; get content failed for Content:{z} that should have existed.  This needs a fix: '{b}'".format(x=tname, z=url, b=str(e)))

                app.logger.debug("Thread:{x} - List/Get request completed successfully for Account:{y} listing notifications for Repository:{z} Count:{a}".format(x=tname, y=api_key, z=repository_id, a=count))

            except Exception as e:
                app.logger.error("Thread:{x} - MAJOR ISSUE; List/Get request for Account:{y} listing notifications for Repository:{z} resulted in exception '{e}'".format(x=tname, y=api_key, z=repository_id, e=str(e)))

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            app.logger.error("Thread:{x} - Fatal exception '{y}'".format(x=tname, y=str(e)))

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
        print("STARTED IN REMOTE DEBUG MODE")

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
        app.logger.debug("Starting Thread:{x}".format(x=t.name))
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
