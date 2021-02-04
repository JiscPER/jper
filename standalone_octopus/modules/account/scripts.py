from standalone_octopus.modules.account.factory import AccountFactory
from standalone_octopus.lib import cli
import argparse, getpass

class UserMod(cli.Script):

    def _input_password(self):
        password = None
        while password is None:
            password = self._request_password()
        return password

    def _request_password(self):
        password = getpass.getpass()
        confirm = getpass.getpass("Confirm Password:")
        if password != confirm:
            print("passwords do not match - try again!")
            return None
        return password

    def run(self, argv):

        parser = argparse.ArgumentParser()

        parser.add_argument("-e", "--email", help="email address of user")
        parser.add_argument("-p", "--password", help="password for the new or existing user.  If omitted, you will be prompted for one on the next line")
        parser.add_argument("-r", "--role", help="comma separated list of roles to be held by this account")

        args = parser.parse_args(argv)

        if not args.email:
            print("Please specify an email with the -e option")
            parser.print_help()
            exit()

        if not args.role:
            print("WARNING: no role specified, so this user won't be able to do anything")

        email = args.email
        password = None
        roles = [r.strip() for r in args.role.split(",")] if args.role is not None else []

        if args.password:
            password = args.password
        else:
            password = self._input_password()

        Account = AccountFactory.get_model()
        acc = Account.pull_by_email(email)
        if not acc:
            acc = Account()
            acc.email = email
        acc.role = roles
        acc.set_password(password)
        acc.save()
