from octopus.core import app, add_configuration
import threading, time, os, uuid, shutil
from datetime import datetime, timedelta
from random import randint, random, triangular
from octopus.modules.jper import client
from service.tests import fixtures

def _load_keys(path):
    with open(path) as f:
        return f.read().split("\n")

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

def _make_notification(error=False):
    if not error:
        base = fixtures.APIFactory.incoming()
        # FIXME: we may want to interfere with the base later when we have more to go on
        return base
    else:
        return {"something" : "broken"}


def _get_file_path(parent_dir, max_file_size, error=False):
    # sort out a file path
    fn = uuid.uuid4().hex + ".zip"
    path = os.path.join(parent_dir, fn)

    # determine our target filesize
    mode = (max_file_size - 1) / 10
    if mode < 1:
        mode = 1
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
    print "Thread:{x} - Initialise Validate; base_url:{a}, throttle:{b}, mdrate:{c}, mderrors:{d}, cterrors:{e}, max_file_size:{f}, tmpdir:{g}".format(x=tname, a=base_url, b=throttle, c=mdrate, d=mderrors, e=cterrors, f=max_file_size, g=tmpdir)

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

            print "Thread:{x} - Validate request for Account:{y} Type:{z} MD:{a} CT:{b}".format(x=tname, y=api_key, z=hasct, a=mdtype, b=cterr)

            # make the validate request (which will throw an exception more often than not, because that's what we're testing)
            try:
                j.validate(note, file_handle)
                print "Thread:{x} - Validate request resulted in success".format(x=tname)
            except:
                print "Thread:{x} - Validate request resulted in exception".format(x=tname)

            # cleanup after ourselves
            if filepath is not None:
                file_handle.close()
                os.remove(filepath)

            # sleep before making the next request
            time.sleep(throttle)
        except Exception as e:
            print e.message

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

    # options to control the validation calls
    parser.add_argument("--validate_threads", help="number of threads to run for validation", default=1, type=int)
    parser.add_argument("--validate_throttle", help="number of seconds for each thread to pause between requests", default=1.0, type=int)
    parser.add_argument("--validate_mdrate", help="proportion of validate requests to be metadata-only (between 0 and 1) - the remainder will have content", default=0.1, type=float)
    parser.add_argument("--validate_mderrors", help="proportion of metadata-only validation requests which will contain errors (between 0 and 1)", default=0.8, type=float)
    parser.add_argument("--validate_cterrors", help="proportion of content validation requests which will contain errors (between 0 and 1)", default=0.8, type=float)
    parser.add_argument("--validate_maxfilesize", help="largest filesize to send in megabytes", default=100, type=int)

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

    # now kick off all the threads
    for t in thread_pool:
        print "Starting Thread:{x}".format(x=t.name)
        t.start()

    # now we just wait until either we timeout or we are explicitly terminated (e.g. by KeyboardInterrupt)
    start = datetime.now()
    try:
        while True:
            if args.timeout > 0:
                if datetime.now() > start + timedelta(seconds=args.timeout):
                    break
    finally:
        shutil.rmtree(args.tmpdir)
        exit()