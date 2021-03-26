from octopus.core import app, add_configuration, initialise
import json
from service import models

def _load_repo_configs(path):
    """
    load repository configs from the specified json file

    :param path:
    :return: list of json objects
    """
    with open(path) as f:
        return json.loads(f.read())

def _load_keys(path):
    """
    Load API keys from the specified file

    :param path:
    :return: list of api keys
    """
    with open(path) as f:
        return f.read().split("\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")

    parser.add_argument("-r", "--repo_configs", help="path to file which contains configs to load", default="repo_configs.json")
    parser.add_argument("-k", "--repo_keys", help="file where you can find a list of repo keys.  Should be the same number as there are repo configs")

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

    # init the app
    initialise()

    if args.repo_configs:
        configs = _load_repo_configs(args.repo_configs)

        for i in range(len(configs)):
            config = configs[i]

            rc = models.RepositoryConfig.pull(config["id"])
            if rc is not None:
                rc.delete()

            acc = models.Account.pull(config["repository"])
            if acc is not None:
                acc.delete()

    if args.repo_keys:
        keys = _load_keys(args.repo_keys)

        for i in range(len(keys)):
            models.Account.delete_by_query({"query" : {"term" : {"api_key.exact" : keys[i]}}})