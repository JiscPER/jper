import socket
import time
import sys
import subprocess
from standalone_octopus.modules import dictdiffer
from unittest import TestCase
from standalone_octopus.lib import plugin
import os


class FunctionalTestServer(TestCase):
    """
    FIXME: don't use this, it doesn't work.  Leaving it here for later diagnosis.
    """
    def setUp(self):
        super(FunctionalTestServer, self).setUp()
        if self.config and self.cfg_file and self.flask_app:
            mod = plugin.load_module(self.flask_app)
            make_config(self.config, self.cfg_file)
            self.test_server = TestServer(port=None, index=None, python_app_module_path=os.path.abspath(mod.__file__), cfg_file=self.cfg_file)
            self.test_server.spawn_with_config()

    def tearDown(self):
        super(FunctionalTestServer, self).tearDown()
        self.test_server.terminate()
        os.remove(self.cfg_file)


def make_config(cfg, filepath):
    with open(filepath, "wb") as out:
        for k, v in cfg.items():
            if isinstance(v, str):
                # if the value is a string, wrap it in quotes
                out.write(f"{k} = '{v}'\n".encode('utf-8'))
            else:
                # otherwise it's probably an int, float or bool so just stringify it
                out.write(f"{k} = '{str(v)}'\n".encode('utf-8'))

            # NOTE: this would not handle dicts and lists, so you might get errors, in which
            # case you'll need to work out what to do next


def get_first_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))  # let OS pick the first available port
    free_port = sock.getsockname()[1]  # which port did the OS pick?
    sock.close()
    return free_port


class TestServer(object):
    def __init__(self, port, index, python_app_module_path='service/web.py', cfg_file=None):
        self.port = port
        self.index = index
        self.python_app_module_path = python_app_module_path
        self.cfg_file = cfg_file
        self._process = None

    def get_server_url(self):
        """
        Return the url of the test server
        """
        return 'http://localhost:{0}'.format(self.port)

    def spawn(self):
        # sys.executable is the full, absolute path to the current Python interpreter
        # This is used so that the new process with the test app in it runs properly in a virtualenv.
        self._process = subprocess.Popen([sys.executable, self.python_app_module_path, '--port', str(self.port), '--index', self.index, '--no-logging'])

        # we must wait for the server to start listening
        time.sleep(1)

    def spawn_with_config(self):
        self._process = subprocess.Popen([sys.executable, self.python_app_module_path, "--config", self.cfg_file])

        # we must wait for the server to start listening
        time.sleep(3)

    def terminate(self):
        if self._process:
            self._process.terminate()
        time.sleep(1)


def diff_dicts(d1, d2, d1_label='d1', d2_label='d2', print_unchanged=False):
    """
    Diff two dictionaries - prints changed, added and removed keys and the changed values. DOES NOT DO NESTED DICTS!

    :param d1: First dict - we compare this with d2
    :param d2: Second dict - we compare against this one
    :param d1_label: Will be used instead of "d1" in debugging output to make it more helpful.
    :param d2_label: Will be used instead of "d2" in debugging output to make it more helpful.
    :param print_unchanged: - should we print set of unchanged keys (can be long and useless). Default: False.
    :return: nothing, prints results to STDOUT
    """
    differ = dictdiffer.DictDiffer(d1, d2)
    print('Added :: keys present in {d1} which are not in {d2}'.format(d1=d1_label, d2=d2_label))
    print(differ.added())
    print()
    print('Removed :: keys present in {d2} which are not in {d1}'.format(d1=d1_label, d2=d2_label))
    print(differ.removed())
    print()
    print('Changed :: keys which are the same in {d1} and {d2} but whose values are different'.format(d1=d1_label, d2=d2_label))
    print(differ.changed())
    print()

    if differ.changed():
        print('Changed values :: the values of keys which have changed. Format is as follows:')
        print('  Key name:')
        print('    value in {d1}'.format(d1=d1_label))
        print('    value in {d2}'.format(d2=d2_label))
        print()
        for key in differ.changed():
            print(' ', key + ':')
            print('   ', d1[key])
            print('   ', d2[key])
            print()
        print()

    if print_unchanged:
        print('Unchanged :: keys which are the same in {d1} and {d2} and whose values are also the same'.format(d1=d1_label, d2=d2_label))
        print(differ.unchanged())
