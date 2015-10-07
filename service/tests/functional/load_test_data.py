from octopus.core import app, add_configuration, initialise
import json
from service import models

def _load_keys(path):
    with open(path) as f:
        return f.read().split("\n")

def _load_repo_configs(path):
    with open(path) as f:
        return json.loads(f.read())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    parser.add_argument("-r", "--repo_configs", help="path to file which contains configs to load", default="repo_configs.json")
    parser.add_argument("-k", "--repo_keys", help="file where you can find a list of repo keys.  Should be the same number as there are repo configs", default="repo_keys.txt")
    parser.add_argument("-p", "--pub_keys", help="file where you can find a list of publisher keys.")

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

    # init the app
    initialise()

    # load the repository configs
    configs = _load_repo_configs(args.repo_configs)
    keys = _load_keys(args.repo_keys)

    # load the publisher keys
    pubs = None
    if args.pub_keys:
        pubs = _load_keys(args.pub_keys)

    for i in range(len(configs)):
        config = configs[i]
        key = keys[i]

        # make the repository config
        rc = models.RepositoryConfig(config)
        rc.save()

        # make the user account
        acc = models.Account()
        acc.id = rc.id
        acc.add_packaging("http://purl.org/net/sword/package/SimpleZip")
        acc.set_api_key(key)
        acc.add_role("repository")
        acc.save()

    # load the publisher accounts
    for key in pubs:
        acc = models.Account()
        acc.set_api_key(key)
        acc.add_role("publisher")
        acc.save()




