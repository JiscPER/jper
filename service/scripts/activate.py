from octopus.core import app, add_configuration
from service import control

import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    # some general script running features
    parser.add_argument("-d", "--debug", action="store_true", help="pycharm debug support enable")
    parser.add_argument("-c", "--config", help="additional configuration to load (e.g. for testing)")
    parser.add_argument("-i", "--input", help="provide a .txt (or .csv with one column) file of ids")
    parser.add_argument("-r", "--repo", help="id of the repository account to affect")
    parser.add_argument("-a", "--activate", help="activate this account (e.g. if it has been suspended)", action="store_true")
    parser.add_argument("-s", "--stop", help="stop/deactivate this account", action="store_true")

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

    if not args.repo and not args.input:
        parser.print_help()
        exit(0)

    if args.activate and args.stop:
        print("Please specify only one of -a/--activate and -s/--stop")
        parser.print_help()
        exit(0)

    if args.input and args.repo:
        print("Please specify only one of -i/--input and -r/--repo")
        parser.print_help()
        exit(0)

    if args.input:
        try:
            if args.input == '-':
                if args.stop:
                    for line in sys.stdin:
                        repo = line.rstrip()
                        print("stop {repo}".format(repo=repo))
                        control.deactivate_account(repo)
                elif args.activate:
                    for line in sys.stdin:
                        repo = line.rstrip()
                        print("activate {repo}".format(repo=repo))
                        control.activate_account(repo)
            else:
                with open(args.input,'r') as f:
                    if args.stop:
                        for line in f:
                            repo = line.rstrip()
                            print("stop {repo}".format(repo=repo))
                            control.deactivate_account(repo)
                    elif args.activate:
                        for line in f:
                            repo = line.rstrip()
                            print("activate {repo}".format(repo=repo))
                            control.activate_account(repo)
        except Exception as e:
            print("ERROR: exception '{s}'".format(s=e.message))
            pass
    else:
        if args.stop:
            control.deactivate_account(args.repo)
        elif args.activate:
            control.activate_account(args.repo)
